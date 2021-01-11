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
    sample_collection_objects = [{'_id':1, 'name': 'first', 'manifest_info':{'kind': 'encoder', 'type': 'pod'}}, {'_id':2, 'name': 'second', 'manifest_info':{'kind': 'encoder', 'type': 'pod'}}]
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

    mock_client = mocker.patch.object(MongoDBHandler, 'client', autospec=True)
    mock_client.return_value = mock_pymongo_mongoclient
    mock_client.return_value.find_many = MongoDBHandler.find_many(mock_client, query=use_query)
    sample_collection_objects = [{'_id':1, 'name': 'first', 'manifest_info':{'kind': 'encoder', 'type': 'pod'}}, {'_id':2, 'name': 'second', 'manifest_info':{'kind': 'encoder', 'type': 'pod'}}]
    mock_collection = mongomock.MongoClient().db.collection #mock_pymongo_mongoclient.db.collection
    for obj in sample_collection_objects:
        obj['_id'] = mock_collection.insert_one(obj).inserted_id
    mock_client.return_value.collection = mock_collection #mongomock.Collection
    mock_pymongo_mongoclient.return_value.collection = mock_collection

    mock_connect = mocker.patch.object(MongoDBHandler, 'connect', autospec=True)
    mock_connect.return_value = mock_pymongo_mongoclient
    mock_connect.return_value.close = None
  
    objs = []
    with open('mongo_list_objs.json', "r") as read_file:
        mongo_objs = json.load(read_file)
        objs = mongo_objs["collection"]
    # mock_pymongo_mongoclient.collection = objs
    # mock_client.return_value.collection = objs #mongomock.Collection


    mock_my_collection = mocker.patch.object(MongoDBHandler, 'collection', autospec=True)
    mock_my_collection.return_value = sample_collection_objects
    print(str(objs))
    print(mongo_objs)

    result = lambda_handler(event, None)
