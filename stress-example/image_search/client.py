import click
from jina import Client, Document
from jina.parsers import set_client_cli_parser

NUM_DOCS = 500
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
        for m in d.matches:
            assert 'filename' in m.tags.keys()
            # to test that the data from the KV store is retrieved
            assert 'image ' in m.tags['filename']
        assert len(d.matches) == TOP_K, f'Number of actual matches: {len(d.matches)} vs expected number: {TOP_K}'


def random_docs(start, end):
    for idx in range(start, end):
        with Document() as doc:
            doc.id = idx
            doc.content = create_random_img_array(IMG_HEIGHT, IMG_WIDTH)
            doc.mime_type = 'image/png'
            doc.tags['filename'] = f'image {idx}'
        yield doc


docs_index = random_docs(0, NUM_DOCS)
docs_query = random_docs(0, QUERY_NUM_DOCS)


def index(port):
    # TODO get hostname and port programatically
    host = '0.0.0.0'
    args = set_client_cli_parser().parse_args(
        ['--host', host, '--port-expose', str(port)])
    grpc_client = Client(args)
    grpc_client.index(docs_index)


def query(port):
    # TODO get hostname and port programatically
    host = '0.0.0.0'
    args = set_client_cli_parser().parse_args(
        ['--host', host, '--port-expose', str(port)])
    grpc_client = Client(args)
    grpc_client.search(input_fn=docs_query, on_done=validate_img, top_k=TOP_K)


@click.command()
@click.option('--task', '-t')
@click.option('--port', '-p')
def main(task, port):
    if task == 'index':
        index(port)
    elif task == 'query':
        query(port)
    else:
        raise NotImplementedError(
            f'unknown task: {task}. A valid task is either `index` or `query`.')


if __name__ == '__main__':
    main()
