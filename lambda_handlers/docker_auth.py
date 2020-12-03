import json
import logging
import os


def get_logger(context='generic', file=True):
    logger = logging.getLogger(context)
    logger.setLevel(logging.DEBUG)
    return logger


def _return_json_builder(body, status):
    return {
        "isBase64Encoded": True,
        "headers": {
            "Content-Type": "application/json"
        },
        "statusCode": int(status),
        "body": body
    }

# Returns Base64 encoded docker credentials from AWS environment
def lambda_handler(event, context):
    logger = get_logger(context='docker_auth')

    docker_username = os.environ['docker_username']
    docker_password = os.environ['docker_password']

    return _return_json_builder(body=json.dumps({"docker_username": docker_username, "docker_password": docker_password}), status=200)
