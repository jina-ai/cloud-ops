__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
from contextlib import ExitStack
from typing import List, Optional, Dict

import click
import requests
from jina.flow import Flow

# TODO make it available to the client
JINA_PORT = 45678
FLOW_HOST_PORT = os.environ.get('FLOW_HOST_PORT')


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
                     url: str = f'{FLOW_HOST_PORT}/workspaces') -> str:
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


def create_remote_flow(flow_yaml: str,
                       workspace_id: str = None,
                       url: str = f'{FLOW_HOST_PORT}/flows') -> str:
    with open(flow_yaml, 'rb') as f:
        r = requests.post(url,
                          data={'workspace_id': workspace_id},
                          files={'flow': f})
        print(f'Checking if the flow creation is succeeded: {r.json()}')
        assert r.status_code == 201
        return r.json()


def publish_flow(flow_yaml, workspace_id=None):
    # TODO adjust for reading either image or nlp search
    dependencies = [f'pods/vec.yml', f'pods/encoder.yml', f'pods/redis.yml',
                    f'pods/craft.yml', f'pods/merge_and_topk.yml']
    if workspace_id is None:
        workspace_id = create_workspace(filepaths=dependencies)
    ret = create_remote_flow(flow_yaml, workspace_id)
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
                   url=f'{FLOW_HOST_PORT}/flows/{flow_id}',
                   payload={'workspace': False})


@click.command()
@click.option('--task', '-t', type=click.Choice(['index', 'query']))
@click.option('--indexer-query-type', '-i', type=click.Choice(['faiss', 'annoy', 'numpy', 'scann']))
@click.option('--jinad', default=None, type=click.Choice(['index', 'query', 'remove']))
@click.option('--flow-id', default=None)
@click.option('--ws', default=None)
def main(task, indexer_query_type, jinad, flow_id, ws):
    if jinad is not None:
        if FLOW_HOST_PORT is None:
            raise ValueError('set FLOW_HOST_PORT')
        print(f'Using jinad gateway on {FLOW_HOST_PORT}')
        if ws:
            print(f'reusing workspace id {ws}')
        if jinad == 'index':
            # TODO make it possible to use either image or text flows
            # `flows/{dataset}/{task}.yml`
            publish_flow('flows/index.yml', ws)
        elif jinad == 'query':
            publish_flow('flows/query.yml', ws)
        elif jinad == 'remove':
            close_flow(flow_id)
    else:
        print(f'creating local flow on task {task}...')
        config(task, indexer_query_type)
        if task == 'index':
            index()
        elif task == 'query':
            query()


if __name__ == '__main__':
    main()
