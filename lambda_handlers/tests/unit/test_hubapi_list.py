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
    # for obj in sample_collection_objects:
    #     obj['_id'] = client.db.collection.insert_one(obj).inserted_id
    # print('** fix collection count is *** '+ str(client.db.collection.count()))
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

    sample_collection_objects = [{'_id':111, 'name': 'first', 'manifest_info':{'kind': 'encoder', 'type': 'pod'}}, {'_id':222, 'name': 'second', 'manifest_info':{'kind': 'encoder', 'type': 'pod'}}]
    mock_collection = mock_pymongo_mongoclient.db.collection #mongomock.MongoClient().db.collection 
    mock_collection.insert_many(sample_collection_objects)
    # for obj in sample_collection_objects:
    #     #mock_collection.insert_one(obj)
    #     obj['_id'] = mock_collection.insert_one(obj).inserted_id
    assert mock_collection.count() == 2
    print('** mox count is *** '+ str(mock_collection.count()))
    print('*****mox  collections has objs **** '+str(list(mock_collection.find())))
    #mock_client.return_value.db.collection = mock_collection #mongomock.Collection
    #mock_pymongo_mongoclient.return_value.db.collection = mock_collection

    #mock_client.return_value.collection = mock_collection #mongomock.Collection
    #mock_pymongo_mongoclient.return_value.collection = mock_collection


    use_query = _query_builder(params=event.get('queryStringParameters', {}))

    mock_client = mocker.patch.object(MongoDBHandler, 'client', autospec=True)
    mock_client.return_value = mock_pymongo_mongoclient
    mock_client.return_value.find_many = MongoDBHandler.find_many(mock_client, query=use_query)

    mock_connect = mocker.patch.object(MongoDBHandler, 'connect', autospec=True)
    mock_connect.return_value = mock_pymongo_mongoclient
    mock_connect.return_value.close = None
  
    objs = []
    with open('mongo_list_objs.json', "r") as read_file:
        mongo_objs = json.load(read_file)
        objs = mongo_objs["collection"]
    # mock_pymongo_mongoclient.collection = objs
    # mock_client.return_value.collection = objs #mongomock.Collection


    # mock_my_collection = mocker.patch.object(MongoDBHandler, 'collection', autospec=True)
    # mock_my_collection.return_value = sample_collection_objects
    # print(str(objs))
    # print(mongo_objs)

    with mock.patch('lambda_handlers.hubapi_list.MongoDBHandler.collection', new_callable=mock.PropertyMock) as mock_handler_collection:
        mock_handler_collection.return_value = mock_collection

        # mock_my_collection = mocker.patch.object(MongoDBHandler, 'collection', autospec=True)
        # mock_my_collection.return_value =  mock_collection #sample_collection_objects
        # monkeypatch.setattr(MongoDBHandler, "collection", mock_collection) #sample_collection_objects

        type(mock_pymongo_mongoclient).collection = mock.PropertyMock(return_value=mock_collection)
        type(mock_client).collection = mock.PropertyMock(return_value=mock_collection)
        type(mock_pymongo_mongoclient).collection.find = mock.PropertyMock(return_value=sample_collection_objects)
        type(mock_client).collection.find = mock.PropertyMock(return_value=sample_collection_objects)

        result = lambda_handler(event, None)
        print('*** result items are **** ')
        print('*******    *******')
        print(str(result.items()))
        mongomock.database.Collection






# lots to learn from this
# reason could be : I should mock the MongoDBHandler class oject itself - set it's client property to mongomock
# not the entire object itself
# then set its database proprty to mongomock db, similarly collection, find_many - this is the right way to go
# so find_many would invoke mongomock's find- this seems to be crux