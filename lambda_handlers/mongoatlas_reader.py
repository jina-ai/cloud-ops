import os
import json
import logging
from typing import Optional, Dict, List, Union

import pymongo


def lambda_handler(event, context):
    """Lambda handler to read data from Mongodb Atlas (Used to perform `jina hub list`)
    """
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
            
    def _query_builder(params):
        print(params)
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
            keyword_query = {'manifest_info.keywords': {'$all': keywords_list}}
            sub_query.append(keyword_query)

        _executor_query = {'$and': sub_query}
        return _executor_query
    
    if 'queryStringParameters' in event:
        _executor_query = _query_builder(params=event['queryStringParameters'])
        with MongoDBHandler(hostname=os.environ['JINA_DB_HOSTNAME'],
                            username=os.environ['JINA_DB_USERNAME'],
                            password=os.environ['JINA_DB_PASSWORD'],
                            database_name=os.environ['JINA_DB_NAME'],
                            collection_name=os.environ['JINA_DB_COLLECTION']) as db:
            existing_docs = db.find_many(query=_executor_query)
            all_manifests = []
            if existing_docs:
                for doc in existing_docs:
                    manifest_info = doc['manifest_info']
                    all_manifests.append(manifest_info)
                
                return {
                    "isBase64Encoded": False,
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "statusCode": 200,
                    "body": json.dumps({"manifest": all_manifests})
                }
    
    return {
        "isBase64Encoded": False,
        "headers": {
            'Content-Type': 'application/json'
        },
        "statusCode": 400,
        "body": "Invalid keys passed!",
    }
