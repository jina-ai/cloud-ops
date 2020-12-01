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
from jina.helper import yaml


def get_logger(context='generic', file=True):
    logger = logging.getLogger(context)
    logger.setLevel(logging.DEBUG)
    return logger

@pytest.fixture
def mock_pymongo_mongoclient():
    #return pymongo.MongoClient
    return mongomock.MongoClient  #('fake-connection-string')

@pytest.fixture
def mock_mongohandler():
    return MongoDBHandler 

#@pytest.fixture
def test_list(monkeypatch, mock_pymongo_mongoclient, mock_mongohandler):

    # monkeypatch.setattr(flow.flow_store, '_create', mock_pymongo_mongohandler)


    monkeypatch.setattr(pymongo, "MongoClient", mock_pymongo_mongoclient)
    #monkeypatch.setattr(pymongo.MongoClient, "admin", None)


    mock_mongohandler.connect.return_value = mock_mongohandler

    monkeypatch.setenv('JINA_DB_HOSTNAME', "TestingHost")
    monkeypatch.setenv('JINA_DB_USERNAME', "TestingUser")
    monkeypatch.setenv('JINA_DB_PASSWORD', "TestingPassword")
    monkeypatch.setenv('JINA_DB_NAME', "TestingName")
    monkeypatch.setenv('JINA_DB_COLLECTION', "TestingCollection")

    objs = []
    read_file = open('mongo_list_objs.json', "r")
    mongo_objs = json.load(read_file)
    objs = mongo_objs["collection"]
    #mock_pymongo_mongoclient.collection = objs
    mock_mongohandler.collection = objs


    print(str(objs))
    # mocker.patch('MongoDBHandler.connect', return_value=MongoDBHandler)
    # mocker.patch('MongoDBHandler.collection', return_value=mongo_objs)
   

    print('****')
    print(mongo_objs)
    # print(str(objs[0]))
    event = None
    with open('event.json', "r") as read_file:
        event = json.load(read_file)

    lambda_handler(event, None)



















# @mock.patch("lambda_handlers.hubapi_list.MongoDBHandler.connect")
# # @mock.patch("lambda_handlers.hubapi_list.MongoDBHandler.find")
# # @mock.patch("lambda_handlers.hubapi_list.MongoDBHandler.find_many")
# @mock.patch("lambda_handlers.hubapi_list.MongoDBHandler.collection")
# def test_list(mock_collection, mock_connect, monkeypatch):
# # def test_list(mock_collection, mock_find_many, mock_find, mock_connect, monkeypatch):

#     # mock_find_many.return_value = {}
#     # mock_find.return_value = {}
#     mock_connect.return_value = MongoDBHandler #mongomock.MongoClient
#     setattr(mongomock.database.Database, "address", ("localhost", 27017))
#     # monkeypatch.setattr(pymongo.collection, "Collection", mongomock.collection.Collection)
#     monkeypatch.setattr(pymongo, "MongoClient", mongomock.MongoClient)
#     monkeypatch.setenv('JINA_DB_HOSTNAME', "TestingHost")
#     monkeypatch.setenv('JINA_DB_USERNAME', "TestingUser")
#     monkeypatch.setenv('JINA_DB_PASSWORD', "TestingPassword")
#     monkeypatch.setenv('JINA_DB_NAME', "TestingName")
#     monkeypatch.setenv('JINA_DB_COLLECTION', "TestingCollection")

#     collection = mongomock.MongoClient().db.collection

#     objs = []

#     read_file = open('mongo_list_objs.json', "r")
#     mongo_objs = json.load(read_file)
#     objs = mongo_objs["collection"]
   
#     mock_collection.return_value = mongo_objs
#     #monkeypatch.setattr(pymongo.collection, "Collection", mongo_objs)

#     #collection.insert(objs)

#     print('****')
#     print(mongo_objs)
#     # print(str(objs[0]))
#     event = None
#     with open('event.json', "r") as read_file:
#         event = json.load(read_file)

#     lambda_handler(event, None)
