from enum import Enum


class SSMCreationStatus(Enum):
    """
    Status list to be used by `waiter` before timing out during SSM Creation
    """
    SUCCESS = ['Active']
    WAIT = ['Creating', 'Updating', 'Pending']
    FAILURE = ['Failed']
    

class SSMCreationTime(Enum):
    TIMEOUT = 120
    SLEEP = 5
    

class SSMAssociationStatus(Enum):
    """
    Status list to be used by `waiter` before timing out during SSM Association
    """
    SUCCESS = ['Active']
    WAIT = ['Creating', 'Updating', 'Pending']
    FAILURE = ['Failed']
    
    
class SSMAssociationTime(Enum):
    TIMEOUT = 120
    SLEEP = 5
    
    
class SSMDeletionStatus(Enum):
    """
    Status list to be used by `waiter` before timing out during SSM Deletion
    """
    SUCCESS = ['Deleted']
    WAIT = ['Deleting', 'Pending']
    FAILURE = ['Failed']


class SSMDeletionTime(Enum):
    TIMEOUT = 120
    SLEEP = 5


class PluginStatus(Enum):
    """
    Status list to be used by `waiter` before timing out during SSM Plugin Execution
    """
    SUCCESS = ['Success']
    WAIT = ['Pending', 'InProgress', 'Delayed']
    FAILURE = ['Cancelled', 'TimedOut', 'Failed', 'Cancelling']


class PluginTime(Enum):
    TIMEOUT = 14400
    SLEEP = 10
