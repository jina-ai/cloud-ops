import json
from logging import getLogger

import mock

from jina.docker.hubapi import _list

sample_manifest = {
    'manifest': [
        {
            "name": "Dummy MWU Encoder",
            "description": "a minimum working unit of a containerized encoder, used for tutorial only",
            "type": "pod",
            "author": "Jina AI Dev-Team (dev-team@jina.ai)",
            "url": "https://jina.ai",
            "documentation": "https://github.com/jina-ai/jina-hub",
            "version": "0.0.52",
            "vendor": "Jina AI Limited",
            "license": "apache-2.0",
            "avatar": None,
            "platform": [
                "linux/amd64"
            ],
            "keywords": [
                "toy",
                "example"
            ],
            "manifest_version": 1,
            "update": "nightly",
            "kind": "encoder"
        }
    ]
}


@mock.patch('jina.docker.hubapi.urlopen')
def test_hubapi_list(mocker):
    mocker.return_value.__enter__.return_value.read.return_value = json.dumps(sample_manifest)
    result = _list(logger=getLogger(),
                   image_name='Dummy MWU Encoder',
                   image_kind='encoder',
                   image_type='pod',
                   image_keywords=['toy'])

    mocker.assert_called_once()
    assert result[0]['name'] == 'Dummy MWU Encoder'
    assert result[0]['version'] == '0.0.52'
    assert result[0]['kind'] == 'encoder'







































import os

import json
import logging
import pymongo
import pytest
from pytest_mock import mocker
import mongomock
import mock
from mock import Mock

from jina.docker.hubio import HubIO

from ...hubapi_list import MongoDBHandler
from ...hubapi_list import lambda_handler
from jina.helper import yaml


def get_logger(context='generic', file=True):
    logger = logging.getLogger(context)
    logger.setLevel(logging.DEBUG)
    return logger

@pytest.fixture
def mock_mongo_client():
	return Mock(spec=MongoDBHandler)

@pytest.fixture
def mock_pymongo_client():
	return Mock(spec=pymongo.MongoClient)

@pytest.fixture
def mock_pymongo_mongohandler():
    return pymongo.MongoClient('fake-connection-string')


def test_hub_list_api(monkeypatch, mock_mongo_client, mock_pymongo_client):

    #monkeypatch.setattr('MongoDBHandler', 'client', mock_pymongo_client)
    #mocker.patch.object(MongoDBHandler, 'connect', return_value=mock_mongo_client)

    monkeypatch.setattr('pymongo.MongoClient', mock_pymongo_client)
    monkeypatch.setattr('lambda_handlers.hubapi_list.MongoDBHandler', mock_mongo_client)

    mock_mongo_client.return_value = mock_mongo_client
    #mock_mongo_client.__enter__.return_value = Mock(spec=MongoDBHandler)
    mock_mongo_client.return_value.__enter__.return_value = mock_mongo_client


    #mock_mongo_client.__exit__.return_value = False
    #mock_mongo_client.connect.return_value = Mock(spec=pymongo.MongoClient)


    #monkeypatch.setattr('lambda_handlers.hubapi_list.MongoDBHandler.connect', mock_mongo_client)

    monkeypatch.setenv('JINA_DB_HOSTNAME', "TestingHost123")
    monkeypatch.setenv('JINA_DB_USERNAME', "TestingUser")
    monkeypatch.setenv('JINA_DB_PASSWORD', "TestingPassword")
    monkeypatch.setenv('JINA_DB_NAME', "TestingName")
    monkeypatch.setenv('JINA_DB_COLLECTION', "TestingCollection")
    # MM = Mock(return_value=mock_mongo_client)
    # PM = Mock(return_value=mock_pymongo_client)
    # monkeypatch.setattr('MongoDBHandler', MM)
    # monkeypatch.setattr(pymongo, "MongoClient", mock_pymongo_client)
    # mock_mongo_client.client.return_value = mock_pymongo_client

    # mock_mongo_client.database.return_value = 'mock_database'

    objs = []
    read_file = open('mongo_list_objs.json', "r")
    mongo_objs = json.load(read_file)
    objs = mongo_objs["collection"]

    mock_mongo_client.collection.return_value = {
    "collection" : [
        {
            "_id": {
                "id": "5f60529aeb8374c52d5e9fca"
            },
            "name": "jinahub/pod.encoder.randomsparseencoder",
            "version": "0.0.2",
            "path": "jina/hub/encoders/numeric/RandomSparseEncoder",
            "manifest_info": {
                "description": "RandomSparseEncoder encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`",
                "kind": "encoder",
                "type": "pod",
                "keywords": [
                "numeric",
                "sklearn"
                ],
                "author": "Jina AI Dev-Team (dev-team@jina.ai)",
                "license": "apache-2.0",
                "url": "https://jina.ai",
                "vendor": "Jina AI Limited",
                "documentation": "https://github.com/jina-ai/jina-hub"
            }
        },
        {
            "_id": {
                "id": "6f60529aeb8374c52d5e9fca"
            },
            "name": "jinahub/pod.encoder.dummyencoder",
            "version": "0.0.2",
            "path": "jina/hub/encoders/numeric/DummyEncoder",
            "manifest_info": {
                "description": "DummyEncoder encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`",
                "kind": "encoder",
                "type": "pod",
                "keywords": [
                "numeric",
                "sklearn"
                ],
                "author": "Jina AI Dev-Team (dev-team@jina.ai)",
                "license": "apache-2.0",
                "url": "https://jina.ai",
                "vendor": "Jina AI Limited",
                "documentation": "https://github.com/jina-ai/jina-hub"
            }
        },
        {
            "_id": {
                "id": "7f60529aeb8374c52d5e9fca"
            },
            "name": "jinahub/pod.crafter.deepsegmenter:0.0.2",
            "version": "0.0.2",
            "path": "jina/hub/crafters/nlp/DeepSegmenter",
            "manifest_info": {
                "description": "DeepSegmenter encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`",
                "kind": "encoder",
                "type": "pod",
                "keywords": [
                "numeric",
                "sklearn"
                ],
                "author": "Jina AI Dev-Team (dev-team@jina.ai)",
                "license": "apache-2.0",
                "url": "https://jina.ai",
                "vendor": "Jina AI Limited",
                "documentation": "https://github.com/jina-ai/jina-hub"
            }
        }
    ]}

    event = None
    with open('event.json', "r") as read_file:
        event = json.load(read_file)

    handler = lambda_handler(event, None)














# def test_list(monkeypatch, mock_mongo_client):
# 	WS = Mock(return_value=mock_mongo_client)
# 	monkeypatch.setattr('MongoDBHandler', WS)
#     mock_mongo_client.client.return_value = mongomock.MongoClient


#     monkeypatch.setattr(pymongo, "MongoClient", mongomock.MongoClient)
#     monkeypatch.setenv('JINA_DB_HOSTNAME', "TestingHost")
#     monkeypatch.setenv('JINA_DB_USERNAME', "TestingUser")
#     monkeypatch.setenv('JINA_DB_PASSWORD', "TestingPassword")
#     monkeypatch.setenv('JINA_DB_NAME', "TestingName")
#     monkeypatch.setenv('JINA_DB_COLLECTION', "TestingCollection")

#     objs = []
#     read_file = open('mongo_list_objs.json', "r")
#     mongo_objs = json.load(read_file)
#     objs = mongo_objs["collection"]

#     print(str(objs))
#     # mocker.patch('MongoDBHandler.connect', return_value=MongoDBHandler)
#     # mocker.patch('MongoDBHandler.collection', return_value=mongo_objs)
   
#     print('****')
#     print(mongo_objs)
#     # print(str(objs[0]))
#     event = None
#     with open('event.json', "r") as read_file:
#         event = json.load(read_file)

#     lambda_handler(event, None)




