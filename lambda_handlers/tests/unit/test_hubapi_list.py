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

# @mock.patch("pymongo.MongoClient")
# @mock.patch("pymongo.collection.Collection")
# @mock.patch("pymongo.database.Database") #MongoDBHandler

@mock.patch("lambda_handlers.hubapi_list.MongoDBHandler.connect")
@mock.patch("lambda_handlers.hubapi_list.MongoDBHandler.find")
@mock.patch("lambda_handlers.hubapi_list.MongoDBHandler.find_many")
def test_list(mock_find_many, mock_find, mock_connect, monkeypatch):
# def test_list(mock_db, mock_collection, mock_mongo, mock_handler, monkeypatch):

    #mock_handler.return_value = mongomock.MongoClient
    mock_find_many.return_value = {}
    mock_find.return_value = {}
    mock_connect.return_value = MongoDBHandler #mongomock.MongoClient
    # mock_mongo.return_value = mongomock.MongoClient
    # mock_collection.return_value = mongomock.collection.Collection
    # mock_db.return_value = mongomock.database.Database 
    setattr(mongomock.database.Database, "address", ("localhost", 27017))


    

    monkeypatch.setattr(pymongo.collection, "Collection", mongomock.collection.Collection)
    monkeypatch.setattr(pymongo, "MongoClient", mongomock.MongoClient)

    monkeypatch.setenv('JINA_DB_HOSTNAME', "TestingHost")
    monkeypatch.setenv('JINA_DB_USERNAME', "TestingUser")
    monkeypatch.setenv('JINA_DB_PASSWORD', "TestingPassword")
    monkeypatch.setenv('JINA_DB_NAME', "TestingName")
    monkeypatch.setenv('JINA_DB_COLLECTION', "TestingCollection")

    #collection = mock_mongo.db.collection
    collection = mongomock.MongoClient().db.collection ## test with l31 and l32

    objs = []

    read_file = open('mongo_list_objs.json', "r")
    mongo_objs = json.load(read_file)
    objs = mongo_objs["collection"]
   
    collection.insert(objs)

    event = None
    with open('event.json', "r") as read_file:
        event = json.load(read_file)

    lambda_handler(event, None)

