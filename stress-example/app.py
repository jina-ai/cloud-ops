__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
from contextlib import ExitStack
from glob import glob
from typing import List, Optional, Dict

import click
import requests

# TODO make it available to the client
FLOW_HOST_PORT = os.environ.get('FLOW_HOST_PORT')


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


def publish_flow(flow_yaml, dataset, workspace_id=None):
    dependencies = glob(f'{dataset}/*.yml')
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
@click.option('--jinad', default=None, type=click.Choice(['index', 'query', 'remove']))
@click.option('--flow-id', default=None)
@click.option('--ws', default=None)
@click.option('--dataset', default=None, type=click.Choice(['image', 'text']))
def main(jinad, flow_id, ws, dataset):
    if FLOW_HOST_PORT is None:
        raise ValueError('set FLOW_HOST_PORT')

    print(f'Using jinad gateway on {FLOW_HOST_PORT}')

    if ws:
        print(f'reusing workspace id {ws}')

    if jinad == 'remove':
        close_flow(flow_id)
    else:
        if dataset is None:
            raise ValueError('choose --dataset')
        if jinad == 'index':
            publish_flow(f'{dataset}/index.yml', dataset, ws)
        elif jinad == 'query':
            publish_flow(f'{dataset}/query.yml', dataset, ws)


if __name__ == '__main__':
    main()
