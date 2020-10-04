import re
import logging
import urllib3


def get_logger(context='generic', file=True):
    logger = logging.getLogger(context)
    logger.setLevel(logging.DEBUG)
    return logger


def validate_github_token(token):
    logger = get_logger(context='validate_github_token')
    http = urllib3.PoolManager()
    if not token:
        return False
    headers = {
        'Authorization': f'token {token}', 
        'User-Agent': GitHub.APP
    }
    # TODO: Check & implement if email id needs to be stored
    response = http.request(method=GitHub.METHOD, 
                            url=GitHub.URL, 
                            headers=headers)
    logger.info(f'Got the following response status from Github: {response.status}')
    if response.status == 200:
        return True
    else:
        return False


class GitHub:
    URL = 'https://api.github.com'
    METHOD = 'GET'
    APP = 'jina-hub-api'


class HttpVerb:
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    HEAD = 'HEAD'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'
    ALL = '*'


class AuthPolicy:
    # The AWS account id the policy will be generated for. This is used to create the method ARNs.
    aws_account_id = ''
    # The principal used for the policy, this should be a unique identifier for the end user.
    principal_id = ''
    # The policy version used for the evaluation. This should always be '2012-10-17'
    version = '2012-10-17'
    # The regular expression used to validate resource paths for the policy
    path_regex = '^[/.a-zA-Z0-9-\*]+$'

    '''Internal lists of allowed and denied methods.

    These are lists of objects and each object has 2 properties: A resource
    ARN and a nullable conditions statement. The build method processes these
    lists and generates the approriate statements for the final policy.
    '''
    allow_methods = []
    deny_methods = []

    # The API Gateway API id. By default this is set to '*'
    rest_api_id = '*'
    # The region where the API is deployed. By default this is set to '*'
    region = '*'
    # The name of the stage used in the policy. By default this is set to '*'
    stage = '*'

    def __init__(self, principal, aws_account_id):
        self.aws_account_id = aws_account_id
        self.principal_id = principal
        self.allow_methods = []
        self.deny_methods = []

    def _add_method(self, effect, verb, resource, conditions):
        '''Adds a method to the internal lists of allowed or denied methods. Each object in
        the internal list contains a resource ARN and a condition statement. The condition
        statement can be null.'''
        if verb != '*' and not hasattr(HttpVerb, verb):
            raise NameError('Invalid HTTP verb ' + verb + '. Allowed verbs in HttpVerb class')
        resource_pattern = re.compile(self.path_regex)
        if not resource_pattern.match(resource):
            raise NameError('Invalid resource path: ' + resource + '. Path should match ' + self.path_regex)

        if resource[:1] == '/':
            resource = resource[1:]

        resourceArn = f'arn:aws:execute-api:{self.region}:{self.aws_account_id}:{self.rest_api_id}/*/{verb}/{resource}'

        if effect.lower() == 'allow':
            self.allow_methods.append({
                'resourceArn': resourceArn,
                'conditions': conditions
            })
        elif effect.lower() == 'deny':
            self.deny_methods.append({
                'resourceArn': resourceArn,
                'conditions': conditions
            })

    def _get_empty_statement(self, effect):
        '''Returns an empty statement object prepopulated with the correct action and the
        desired effect.'''
        statement = {
            'Action': 'execute-api:Invoke',
            'Effect': effect[:1].upper() + effect[1:].lower(),
            'Resource': []
        }

        return statement

    def _get_statement_for_effect(self, effect, methods):
        '''This function loops over an array of objects containing a resourceArn and
        conditions statement and generates the array of statements for the policy.'''
        statements = []

        if len(methods) > 0:
            statement = self._get_empty_statement(effect)

            for curMethod in methods:
                if curMethod['conditions'] is None or len(curMethod['conditions']) == 0:
                    statement['Resource'].append(curMethod['resourceArn'])
                else:
                    conditionalStatement = self._get_empty_statement(effect)
                    conditionalStatement['Resource'].append(curMethod['resourceArn'])
                    conditionalStatement['Condition'] = curMethod['conditions']
                    statements.append(conditionalStatement)

            if statement['Resource']:
                statements.append(statement)

        return statements

    def allow_all_methods(self):
        '''Adds a '*' allow to the policy to authorize access to all methods of an API'''
        self._add_method('Allow', HttpVerb.ALL, '*', [])

    def deny_all_methods(self):
        '''Adds a '*' allow to the policy to deny access to all methods of an API'''
        self._add_method('Deny', HttpVerb.ALL, '*', [])

    def allow_method(self, verb, resource):
        '''Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods for the policy'''
        self._add_method('Allow', verb, resource, [])

    def deny_method(self, verb, resource):
        '''Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods for the policy'''
        self._add_method('Deny', verb, resource, [])

    def allow_method_with_conditions(self, verb, resource, conditions):
        '''Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods and includes a condition for the policy statement. More on AWS policy
        conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition'''
        self._add_method('Allow', verb, resource, conditions)

    def deny_method_with_conditions(self, verb, resource, conditions):
        '''Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods and includes a condition for the policy statement. More on AWS policy
        conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition'''
        self._add_method('Deny', verb, resource, conditions)

    def build(self):
        '''Generates the policy document based on the internal lists of allowed and denied
        conditions. This will generate a policy with two main statements for the effect:
        one statement for Allow and one statement for Deny.
        Methods that includes conditions will have their own statement in the policy.'''
        if ((self.allow_methods is None or len(self.allow_methods) == 0) and 
                (self.deny_methods is None or len(self.deny_methods) == 0)):
            raise NameError('No statements defined for the policy')

        policy = {
            'principalId': self.principal_id,
            'policyDocument': {
                'Version': self.version,
                'Statement': []
            }
        }

        policy['policyDocument']['Statement'].extend(self._get_statement_for_effect('Allow', self.allow_methods))
        policy['policyDocument']['Statement'].extend(self._get_statement_for_effect('Deny', self.deny_methods))

        return policy


def lambda_handler(event, context):
    logger = get_logger(context='hub_authorizer')
    
    if 'authorizationToken' in event:
        github_token = event['authorizationToken']
        logger.info(f'Got an authorization token in the request!')
    else:
        github_token = ''
        logger.info(f'No authorization token in the request!')
    
    if 'methodArn' in event:
        method_arn = event['methodArn']
        logger.info(f'Current Method ARN: {method_arn}')
    
    principal_id = 'user|a1b2c3d4'
    tmp = event['methodArn'].split(':')
    apiGatewayArnTmp = tmp[5].split('/')
    aws_account_id = tmp[4]

    policy = AuthPolicy(principal_id, aws_account_id)
    policy.rest_api_id = apiGatewayArnTmp[0]
    policy.region = tmp[3]
    policy.stage = apiGatewayArnTmp[1]
    
    if validate_github_token(token=github_token):
        policy.allow_all_methods()
    else:
        policy.allow_method(HttpVerb.GET, '/list/')
        policy.deny_method(HttpVerb.POST, '/push/')

    auth_response = policy.build()
    context = {
        'user_email': 'value',  # TODO: $context.authorizer.user_email -> value
    }
    auth_response['context'] = context
    return auth_response
