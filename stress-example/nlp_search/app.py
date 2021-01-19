__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

__version__ = '0.0.1'

import click
import os
import sys

from jina.flow import Flow
from jina import Document

NUM_DOCS = 50
NUM_CHUNKS = 5
QUERY_NUM_DOCS = 1
TOP_K = 3
REQUEST_SIZE = 4
IMG_HEIGHT = 224
IMG_WIDTH = 224


def config(indexer_query_type):
    parallel = 1
    shards = 2

    os.environ['JINA_PARALLEL'] = str(parallel)
    os.environ['JINA_SHARDS'] = str(shards)
    os.environ.setdefault('JINA_WORKSPACE', './workspace')
    os.environ.setdefault('JINA_PORT', str(45678))
    os.environ['JINA_ENCODER_DRIVER_BATCH_SIZE'] = str(16)

    if indexer_query_type == 'faiss':
        os.environ['JINA_USES'] = os.environ.get('JINA_USES_FAISS', 'docker://faiss_indexer_image:test')
        os.environ['JINA_USES_INTERNAL'] = 'pods/faiss_indexer.yml'
    elif indexer_query_type == 'annoy':
        os.environ['JINA_USES'] = os.environ.get('JINA_USES_ANNOY', 'docker://annoy_indexer_image:test')
        os.environ['JINA_USES_INTERNAL'] = 'pods/annoy_indexer.yml'
    elif indexer_query_type == 'scann':
        os.environ['JINA_USES'] = os.environ.get('JINA_USES_SCANN', 'docker://scann_indexer_image:test')
        os.environ['JINA_USES_INTERNAL'] = 'pods/scann_indexer.yml'


def document_generator(num_docs, num_chunks):
    import numpy as np
    chunk_id = num_docs
    for idx in range(num_docs):
        with Document() as doc:
            doc.id = idx
            doc.text = f'I have {idx} cats'
            doc.embedding = np.random.random([9])
            for chunk_idx in range(num_chunks):
                with Document() as chunk:
                    chunk.id = chunk_id
                    chunk.tags['id'] = chunk_idx
                    chunk.text = f'I have {chunk_idx} chunky cats. So long and thanks for all the fish'
                    chunk.embedding = np.random.random([9])
                chunk_id += 1
                doc.chunks.append(chunk)
        yield doc


def validate_text(resp):
    for d in resp.search.docs:
        print(f'Number of actual matches: {len(d.matches)} vs expected number: {TOP_K}')


# for index
def index():
    with Flow.load_config('flows/index.yml') as index_flow:
        index_flow.index(input_fn=document_generator(NUM_DOCS, NUM_CHUNKS), request_size=REQUEST_SIZE)


# for search
def query():
    with Flow.load_config('flows/query.yml') as search_flow:
        search_flow.search(input_fn=document_generator(QUERY_NUM_DOCS, NUM_CHUNKS), output_fn=validate_text,
            top_k=TOP_K)


@click.command()
@click.option('--task', '-t')
@click.option('--indexer-query-type', '-i')
def main(task, indexer_query_type):
    config(indexer_query_type)

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
