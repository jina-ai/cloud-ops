__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import sys

import click
from jina.flow import Flow

# TODO make it available to the client
JINA_PORT = 45678


def config(task, indexer_query_type):
    # TODO make these configurable
    shards_encoder = 1
    shards_indexers = 2

    os.environ['JINA_SHARDS_ENCODER'] = str(shards_encoder)
    os.environ['JINA_SHARDS_INDEXERS'] = str(shards_indexers)
    os.environ.setdefault('JINA_WORKSPACE', './workspace')
    os.environ.setdefault('JINA_PORT', str(JINA_PORT))

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


@click.command()
@click.option('--task', '-t')
@click.option('--indexer-query-type', '-i')
def main(task, indexer_query_type):
    config(task, indexer_query_type)
    if task == 'index':
        workspace = os.environ['JINA_WORKSPACE']
        if os.path.exists(workspace):
            print(f'\n +---------------------------------------------------------------------------------+ \
                    \n |                                   🤖🤖🤖                                        | \
                    \n | The directory {workspace} already exists. Please remove it before indexing again. | \
                    \n |                                   🤖🤖🤖                                        | \
                    \n +---------------------------------------------------------------------------------+')
            sys.exit()
        index()
    elif task == 'query':
        query()
    else:
        raise NotImplementedError(
            f'unknown task: {task}. A valid task is either `index` or `query`.')


if __name__ == '__main__':
    main()
