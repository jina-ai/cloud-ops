import os
import json
import base64
import logging
from typing import Optional, Dict, List, Union

import pymongo


def get_logger(context='generic', file=True):
    logger = logging.getLogger(context)
    logger.setLevel(logging.DEBUG)
    return logger


class MongoDBException(Exception):
    """ Any errors raised by MongoDb """


class MongoDBHandler:
    """
    Mongodb Handler to connect to the database & insert documents in the collection
    """

    def __init__(self, hostname: str, username: str, password: str,
                 database_name: str, collection_name: str):
        self.logger = get_logger(self.__class__.__name__)
        self.hostname = hostname
        self.username = username
        self.password = password
        self.database_name = database_name
        self.collection_name = collection_name
        self.connection_string = \
            f'mongodb+srv://{self.username}:{self.password}@{self.hostname}'

    def __enter__(self):
        return self.connect()

    def connect(self) -> 'MongoDBHandler':
        try:
            self.client = pymongo.MongoClient(self.connection_string)
            self.client.admin.command('ismaster')
            self.logger.info('Successfully connected to the database')
        except pymongo.errors.ConnectionFailure:
            raise MongoDBException('Database server is not available')
        except pymongo.errors.ConfigurationError:
            raise MongoDBException('Credentials passed are not correct!')
        except pymongo.errors.PyMongoError as exp:
            raise MongoDBException(exp)
        except Exception as exp:
            raise MongoDBException(exp)
        return self

    @property
    def database(self):
        return self.client[self.database_name]

    @property
    def collection(self):
        return self.database[self.collection_name]

    def find(self, query: Dict[str, Union[Dict, List]]) -> None:
        try:
            return self.collection.find_one(query)
        except pymongo.errors.PyMongoError as exp:
            self.logger.error(f'got an error while finding a document in the db {exp}')

    def find_many(self, query: Dict[str, Union[Dict, List]]) -> None:
        try:
            return self.collection.find(query, limit=10)
        except pymongo.errors.PyMongoError as exp:
            self.logger.error(f'got an error while finding a document in the db {exp}')

    def insert(self, document: str) -> Optional[str]:
        try:
            result = self.collection.insert_one(document)
            self.logger.info(f'Pushed current summary to the database')
            return result.inserted_id
        except pymongo.errors.PyMongoError as exp:
            self.logger.error(f'got an error while inserting a document in the db {exp}')

    def replace(self, document: Dict, query: Dict):
        try:
            result = self.collection.replace_one(query, document)
            return result.modified_count
        except pymongo.errors.PyMongoError as exp:
            self.logger.error(f'got an error while replacing a document in the db {exp}')

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.client.close()
        except pymongo.errors.PyMongoError as exp:
            raise MongoDBException(exp)


def is_db_envs_set():
    """ Checks if any of the db env variables are not set """
    keys = ['JINA_DB_HOSTNAME', 'JINA_DB_USERNAME', 'JINA_DB_PASSWORD', 'JINA_DB_NAME', 'JINA_DB_COLLECTION']
    return all(len(os.environ.get(k, '')) > 0 for k in keys)


def _handle_dot_in_keys(document: Dict[str, Union[Dict, List]]) -> Union[Dict, List]:
    updated_document = {}
    for key, value in document.items():
        if isinstance(value, dict):
            value = _handle_dot_in_keys(value)
        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            value[0] = _handle_dot_in_keys(value[0])
        updated_document[key.replace('.', '_')] = value
    return updated_document


def _return_json_builder(body, status):
    return {
        "isBase64Encoded": False,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin":"*"
        },
        "statusCode": int(status),
        "body": body
    }


def str_to_ascii_to_base64_to_str(text):
    return base64.b64decode(text.encode('ascii')).decode('ascii')


def read_environment():
    hostname = str_to_ascii_to_base64_to_str(os.environ.get('JINA_DB_HOSTNAME'))
    username = str_to_ascii_to_base64_to_str(os.environ.get('JINA_DB_USERNAME'))
    password = str_to_ascii_to_base64_to_str(os.environ.get('JINA_DB_PASSWORD'))
    database_name = str_to_ascii_to_base64_to_str(os.environ.get('JINA_DB_NAME'))
    collection_name = str_to_ascii_to_base64_to_str(os.environ.get('JINA_DB_COLLECTION'))
    return hostname, username, password, database_name, collection_name


def lambda_handler(event, context):
    """Lambda handler to write data into Mongodb Atlas (Used to perform `jina hub push`)
    """
    logger = get_logger(context='hub_push')

    if not is_db_envs_set():
        logger.warning('MongoDB environment vars are not set! bookkeeping skipped.')
        return _return_json_builder(body='Invalid Lambda environment',
                                    status=500)

    try:
        if 'body' not in event or event['body'] is None:
            return _return_json_builder(body='Invalid body passed in event',
                                        status=500)

        summary = json.loads(event['body'])
        build_summary = _handle_dot_in_keys(document=summary)
        _build_query = {
            'name': build_summary['name'],
            'version': build_summary['version']
        }

        # this ensure _current_build_history is always a list
        if not isinstance(build_summary['build_history'], list):
            build_summary['build_history'] = list(build_summary['build_history'])

        _current_build_history = build_summary['build_history']

        hostname, username, password, database_name, collection_name = read_environment()
        with MongoDBHandler(hostname=hostname, username=username, password=password,
                            database_name=database_name, collection_name=collection_name) as db:
            existing_doc = db.find(query=_build_query)
            if existing_doc:
                build_summary['build_history'] = existing_doc['build_history'] + _current_build_history
                _modified_count = db.replace(document=build_summary,
                                             query=_build_query)
                logger.info(f'Updated the build + push summary in db. {_modified_count} documents modified')
                return _return_json_builder(body='Updated existing doc in MongoDB',
                                            status=200)
            else:
                _inserted_id = db.insert(document=build_summary)
                logger.info(f'Inserted the build + push summary in db with id {_inserted_id}')
                return _return_json_builder(body='Created new doc in MongoDB',
                                            status=200)
    except KeyError as exp:
        logger.error(f'Got following keyerror during `hub_push` {exp}')
        return _return_json_builder(body='KeyError. Please check Lambda logs',
                                    status=500)
    except Exception as exp:
        logger.error(f'Got following exception for `hub_push` {exp}')
        return _return_json_builder(body='Mongodb Push Failed. Please check Lambda logs',
                                    status=500)
