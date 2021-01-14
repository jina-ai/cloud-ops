import os

import json
import logging
import pymongo
import pytest
import mongomock
import mock

from jina.docker.hubio import HubIO

from ...hubapi_list import MongoDBHandler
from ...hubapi_list import lambda_handler
from ...hubapi_list import _query_builder

from jina.docker.hubapi import JAML
from pymongo import MongoClient

@pytest.fixture
def mock_pymongo_mongoclient():
    client = mongomock.MongoClient()
    sample_collection_objects = []
    with open('mongo_list_objs.json', "r") as read_file:
        mongo_objs = json.load(read_file)
        sample_collection_objects = mongo_objs["collection"]
    for obj in sample_collection_objects:
        obj['_id'] = client.db.collection.insert_one(obj).inserted_id
    return client

def test_list(mocker, monkeypatch, mock_pymongo_mongoclient):
    monkeypatch.setattr(pymongo, "MongoClient", mock_pymongo_mongoclient)
    monkeypatch.setenv('JINA_DB_HOSTNAME', "TestingHost")
    monkeypatch.setenv('JINA_DB_USERNAME', "TestingUser")
    monkeypatch.setenv('JINA_DB_PASSWORD', "TestingPassword")
    monkeypatch.setenv('JINA_DB_NAME', "TestingName")
    monkeypatch.setenv('JINA_DB_COLLECTION', "TestingCollection")

    event = None
    with open('event.json', "r") as read_file:
        event = json.load(read_file)
    use_query = _query_builder(params=event.get('queryStringParameters', {}))

    assert use_query[0] == {'$and': [{'manifest_info.kind': 'encoder'}, {'manifest_info.type': 'pod'}]}

    # assert that mock collection has 3 objects, two with kind encoder, one with type indexer, type pod.
    mock_collection = mock_pymongo_mongoclient.db.collection
    assert mock_collection.count() == 3

  
    mock_client = mocker.patch.object(MongoDBHandler, 'client', autospec=True)
    mock_client.return_value = mock_pymongo_mongoclient

    mock_connect = mocker.patch.object(MongoDBHandler, 'connect', autospec=True)
    mock_connect.return_value.close = None
  
    # assert that 2 objects with kind encoder are returned, type pod
    assert mock_collection.count(use_query[0]) == 2
    result = lambda_handler(event, None)