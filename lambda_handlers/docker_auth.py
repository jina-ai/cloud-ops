import base64
import json
import logging
import os


def get_logger(context='generic', file=True):
    logger = logging.getLogger(context)
    logger.setLevel(logging.INFO)
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


def lambda_handler(event, context):
    logger = get_logger(context='docker_auth')

    docker_username = os.environ['docker_username']
    docker_password = os.environ['docker_password']

    encoded_docker_username = base64.b64encode(docker_username.encode('utf-8'))
    encoded_docker_password = base64.b64encode(docker_password.encode('utf-8'))

    return _return_json_builder(body=json.dumps({"docker_username": str(encoded_docker_username), "docker_password": str(encoded_docker_password)}), status=200)
