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

    def find_one(self, query: Dict[str, Union[Dict, List]]) -> None:
        try:
            return self.collection.find_one(query)
        except pymongo.errors.PyMongoError as exp:
            self.logger.error(f'got an error while finding a document in the db {exp}')

    def find(self,
             query: Dict[str, Union[Dict, List]],
             projection: Dict[str, Union[Dict, List]],
             limit: int = 0) -> None:
        try:
            return self.collection.find(filter=query, projection=projection, limit=limit)
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


def _query_builder(params: Dict):
    logger = get_logger(context='query_builder')
    logger.info(f'Got the following params: {params}')

    sub_query = []
    if 'kind' in params:
        kind_query = {'manifest_info.kind': params['kind']}
        sub_query.append(kind_query)
    if 'type' in params:
        type_query = {'manifest_info.type': params['type']}
        sub_query.append(type_query)
    if 'name' in params:
        name_query = {'manifest_info.name': params['name']}
        sub_query.append(name_query)
    if 'keywords' in params:
        keywords_list = params['keywords'].split(',')
        keyword_query = {'manifest_info.keywords': {'$in': keywords_list}}
        sub_query.append(keyword_query)

    # A limit() value of 0 (i.e. limit(0)) is equivalent to setting no limit.
    limit = params.get('limit', 0)

    if sub_query:
        _executor_query = {'$and': sub_query}
        logger.info(f'Query to search in mongodb: {_executor_query}')
        return _executor_query, limit
    else:
        # select ALL
        # force the cursor to iterate over each object
        return {}, limit


def _return_json_builder(body, status):
    return {
        "isBase64Encoded": False,
        "headers": {
            "Content-Type": "application/json"
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
    hubpod_collection = str_to_ascii_to_base64_to_str(os.environ.get('JINA_HUBPOD_COLLECTION'))
    metadata_collection = str_to_ascii_to_base64_to_str(os.environ.get('JINA_METADATA_COLLECTION'))
    return hostname, username, password, database_name, hubpod_collection, metadata_collection


def lambda_handler(event, context):
    """Lambda handler to read data from Mongodb Atlas (Used to perform `jina hub list`)
    """
    logger = get_logger(context='hub_list')

    if not is_db_envs_set():
        logger.warning('MongoDB environment vars are not set! book-keeping skipped.')
        return _return_json_builder(body='Invalid Lambda environment',
                                    status=500)

    # what all fields to be fetched from the collection
    projection = {
        '_id': 0,
        'name': 1,
        'version': 1,
        'jina_version': 1,
        'manifest_info': 1
    }

    if event.get('queryStringParameters', {}):
        _executor_query, limit = _query_builder(params=event['queryStringParameters'])
    else:
        _executor_query, limit = {}, 0

    hostname, username, password, database_name, hubpod_collection, metadata_collection = read_environment()
    try:
        with MongoDBHandler(hostname=hostname, username=username, password=password,
                            database_name=database_name, collection_name=hubpod_collection) as db:
            cursor = db.find(query=_executor_query, projection=projection, limit=limit)
            all_manifests = list(cursor)
            if all_manifests:
                return _return_json_builder(body=json.dumps({"manifest": all_manifests}),
                                            status=200)
            return _return_json_builder(body="No docs found",
                                        status=400)
    except MongoDBException:
        return _return_json_builder(body='Couldn\'t connect to the database',
                                    status=502)
