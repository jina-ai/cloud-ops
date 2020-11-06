import os

import json
import logging
import pytest
import mongomock
import mock

from jina.docker.hubio import HubIO

from ..hubapi_list import MongoDBHandler
from ..hubapi_list import lambda_handler
from jina.helper import yaml


def get_logger(context='generic', file=True):
    logger = logging.getLogger(context)
    logger.setLevel(logging.DEBUG)
    return logger

@mock.patch("pymongo.MongoClient")
@mock.patch("pymongo.collection.Collection")
@mock.patch("pymongo.database.Database") #MongoDBHandler
def test_list(mock_db, mock_collection, mock_mongo, monkeypatch):

    mock_mongo.return_value = mongomock.MongoClient
    mock_collection.return_value = mongomock.collection.Collection
    mock_db.return_value = mongomock.database.Database 
    setattr(mongomock.database.Database, "address", ("localhost", 27017))

    monkeypatch.setenv('JINA_DB_HOSTNAME', "TestingHost")
    monkeypatch.setenv('JINA_DB_USERNAME', "TestingUser")
    monkeypatch.setenv('JINA_DB_PASSWORD', "TestingPassword")
    monkeypatch.setenv('JINA_DB_NAME', "TestingName")
    monkeypatch.setenv('JINA_DB_COLLECTION', "TestingCollection")

    collection = mock_mongo.db.collection
    collection = mongomock.MongoClient().db.collection ## test with l31 and l32

    objs = []

    fname = os.path.join(os.getcwd(), 'lambda_handlers/unit_tests/mongo_list_objs.json')
    read_file = open(fname, "r")
    mongo_objs = json.load(read_file)
    objs = mongo_objs["collection"]
   
    collection.insert(objs)

    event = None
    fname = os.path.join(os.getcwd(), 'lambda_handlers/unit_tests/event.json')
    with open(fname, "r") as read_file:
        event = json.load(read_file)

    lambda_handler(event, None)

