import boto3
import botocore

from ..logger import get_logger
from ..client import AWSClientWrapper
from ..excepts import LambdaCreateFailed, LambdaUpdateFailed
from ..helper import TimeContext, file_exists, waiter


class Lambda:
    """Wrapper around boto3 to create/update Lambda functions
    """
    def __init__(self, name: str, zip_location: str, handler: str = 'lambda_function', 
                 role='arn:aws:iam::416454113568:role/lambda-role', description: str = ''):
        self.logger = get_logger(context=self.__class__.__name__)
        self._client_wrapper = AWSClientWrapper(service='lambda')
        self._client = self._client_wrapper.client
        self._name = name
        self._handler = handler
        self._role = role
        self._zip_location = zip_location
        self._description = description
    
    def __enter__(self):
        self.logger.info(f'Entering Lambda context. Creating/updating the stack with name `{self._name}`')
        self.logger.info(f'Checking if the function already exists!')
        self.get()
        if self.state in ['Invalid', 'Failed']:
            self.logger.info(f'Function doesn\'t exist. Creating..')
            self.create()
        else:
            self.logger.info(f'Function already exists. Updating the code..')
            self.update()
        return self
        
    def create(self):
        try:
            self.logger.info(f'Creating Lambda function!')
            if not file_exists(filepath=self._zip_location):
                raise LambdaCreateFailed(f'Invalid zip location provided. Lambda creation failed!')
            with open(self._zip_location, 'rb') as f:
                code_bytes = f.read()
            response = self._client.create_function(FunctionName=self._name,
                                                    Runtime='python3.8',
                                                    Code={'ZipFile': code_bytes},
                                                    Role=self._role,
                                                    Handler=self._handler,
                                                    Description=self._description,
                                                    Publish=True)
            self.logger.info(f'Calling `function_active` waiter!')
            self._active = self.wait(waiter_name='function_active')
        except self._client.exceptions.ResourceConflictException:
            self._active = False
            raise LambdaCreateFailed(f'Lambda creation failed with Resource Conflict error. Exiting!')
        except Exception as exp:
            self._active = False
            raise LambdaCreateFailed(f'Lambda creation failed with exception. Exiting! \n{exp}')
    
    def get(self):
        try:
            self.logger.info(f'Getting Lambda function!')
            response = self._client.get_function(FunctionName=self._name)
            self._state = response['Configuration']['State']
            self._function_arn = response['Configuration']['FunctionArn']
            self._runtime = response['Configuration']['Runtime']
        except self._client.exceptions.ResourceNotFoundException:
            self._state = 'Invalid'
            self.logger.error(f'get_function cannot find the resource')
        except Exception as exp:
            self._state = 'Invalid'
            self.logger.error(f'Got the following exception while executing get_function \n{exp}')
    
    def wait(self, waiter_name):
        self._client_wrapper.waiter = waiter_name
        with TimeContext(f'Waiting for `{waiter_name}`'):
            try:
                self._client_wrapper.waiter.wait(FunctionName=self._name)
                return True
            except botocore.exceptions.WaiterError:
                self.logger.error(f'Operation failed after waiting!')
                return False
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def arn(self):
        if hasattr(self, '_function_arn'):
            return self._function_arn
    
    @property
    def active(self):
        if hasattr(self, '_active'):
            return self._active

    @property
    def state(self):
        if hasattr(self, '_state'):
            return self._state
        
    @property
    def runtime(self):
        if hasattr(self, '_runtime'):
            return self._runtime
        
    @property
    def updated(self):
        if hasattr(self, '_updated'):
            return self._updated
    
    def update(self):
        try:
            self.logger.info(f'Updating Lambda function code!')
            if not file_exists(filepath=self._zip_location):
                raise LambdaUpdateFailed(f'Invalid zip location provided. Lambda update failed!')
            with open(self._zip_location, 'rb') as f:
                code_bytes = f.read()
            response = self._client.update_function_code(FunctionName=self._name,
                                                         ZipFile=code_bytes,
                                                         Publish=True)
            self.logger.info(f'Calling `function_updated` waiter!')
            self._updated = self.wait(waiter_name='function_updated')
        except Exception as exp:
            self.logger.error(f'Got the following exception while executing update_function_code \n{exp}') 

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.info(f'Status of function at exit.. {self.state}')
