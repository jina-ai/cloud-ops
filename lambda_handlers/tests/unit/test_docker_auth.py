import os

import json
import logging
import pytest

from ...docker_auth import lambda_handler
from jina.helper import yaml

def get_logger(context='generic', file=True):
    logger = logging.getLogger(context)
    logger.setLevel(logging.DEBUG)
    return logger


def test_docker_auth(monkeypatch):

    monkeypatch.setenv('docker_username', 'test_username')
    monkeypatch.setenv('docker_password', 'test_password')
   
    returned_body = lambda_handler(None, None)
    docker_creds =  json.loads(returned_body['body'])
    assert returned_body['statusCode'] == 200
    assert docker_creds['docker_username'] ==  'test_username'
    assert docker_creds['docker_password'] == 'test_password'