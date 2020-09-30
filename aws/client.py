import os
import boto3

from .logger import get_logger


class AWSClientWrapper:
    """Wrapper around boto3 to create aws clients 
    Using Access key & Secret key we create a boto3 client to be used with other services
    """
    def __init__(self, service, 
                 access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'), 
                 secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'), 
                 region='us-east-2'):
        self.logger = get_logger(self.__class__.__name__)
        self._service = service
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._region = region
        self._client = boto3.client(service_name=self._service,
                                    aws_access_key_id=self._access_key_id,
                                    aws_secret_access_key=self._secret_access_key,
                                    region_name=self._region)
    
    @property
    def client(self):
        return self._client
    
    @property
    def all_waiters(self):
        return self._client.waiter_names
    
    @property
    def waiter(self):
        return self._waiter
    
    @waiter.setter
    def waiter(self, waiter_name):
        try:
            if waiter_name not in self.all_waiters:
                self.logger.error(f'Invalid waiter `{waiter_name} for service `{self._service}`')
            self._waiter = self.client.get_waiter(waiter_name=waiter_name)
        except Exception as exp:
            self.logger.exception(f'Got the following exception while getting the waiter {exp}')
