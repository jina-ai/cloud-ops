__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import click
import os
import sys

from jina import Document
from jina.flow import Flow

NUM_DOCS = 50
QUERY_NUM_DOCS = 1
TOP_K = 3
BATCH_SIZE = 4
IMG_HEIGHT = 224
IMG_WIDTH = 224


def create_random_img_array(img_height, img_width):
    import numpy as np
    return np.random.randint(0, 256, (img_height, img_width, 3))


def validate_img(resp):
    for d in resp.search.docs:
        assert len(d.matches) == TOP_K, f'Number of actual matches: {len(d.matches)} vs expected number: {TOP_K}'


def random_docs(start, end):
    for idx in range(start, end):
        with Document() as doc:
            doc.id = idx
            doc.content = create_random_img_array(IMG_HEIGHT, IMG_WIDTH)
            doc.mime_type = 'image/png'
        yield doc


def config(indexer_query_type):
    parallel = 1
    shards = 2

    os.environ['JINA_PARALLEL'] = str(parallel)
    os.environ['JINA_SHARDS'] = str(shards)
    os.environ.setdefault('JINA_WORKSPACE', './workspace')
    os.environ.setdefault('JINA_PORT', str(45678))

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


# for index
def index():
    with Flow.load_config('flows/index.yml') as index_flow:
        index_flow.index(input_fn=random_docs(0, NUM_DOCS), batch_size=BATCH_SIZE)


# for search; annoy, faiss, scann with refIndexer
def query():
    with Flow.load_config('flows/query.yml') as search_flow:
        search_flow.search(input_fn=random_docs(0, QUERY_NUM_DOCS), output_fn=validate_img, top_k=TOP_K)


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
