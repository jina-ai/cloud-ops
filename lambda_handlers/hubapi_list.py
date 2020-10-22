import json
import logging
import os
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

    def find_many(self, query: Dict[str, Union[Dict, List]], limit: int = 0) -> None:
        try:
            return self.collection.find(filter=query, limit=limit)
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
    logger.info(f'Got the following parans: {params}')
    
    if not params:
        return {}, 0
    
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

    # A limit() value of 0 (i.e. .limit(0)) is equivalent to setting no limit.
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


def lambda_handler(event, context):
    """Lambda handler to read data from Mongodb Atlas (Used to perform `jina hub list`)
    """
    logger = get_logger(context='hub_list')

    if not is_db_envs_set():
        logger.warning('MongoDB environment vars are not set! bookkeeping skipped.')
        return _return_json_builder(body='Invalid Lambda environment',
                                    status=500)

    _executor_query = _query_builder(params=event.get('queryStringParameters', {}))
    with MongoDBHandler(hostname=os.environ['JINA_DB_HOSTNAME'],
                        username=os.environ['JINA_DB_USERNAME'],
                        password=os.environ['JINA_DB_PASSWORD'],
                        database_name=os.environ['JINA_DB_NAME'],
                        collection_name=os.environ['JINA_DB_COLLECTION']) as db:
        existing_docs = db.find_many(*_executor_query)
        if existing_docs:
            all_manifests = [doc['manifest_info'] for doc in existing_docs]
            if all_manifests:
                return _return_json_builder(body=json.dumps({"manifest": all_manifests}),
                                            status=200)
            return _return_json_builder(body="No docs found",
                                        status=400)

    return _return_json_builder(body='Invalid filters passed',
                                status=400)
