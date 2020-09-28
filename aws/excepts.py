
class StackCreationFailed(Exception):
    """ Exception to denote failure during `cloudformation.create()` """
    
class StackDeletionFailed(Exception):
    """ Exception to denote failure during `cloudformation.delete()` """
    
class SSMDocumentCreationFailed(Exception):
    """ Exception to denote failure during `ssm.create()` """

class SSMDocumentDeletionFailed(Exception):
    """ Exception to denote failure during `ssm.delete()` """

class SSMDocumentAssociationFailed(Exception):
    """ Exception to denote failure during `ssm.associate()` """

class LambdaCreateFailed(Exception):
    """ Exception to denote failure during `lambda.create()` """

class LambdaUpdateFailed(Exception):
    """ Exception to denote failure during `lambda.update()` """
