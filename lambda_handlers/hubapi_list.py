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

    def aggregate(self, pipeline: List[Dict]):
        try:
            return self.collection.aggregate(pipeline)
        except pymongo.errors.PyMongoError as exp:
            self.logger.error(f'got an error while executing an aggregation pipeline in the collection {exp}')

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
    keys = ['JINA_DB_HOSTNAME', 'JINA_DB_USERNAME', 'JINA_DB_PASSWORD', 'JINA_DB_NAME', 'JINA_HUBPOD_COLLECTION', 'JINA_METADATA_COLLECTION']
    return all(len(os.environ.get(k, '')) > 0 for k in keys)


def configure_matches_stage(**kwargs):
    matches_stage = {
        '$match': {
        }
    }

    for field in ['jina_version', 'version']:
        if field in kwargs:
            matches_stage['$match'][field] = kwargs[field]

    for field in ['kind', 'type']:
        if field in kwargs:
            matches_stage['$match'][f'manifest_info.{field}'] = kwargs[field].lower()

    if isinstance(kwargs.get('keywords', None), list):
        matches_stage['$match'][f'manifest_info.keywords'] = {'$in': [i.lower() for i in kwargs['keywords']]}

    if isinstance(kwargs.get('name', None), str):
        matches_stage['$match']['name'] = {'$regex': f'.*{kwargs["name"].lower()}.*'}

    if matches_stage['$match']:
        return matches_stage


def configure_aggregation(**kwargs):

    aggregation_pipeline = []

    """
    Stage 1:
    - Form `$match` from different query strings
    - This will be executed only if proper query strings are passed
    - Accepted query strings -
      - `name` -> simple regex search
      - `jina_version` -> exact match
      - `version` -> exact match
      - `kind` -> exact match
      - `type` -> exact match
      - `keywords` -> array search
    """
    matches_stage = configure_matches_stage(**kwargs)
    if matches_stage:
        aggregation_pipeline.append(matches_stage)

    """
    Stage 2:
    - Sort by `name`, `jina_version` & `version`
    - `name`: 1 - this sorts alphabetically (set to -1 for reverse order)
    - `jina_version`: -1 - Sorted according to semver. This should always be latest first.
    - `version`: -1 - Sorted according to semver. This should also be latest first.
    """
    init_sort_stage = {
        '$sort': {
            'name': 1,
            "_jina_version.major": -1,
            "_jina_version.minor": -1,
            "_jina_version.patch": -1,
            "_version.major": -1,
            "_version.minor": -1,
            "_version.patch": -1
        }
    }
    aggregation_pipeline.append(init_sort_stage)

    """
    Stage 3:
    - Groupby `name` of the executor
    - Add `jina_version`, `version` & `manifest_info` to `images` list (this will be ordered)
    """
    group_by_name_stage = {
        '$group': {
            '_id': {
                'name': '$name'
            },
            'images': {
                '$push': {
                    'jina_version': '$jina_version',
                    'version': '$version',
                    'manifest_info': '$manifest_info'
                }
            }
        }
    }
    aggregation_pipeline.append(group_by_name_stage)

    """
    Stage 4:
    - Since groupby removes the sort on `name`, sort it again
    """
    sort_by_name_again_stage = {
        '$sort': {
            '_id.name': 1
        }
    }
    aggregation_pipeline.append(sort_by_name_again_stage)

    """
    Stage 5:
    - Pagination: Fetch images only after a certain image name
    """
    if 'after' in kwargs:
        pagination_filter_stage = {
            '$match': {
                '_id.name': {
                    '$gt': kwargs['after']
                }
            }
        }
        aggregation_pipeline.append(pagination_filter_stage)

    """
    Stage 6:
    - Fetch n results at a time
    """
    if 'n_per_page' in kwargs:
        limit_stage = {
            '$limit': int(kwargs['n_per_page'])
        }
        aggregation_pipeline.append(limit_stage)

    """
    Stage 7:
     - 1st element of the `images` list would be the latest executor
    """
    project_executors_stage = {
        '$project': {
            'image_to_be_sent': {
                '$arrayElemAt': ['$images', 0]
            }
        }
    }
    aggregation_pipeline.append(project_executors_stage)

    """
    # Stage 8:
    # - Finalize the set of arguments to be set
    """
    project_final_args_stage = {
        '$project': {
            'docker-name': '$_id.name',
            'version': '$image_to_be_sent.version',
            'jina-version': '$image_to_be_sent.jina_version',
            'docker-command': {
                '$concat': ['docker pull ', '$_id.name', ':', '$image_to_be_sent.version', '-', '$image_to_be_sent.jina_version']
            },
            'name': '$image_to_be_sent.manifest_info.name',
            'description': '$image_to_be_sent.manifest_info.description',
            'type': '$image_to_be_sent.manifest_info.type',
            'kind': '$image_to_be_sent.manifest_info.kind',
            'keywords': '$image_to_be_sent.manifest_info.keywords',
            'platform': '$image_to_be_sent.manifest_info.platform',
            'license': '$image_to_be_sent.manifest_info.license',
            'url': '$image_to_be_sent.manifest_info.url',
            'documentation': '$image_to_be_sent.manifest_info.documentation',
            'author': '$image_to_be_sent.manifest_info.author',
            'avatar': '$image_to_be_sent.manifest_info.avatar',
            '_id': 0
        }
    }
    aggregation_pipeline.append(project_final_args_stage)
    return aggregation_pipeline


def _return_json_builder(body, status):
    return {
        "isBase64Encoded": False,
        "headers": {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
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


def handle_query_strings(event):
    query_string_params = event['queryStringParameters']
    if event['multiValueQueryStringParameters'] and 'keywords' in event['multiValueQueryStringParameters']:
        query_string_params['keywords'] = event["multiValueQueryStringParameters"]['keywords']

    if query_string_params:
        query_string_params = {k.replace('-', '_'): v for k, v in query_string_params.items()}

    return query_string_params if query_string_params else {}


def lambda_handler(event, context):
    """Lambda handler to read data from Mongodb Atlas (Used to perform `jina hub list`)
    """
    logger = get_logger(context='hub_list')

    if not is_db_envs_set():
        logger.error('MongoDB environment vars are not set! book-keeping skipped.')
        return _return_json_builder(body='Invalid Lambda environment',
                                    status=500)
    query_string_params = handle_query_strings(event)
    hostname, username, password, database_name, hubpod_collection, metadata_collection = read_environment()

    try:
        with MongoDBHandler(hostname=hostname, username=username, password=password,
                            database_name=database_name, collection_name=hubpod_collection) as db:
            cursor = db.aggregate(pipeline=configure_aggregation(**query_string_params))
            current_images = list(cursor)
            if current_images:
                return _return_json_builder(body=json.dumps(current_images),
                                            status=200)
            return _return_json_builder(body="No docs found",
                                        status=400)
    except MongoDBException:
        return _return_json_builder(body='Couldn\'t connect to the database',
                                    status=502)
