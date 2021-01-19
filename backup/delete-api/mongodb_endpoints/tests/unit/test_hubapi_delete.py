import os

import json
import logging
import pymongo
import pytest
import mongomock
import mock

from jina.docker.hubio import HubIO

from ....delete-api.hubapi_delete import MongoDBHandler
from ....delete-api.hubapi_delete import lambda_handler
from jina.docker.hubapi import JAML


def get_logger(context='generic', file=True):
    logger = logging.getLogger(context)
    logger.setLevel(logging.DEBUG)
    return logger

@pytest.fixture
def mock_pymongo_mongoclient():
    return mongomock.MongoClient()

def test_delete(mocker, monkeypatch, mock_pymongo_mongoclient):
    monkeypatch.setattr(pymongo, "MongoClient", mock_pymongo_mongoclient)
    monkeypatch.setenv('JINA_DB_HOSTNAME', "TestingHost")
    monkeypatch.setenv('JINA_DB_USERNAME', "TestingUser")
    monkeypatch.setenv('JINA_DB_PASSWORD', "TestingPassword")
    monkeypatch.setenv('JINA_DB_NAME', "TestingName")
    monkeypatch.setenv('JINA_DB_COLLECTION', "TestingCollection")

    mock_client = mocker.patch.object(MongoDBHandler, 'client', autospec=True)
    mock_client.return_value = mock_pymongo_mongoclient
    mock_client.return_value.find_many = MongoDBHandler.find_many

    sample_collection_objects = [{'_id':1, 'name': 'first', 'manifest_info':{'kind': 'encoder', 'type': 'pod'}}, {'_id':2, 'name': 'second', 'manifest_info':{'kind': 'encoder', 'type': 'pod'}}]
    mock_collection = mongomock.MongoClient().db.collection
    for obj in sample_collection_objects:
        obj['_id'] = mock_collection.insert_one(obj).inserted_id
    mock_client.return_value.collection = mock_collection


    mock_connect = mocker.patch.object(MongoDBHandler, 'connect', autospec=True)
    mock_connect.return_value = mock_pymongo_mongoclient
    mock_connect.return_value.close = None
  
    objs = []
    read_file = open('mongo_list_objs.json', "r")
    mongo_objs = json.load(read_file)
    objs = mongo_objs["collection"]
    mock_pymongo_mongoclient.collection = objs
   
    event = None
    with open('event.json', "r") as read_file:
        event = json.load(read_file)

    lambda_handler(event, None)

