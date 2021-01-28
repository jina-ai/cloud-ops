__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import sys

from typing import List, Optional, Dict

from contextlib import ExitStack
import requests
import click
from jina.flow import Flow

# TODO make it available to the client
JINA_PORT = 45678
FLOW_HOST = os.environ['FLOW_HOST']
if FLOW_HOST is None:
    raise ValueError('set FLOW_HOST')


def config(task, indexer_query_type):
    # TODO make these configurable
    shards_encoder = 1
    shards_indexers = 2

    os.environ['JINA_SHARDS_ENCODER'] = str(shards_encoder)
    os.environ['JINA_SHARDS_INDEXERS'] = str(shards_indexers)
    os.environ.setdefault('JINA_WORKSPACE', './workspace')
    os.environ.setdefault('JINA_PORT', str(JINA_PORT))
    os.environ['JINA_DISTANCE_REVERSE'] = os.environ.get('JINA_DISTANCE_REVERSE',
                                                         'False')
    os.environ['OMP_NUM_THREADS'] = os.environ.get('OMP_NUM_THREADS', '1')

    # make sure you've built the images yourself
    # ex.: go to jina hub faiss directory, `docker build -f Dockerfile -t faiss_indexer_image:test .`
    if indexer_query_type == 'faiss':
        os.environ['JINA_USES'] = os.environ.get('JINA_USES_FAISS', 'docker://faiss_indexer_image:test')
        os.environ['JINA_USES_INTERNAL'] = 'pods/faiss_indexer.yml'
    elif indexer_query_type == 'annoy':
        os.environ['JINA_USES'] = os.environ.get('JINA_USES_ANNOY', 'docker://annoy_indexer_image:test')
        os.environ['JINA_USES_INTERNAL'] = 'pods/annoy_indexer.yml'
    elif indexer_query_type == 'scann':
        os.environ['JINA_USES'] = os.environ.get('JINA_USES_SCANN', 'docker://scann_indexer_image:test')
        os.environ['JINA_USES_INTERNAL'] = 'pods/scann_indexer.yml'
    elif indexer_query_type == 'numpy':
        os.environ['JINA_USES'] = 'pods/vec.yml'
        os.environ['JINA_USES_INTERNAL'] = ''
    elif task == 'query':
        raise ValueError(f'Indexer type {indexer_query_type} not supported')


# for index
def index():
    flow_index = Flow.load_config('flows/index.yml')
    with flow_index:
        print(f'Flow available at  {flow_index.host}, {flow_index.port_expose}')
        flow_index.block()

    return flow_index


# for search; annoy, faiss, scann with refIndexer
def query():
    flow_query = Flow.load_config('flows/query.yml')
    with flow_query:
        print(f'Flow available at  {flow_query.host}, {flow_query.port_expose}')
        flow_query.block()


def create_workspace(filepaths: List[str],
                     url: str = f'{FLOW_HOST}/workspaces') -> str:
    with ExitStack() as file_stack:
        files = [
            ('files', file_stack.enter_context(open(filepath, 'rb')))
            for filepath in filepaths
        ]
        print(f'uploading {files}')
        r = requests.post(url, files=files)
        assert r.status_code == 201

        workspace_id = r.json()
        print(f'Got workspace_id: {workspace_id}')
        return workspace_id


def create_flow_2(flow_yaml: str,
                  workspace_id: str = None,
                  url: str = f'{FLOW_HOST}/flows') -> str:
    with open(flow_yaml, 'rb') as f:
        r = requests.post(url,
                          data={'workspace_id': workspace_id},
                          files={'flow': f})
        print(f'Checking if the flow creation is succeeded: {r.json()}')
        assert r.status_code == 201
        return r.json()


def publish_flow(flow_yaml):
    dependencies = [f'pods/vec.yml', f'pods/encoder.yml', f'pods/redis.yml',
                    f'pods/craft.yml', f'pods/merge_and_topk.yml']
    workspace_id = create_workspace(filepaths=dependencies)
    ret = create_flow_2(flow_yaml, workspace_id)
    print(f' Creating flow results {ret}')


def assert_request(method: str,
                   url: str,
                   payload: Optional[Dict] = None,
                   expect_rcode: int = 200):
    try:
        if payload:
            response = getattr(requests, method)(url, json=payload)
        else:
            response = getattr(requests, method)(url)
        assert response.status_code == expect_rcode
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'got an exception while invoking request {e!r}')


def close_flow(flow_id):
    assert_request(method='delete',
                   url=f'{FLOW_HOST}/flows/{flow_id}',
                   payload={'workspace': False})


@click.command()
@click.option('--task', '-t')
@click.option('--indexer-query-type', '-i')
@click.option('--jinad')
@click.option('--flow-id')
def main(task, indexer_query_type, jinad, flow_id):
    if jinad == 'index':
        publish_flow('flows/index.yml')
    elif jinad == 'query':
        publish_flow('flows/query.yml')
    elif jinad == 'remove':
        close_flow(flow_id)
    else:
        config(task, indexer_query_type)
        if task == 'index':
            index()
        elif task == 'query':
            query()
        else:
            raise NotImplementedError(
                f'unknown task: {task}. A valid task is either `index` or `query`.')


if __name__ == '__main__':
    main()
