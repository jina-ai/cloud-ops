import boto3
import botocore

from ..logger import get_logger
from ..client import AWSClientWrapper
from ..excepts import StackCreationFailed, StackDeletionFailed
from ..helper import TimeContext, waiter


class CFNStack:
    """Wrapper around boto3 to create/delete/run Cloudformation stacks
    """
    def __init__(self, name, template):
        self.logger = get_logger(context=self.__class__.__name__)
        self._client_wrapper = AWSClientWrapper(service='cloudformation')
        self._client = self._client_wrapper.client
        self._name = name
        self._template = template
        
    def __enter__(self):
        self.logger.info(f'Entering CFNStack context. Creating the stack with name `{self._name}`')
        self.create()
        return self
        
    def create(self):
        try:
            response = self._client.create_stack(StackName=self._name,
                                                 TemplateBody=self._template,
                                                 Capabilities=['CAPABILITY_NAMED_IAM'])
            self._stack_id = response['StackId']
            self.logger.info(f'Got stack id `{self._stack_id}`. Calling `stack_create_complete` waiter!')
            self._created = self.wait(waiter_name='stack_create_complete')
        except botocore.exceptions.ClientError as exp:
            raise StackCreationFailed(f'Stack creation failed with exception. Exiting! \n{exp}')
        except Exception as exp:
            raise StackCreationFailed(f'Stack creation failed with exception. Exiting! \n{exp}')
    
    @property
    def name(self):
        return self._name
    
    @property
    def id(self):
        if hasattr(self, '_stack_id'):
            return self._stack_id
    
    @property
    def created(self):
        if hasattr(self, '_created'):
            return self._created
    
    @property
    def status(self):
        self._describe_stack()
        if hasattr(self, '_status'):
            return self._status
        
    @property
    def resources(self):
        self._stack_resources()
        return self._resources
        
    def _describe_stack(self):
        try:
            stack_details = self._client.describe_stacks(StackName=self._name)
            self._status = stack_details['Stacks'][0]['StackStatus']
        except botocore.exceptions.ClientError as exp:
            self.logger.exception(f'Got following error while triggering describe_stacks {exp}')
        except Exception as exp:
            self.logger.exception(f'Got following error while triggering describe_stacks {exp}')
    
    def _stack_resources(self):
        try:
            stack_resources = self._client.describe_stack_resources(StackName=self._name)
            self._resources = {resource['LogicalResourceId']: resource['PhysicalResourceId'] 
                               for resource in stack_resources['StackResources']}
        except Exception as exp:
            self.logger.exception(f'Got following error while triggering describe_stack_resources {exp}')
               
    def wait(self, waiter_name):
        self._client_wrapper.waiter = waiter_name
        with TimeContext(f'Waiting for `{waiter_name}`'):
            try:
                self._client_wrapper.waiter.wait(StackName=self._name)
                return True
            except botocore.exceptions.WaiterError:
                self.logger.error(f'Operation failed after waiting!')
                return False
    
    def delete(self):
        try:
            self._client.delete_stack(StackName=self._name)
            self.logger.info(f'Stack deletion triggered. Calling `stack_delete_complete` waiter!')
            self.wait(waiter_name='stack_delete_complete')
        except botocore.exceptions.ClientError as exp:
            raise StackDeletionFailed(f'Stack deletion failed with exception {exp}')
        except Exception as exp:
            raise StackDeletionFailed(f'Stack deletion failed with exception {exp}')
            
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.logger.info(f'Exiting CFNStack context. Deleting the stack with name `{self._name}`, if it exists!')
            if not self.status:
                self.logger.info(f'Nothing to do, as stack doesn\'t exist.')
                return
            self.delete()
        except Exception as exp:
            self.logger.error('Please make sure stack gets deleted by checking the AWS console..')
            raise StackDeletionFailed(f'Stack deletion failed with exception {exp}')
