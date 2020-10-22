import botocore

from ..client import AWSClientWrapper
from ..excepts import StackCreationFailed, StackUpdateFailed, StackDeletionFailed
from ..helper import TimeContext
from ..logger import get_logger


class CFNStack:
    """Wrapper around boto3 to create/delete/update Cloudformation stacks
    """

    def __init__(self, name, template, parameters=None, delete_at_exit=False):
        self.logger = get_logger(context=self.__class__.__name__)
        self._client_wrapper = AWSClientWrapper(service='cloudformation')
        self._client = self._client_wrapper.client
        self._name = name
        self._template = template
        self._parameters = parameters
        self._delete_at_exit = delete_at_exit
        self._exists = False

    def __enter__(self):
        self.logger.info('Entering CFNStack context')
        self.logger.info(f'Checking if stack with name `{self._name}` exists!')
        self._describe_stack()
        if not self._exists:
            self.logger.info(f'Stack doesn\'t exist. Creating it!')
            self.create()
        else:
            self.logger.info(f'Stack already exists. Updating it!')
            self.update()
        return self

    def create(self):
        try:
            # Find a better way of doing this.
            if self._parameters:
                response = self._client.create_stack(StackName=self._name,
                                                     TemplateBody=self._template,
                                                     Parameters=self._parameters,
                                                     Capabilities=['CAPABILITY_NAMED_IAM'])
            else:
                response = self._client.create_stack(StackName=self._name,
                                                     TemplateBody=self._template,
                                                     Capabilities=['CAPABILITY_NAMED_IAM'])
            self._stack_id = response['StackId']
            self.logger.info(f'Got stack id `{self._stack_id}`. Calling `stack_create_complete` waiter!')
            self._exists = self.wait(waiter_name='stack_create_complete')
        except botocore.exceptions.ClientError as exp:
            raise StackCreationFailed(f'Stack creation failed with exception. Exiting! \n{exp}')
        except Exception as exp:
            raise StackCreationFailed(f'Stack creation failed with exception. Exiting! \n{exp}')

    def update(self):
        try:
            if self._parameters:
                response = self._client.update_stack(StackName=self._name,
                                                     TemplateBody=self._template,
                                                     Parameters=self._parameters,
                                                     Capabilities=['CAPABILITY_NAMED_IAM'])
            else:
                response = self._client.update_stack(StackName=self._name,
                                                     TemplateBody=self._template,
                                                     Capabilities=['CAPABILITY_NAMED_IAM'])
            self._stack_id = response['StackId']
            self.logger.info(f'Got stack id `{self._stack_id}`. Calling `stack_update_complete` waiter!')
            self._exists = self.wait(waiter_name='stack_update_complete')
        except botocore.exceptions.ClientError as exp:
            self.logger.warning(f'Stack update failed with ValidationError as template hasn\'t changed!')
        except Exception as exp:
            raise StackUpdateFailed(f'Stack update failed with exception {exp}')

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        if hasattr(self, '_stack_id'):
            return self._stack_id

    @property
    def exists(self):
        if hasattr(self, '_exists'):
            return self._exists

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
            self.logger.info(f'Describing stack with name `{self._name}`')
            stack_details = self._client.describe_stacks(StackName=self._name)
            self._status = stack_details['Stacks'][0]['StackStatus']
            self._exists = True
            self.logger.info(f'Stack exists with status `{self._status}`')
        except botocore.exceptions.ClientError as exp:
            self.logger.warning(exp)
        except self._client.exceptions.AmazonCloudFormationException:
            self.logger.warning(f'Stack with name {self._name} doesn\'t exist! Please create one!')
        except Exception as exp:
            self.logger.error(f'Got following error while triggering describe_stacks {exp}')

    def _stack_resources(self):
        try:
            self.logger.info(f'Describing all resources under stack with name `{self._name}`')
            stack_resources = self._client.describe_stack_resources(StackName=self._name)
            self._resources = stack_resources['StackResources']
        except Exception as exp:
            self.logger.error(f'Got following error while triggering describe_stack_resources {exp}')

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
            self.logger.info(f'Exiting CFNStack context.')

            if not self.status:
                self.logger.info(f'Nothing to do, as stack doesn\'t exist.')
                return
            if self._delete_at_exit:
                self.logger.info(f'`delete_at_exit` is set to True.')
                self.logger.info(f'Deleting the stack with name `{self._name}`')
                self.delete()
        except Exception as exp:
            self.logger.error('Please make sure stack gets deleted by checking the AWS console..')
            raise StackDeletionFailed(f'Stack deletion failed with exception {exp}')
