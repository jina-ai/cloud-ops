import sys
import boto3
import botocore

from ..logger import get_logger
from ..client import AWSClientWrapper
from ..helper import TimeContext, waiter
from ..excepts import SSMDocumentCreationFailed, SSMDocumentDeletionFailed
from ..enums import SSMCreationStatus, SSMAssociationStatus, SSMDeletionStatus, \
    SSMCreationTime, SSMAssociationTime, SSMDeletionTime
    

class SSMDocument:
    """Wrapper around boto3 to create/delete/execute long-running service manager documents
    """
    def __init__(self, name, template, plugin='runStressTest'):
        self.logger = get_logger(self.__class__.__name__)
        self._client_wrapper = AWSClientWrapper(service='ssm')
        self._client = self._client_wrapper.client
        self._name = name
        self._template = template
        self._plugin = plugin
    
    def __enter__(self):
        self.logger.info(f'Entering SSMDocument context. Creating the document with name `{self._name}`')
        self.create()
        return self

    def create(self):
        try:
            response = self._client.create_document(Content=self._template, 
                                                    Name=self._name,
                                                    DocumentType='Command',
                                                    DocumentFormat='YAML')
            self._status = response['DocumentDescription']['Status']
            self.logger.info(f'Calling waiter for `Document creation`!')
            self._is_created = waiter(func=self._describe_document,
                                      logger=self.logger,
                                      success_status=SSMCreationStatus.SUCCESS.value,
                                      wait_status=SSMCreationStatus.WAIT.value,
                                      failure_status=SSMCreationStatus.FAILURE.value,
                                      time_to_wait=SSMCreationTime.TIMEOUT.value,
                                      time_to_sleep=SSMCreationTime.SLEEP.value)
        except botocore.exceptions.ClientError as exp:
            raise SSMDocumentCreationFailed(f'Document creation failed with folliwng exception. Exiting! \n{exp}')
        except (self._client.exceptions.InvalidDocument, 
                self._client.exceptions.InvalidDocumentSchemaVersion) as exp:
            raise SSMDocumentCreationFailed(f'Document schema is not correct! Please check AWS Docs. Exiting! \n{exp}')
        except Exception as exp:
            raise SSMDocumentCreationFailed(f'Document creation failed with following exception. Exiting! \n{exp}')
    
    def _describe_document(self):
        try:
            response = self._client.describe_document(Name=self._name)
            self._status = response['Document']['Status']
        except (self._client.exceptions.InvalidDocument,
                self._client.exceptions.InvalidDocumentSchemaVersion) as exp:
            self._status = 'Deleted'
        except Exception as exp:
            self._status = 'Deleted'
            self.logger.error(f'Got the following exception {exp}')
        return self._status
        
    @property
    def name(self):
        return self._name
        
    @property
    def status(self):
        return self._status
    
    @property
    def is_created(self):
        if hasattr(self, '_is_created'):
            return self._is_created
    
    @property
    def association_status(self):
        if hasattr(self, '_association_status'):
            return self._association_status
    
    @property
    def association_id(self):
        if hasattr(self, '_association_id'):
            return self._association_id

    @property
    def is_associated(self):
        if hasattr(self, '_is_associated'):
            return self._is_associated
    
    def associate(self, instance_id):
        try:
            self.logger.info(f'Associating document with instance `{instance_id}`')
            response = self._client.create_association(
                Name=self._name,
                Targets=[{'Key': 'InstanceIds',
                          'Values': [instance_id]}]
            )
            self._association_id = response['AssociationDescription']['AssociationId']
            self._association_status = response['AssociationDescription']['Overview']['Status']
            self.logger.info(f'Calling waiter for `Document association`!')
            self._is_associated = waiter(func=self._describe_association,
                                         logger=self.logger,
                                         success_status=SSMAssociationStatus.SUCCESS.value,
                                         wait_status=SSMAssociationStatus.WAIT.value,
                                         failure_status=SSMAssociationStatus.FAILURE.value,
                                         time_to_wait=SSMAssociationTime.TIMEOUT.value,
                                         time_to_sleep=SSMAssociationTime.SLEEP.value,
                                         instance_id=instance_id)
        except botocore.exceptions.ParamValidationError:
            self.logger.error('Invalid parameters. Please check AWS Documents')
        except Exception as exp:
            self.logger.exception(f'Got the following error while associating doc with ec2 instance {exp}')

    def _describe_association(self, instance_id):
        try:
            response = self._client.describe_association(AssociationId=self._association_id)
            self._association_status = response['AssociationDescription']['Overview']['Status']
            return self._association_status
        except self._client.exceptions.InvalidDocument:
            self.logger.exception(f'Document we are invoking is invalid!')
        except Exception as exp:
            self.logger.exception(f'Got the following error while triggering describe_association {exp}')
            
    def _delete_association(self, instance_id):
        try:
            self.logger.info(f'Deleting document association')
            self._client.delete_association(AssociationId=self._association_id)       
        except self._client.exceptions.InvalidDocument:
            self.logger.error(f'Got delete association reqest for an invalid doc')
        except Exception as exp:
            self.logger.error(f'Got the following error while triggering describe_association {exp}')
                
    def run(self, instance_id, s3_bucket_name, s3_key_prefix='blah'):
        try:
            self.logger.info(f'Triggering send_command!')
            response = self._client.send_command(
                DocumentName=self._name,
                Targets=[{'Key': 'InstanceIds',
                          'Values': [instance_id]}],
                TimeoutSeconds=14400,
                OutputS3BucketName=s3_bucket_name,
                OutputS3KeyPrefix=s3_key_prefix
            )
            self._command_id = response['Command']['CommandId']
            self.logger.info(f'Got command id `{self._command_id}`')
            
            self._command_status = {}
            self.wait(waiter_name='command_executed', 
                      instance_id=instance_id)
            self._command_response = self._client.get_command_invocation(
                CommandId=self._command_id,
                InstanceId=instance_id,
                PluginName=self._plugin
            )
        except self._client.exceptions.InvalidInstanceId as exp:
            self.logger.exception(f'Got InvalidInstanceId error\n{exp}')
        except Exception as exp:
            self.logger.exception(f'Got the following error while triggering send_command {exp}')
    
    def _list_command_invocations(self, instance_id):
        try:
            self.logger.info(f'Getting overall command invocations to fetch all plugins!')
            response = self._client.list_command_invocations(
                CommandId=self._command_id,
                InstanceId=instance_id,
                Details=True
            )
            self._command_invocation = response['CommandInvocations'][0]
            self._command_plugins = self._command_invocation['CommandPlugins']
        except Exception as exp:
            self.logger.exception(f'Got the following error while triggering send_command {exp}')

    @property
    def command_status(self):
        if hasattr(self, '_command_response'):
            return self._command_response['Status']
    
    @property
    def command_s3_stdout(self):
        if hasattr(self, '_command_response'):
            return self._command_response['StandardOutputUrl']
    
    @property
    def command_s3_stderr(self):
        if hasattr(self, '_command_response'):
            return self._command_response['StandardErrorUrl']
        
    @property
    def command_start_time(self):
        if hasattr(self, '_command_response'):
            return self._command_response['ExecutionStartDateTime']
        
    @property
    def command_end_time(self):
        if hasattr(self, '_command_response'):
            return self._command_response['ExecutionEndDateTime']
    
    def wait(self, waiter_name, instance_id):
        self._client_wrapper.waiter = waiter_name
        with TimeContext(f'Waiting for `{waiter_name}`'):
            try:
                self._client_wrapper.waiter.wait(CommandId=self._command_id,
                                                 InstanceId=instance_id,
                                                 PluginName=self._plugin)
            except botocore.exceptions.WaiterError as exp:
                self.logger.error(f'Operation failed after waiting! \n{exp}')
    
    @property
    def is_deleted(self):
        if hasattr(self, '_is_deleted'):
            return self._is_deleted
    
    def delete(self):
        try:
            self._client.delete_document(Name=self._name)
            self.logger.info(f'Calling waiter for `Document deletion`!')
            self._is_deleted = waiter(func=self._describe_document,
                                      logger=self.logger,
                                      success_status=SSMDeletionStatus.SUCCESS.value,
                                      wait_status=SSMDeletionStatus.WAIT.value,
                                      failure_status=SSMDeletionStatus.FAILURE.value,
                                      time_to_wait=SSMDeletionTime.TIMEOUT.value,
                                      time_to_sleep=SSMDeletionTime.SLEEP.value)
        except botocore.exceptions.ClientError as exp:
            self.logger.error(f'Got the following error while triggering `delete_stack` {exp}')
        except self._client.exceptions.InvalidDocument:
            self.logger.error(f'Got an invalid document to delete. Please recheck')
        except Exception as exp:
            self.logger.exception(f'Got the following error while triggering `delete_stack` {exp}')
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.logger.info(f'Exiting SSMDocument context. Deleting the document with name `{self._name}`')
            self.delete()
        except Exception as exp:
            self.logger.error('Please make sure document gets deleted by checking the AWS console..')
            raise SSMDocumentDeletionFailed(f'Document deletion failed with exception {exp}')
