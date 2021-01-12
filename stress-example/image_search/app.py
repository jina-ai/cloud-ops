__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import sys

from jina import Document
from jina.flow import Flow

num_docs = 50


def create_random_img_array(img_height, img_width):
    import numpy as np
    return np.random.randint(0, 256, (img_height, img_width, 3))


def random_docs():
    for idx in range(0, num_docs):
        with Document() as doc:
            doc.id = idx
            doc.blob = create_random_img_array(25, 25)
            doc.mime_type = 'image/png'
        yield doc


def config():
    parallel = 1 if sys.argv[1] == 'index' else 1
    shards = 1

    os.environ.setdefault('JINA_PARALLEL', str(parallel))
    os.environ.setdefault('JINA_SHARDS', str(shards))
    os.environ.setdefault('JINA_WORKSPACE', './workspace')
    os.environ.setdefault('JINA_PORT', str(45678))


# for index
def index():
    with Flow.load_config('flows/index.yml') as index_flow:
        index_flow.index(input_fn=random_docs())


# for search; annoy, faiss, scann with refIndexer
def query():
    with Flow.load_config('flows/query.yml') as search_flow:
        search_flow.block()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('choose between "index" and "search" mode')
        exit(1)
    if sys.argv[1] == 'index':
        config()
        workspace = os.environ['JINA_WORKSPACE']
        if os.path.exists(workspace):
            print(f'\n +---------------------------------------------------------------------------------+ \
                    \n |                                   🤖🤖🤖                                        | \
                    \n | The directory {workspace} already exists. Please remove it before indexing again. | \
                    \n |                                   🤖🤖🤖                                        | \
                    \n +---------------------------------------------------------------------------------+')
        index()
    elif sys.argv[1] == 'query':
        config()
        query()
    else:
        raise NotImplementedError(f'unsupported mode {sys.argv[1]}')
