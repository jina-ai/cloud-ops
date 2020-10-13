'''
    Fetch docker token from registry for hub pull and push operation for docker hub
    Ref: https://github.com/docker/distribution/blob/master/docs/spec/auth/token.md
    Token can be alternately obtained by curl:
    curl "https://auth.docker.io/token?service=registry.docker.io&scope=repository:jina-ai/jina:pull,push"
'''
import re
import logging
import json
import urllib3
import docker


def get_logger(context='generic', file=True):
    logger = logging.getLogger(context)
    logger.setLevel(logging.DEBUG)
    return logger

def _return_json_builder(body, status):
    return {
        "isBase64Encoded": False,
        "headers": {
            "Content-Type": "application/json"
        },
        "statusCode": int(status),
        "body": body
    }

def _docker_login():
    """A wrapper of docker login """
    logger = get_logger(context='fetch_docker_token')
    client = docker.from_env()
    from docker.errors import APIError
    username = 'jinacommunity'
    password = 'ba2bf491-1420-4629-b315-dccc6c1aa13d'
    registry = 'https://registry.docker.io/v2/jina-ai/jina'
    if username and password:
        try:
            client.login(username=username, password=password,
                                registry=registry)
            logger.info(f'successfully logged in to docker hub')
            return _return_json_builder(body='docker login successful', status=200)

        except APIError:
            return _return_json_builder(body='invalid credentials passed. docker login failed',
                                    status=401)
    else:
        return _return_json_builder(body='no username/password specified, docker login failed',
                                    status=401)

def fetch_docker_token():
    logger = get_logger(context='fetch_docker_token')
    http = urllib3.PoolManager()
  
    headers = {
        'service': DockerRegistry.SERVICE,
        'scope': DockerRegistry.SCOPE
    }
    response = http.request(method=DockerRegistry.METHOD, 
                            url=DockerRegistry.URL, 
                            headers=headers)
    logger.info(f'Got the following response status from DockerRegistry: {response.status}')
    logger.info(response.data)

    if response.status == 200:
        response_dict = json.loads(response.data.decode('utf-8')) 
        return response_dict['token']
    else:
        return None

def validate_docker_token(token):
    logger = get_logger(context='validate_docker_token')
    http = urllib3.PoolManager()
    if not token:
        logging.warning(f'No tokens passed to validate_docker_token')
        return False
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = http.request(method=DockerRegistry.METHOD, 
                            url=DockerRegistry.REGISTRY_URL, 
                            headers=headers)
    logger.info(f'Got the following response status from DockerRegistry: {response.status}')
    if response.status == 200:
        logger.info('Docker token is valid.')
        return _return_json_builder(body='Docker token is valid',
                                    status=200)
    else:
        logger.info('Docker token is invalid.')
        return _return_json_builder(body='Docker token is invalid',
                                    status=401)

class DockerRegistry:
    URL = 'https://auth.docker.io/token'
    REGISTRY_URL = 'https://registry.docker.io/v2/jina-ai/jina'
    METHOD = 'GET'
    SERVICE = 'registry.docker.io'
    SCOPE = 'repository:jina-ai/jina:pull,push'
    VALIDATE_TOKEN = False


class HttpVerb:
    GET = 'GET'
    POST = 'POST'
    ALL = '*'


def lambda_handler(event, context):
    logger = get_logger(context='docker_authorizer')
    ''' Trigger AWS event for docker auth '''
    # if 'authorizationToken' in event:
    #     docker_token = event['authorizationToken']
    #     logger.info(f'Got an authorization token in the request!')
    # else:
    #     docker_token = ''
    #     logger.info(f'No authorization token in the request!')
    
    # if 'methodArn' in event:
    #     method_arn = event['methodArn']
    #     logger.info(f'Current Method ARN: {method_arn}')

    login_response = _docker_login()
    if login_response['statusCode'] == 200:
        token = fetch_docker_token()
        logger.info('Fetched token: ' + str(token))
        if DockerRegistry.VALIDATE_TOKEN:
            logger.info('Validating docker token')
            validate_docker_token(token)
