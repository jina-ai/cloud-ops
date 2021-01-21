import multiprocessing as mp
import time
from datetime import datetime

import click
from jina import Client, Document
from jina.parsers import set_client_cli_parser
from websocket import warning

DEFAULT_NUM_DOCS = 500
QUERY_NUM_DOCS = 1
TOP_K = 3
BATCH_SIZE = 4
IMG_HEIGHT = 224
IMG_WIDTH = 224
HOST = '0.0.0.0'


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
    for idx in range(start, end + start):
        with Document() as doc:
            doc.id = idx
            doc.content = create_random_img_array(IMG_HEIGHT, IMG_WIDTH)
            doc.mime_type = 'image/png'
            doc.tags['filename'] = f'image {idx}'
        yield doc


def wrapper(client, docs, id, function, time_end):
    print(f'Process {id}: Running function {function.__name__} with {len(docs)} docs...')
    while True:
        client.check_input(docs)
        function(client, docs)
        if time.time() >= time_end:
            print(f'Process {id}: end reached')
            # close Process
            return


def index(client, docs):
    client.index(docs)


def query(client, docs):
    client.search(input_fn=docs, on_done=validate_img, top_k=TOP_K)


@click.command()
@click.option('--task', '-t')
@click.option('--port', '-p')
@click.option('--load', '-l', default=60)  # time (seconds)
@click.option('--nr', '-n', default=DEFAULT_NUM_DOCS)
@click.option('--concurrency', '-c', default=1)
def main(task, port, load, nr, concurrency):
    print(f'task = {task}; port = {port}; load = {load}; nr = {nr}; concurrency = {concurrency}')
    if task not in ['index', 'query']:
        raise NotImplementedError(
            f'unknown task: {task}. A valid task is either `index` or `query`.')

    function = index
    if task == 'query':
        function = query

    args = set_client_cli_parser().parse_args(
        ['--host', HOST, '--port-expose', str(port)])
    grpc_client = Client(args)

    time_end = time.time() + load
    print(f'Will end at {datetime.fromtimestamp(time_end).isoformat()}')

    # needs to be a list otherwise it gets exhausted
    docs = list(random_docs(0, nr))
    # FIXME(cristianmtr): remote clients?
    processes = [
        mp.Process(
            target=wrapper,
            args=(grpc_client, docs, id, function, time_end),
            name=f'{str(function)}-{id}'
        )
        for id in range(concurrency)
    ]
    for p in processes:
        p.start()

    wait_secs = time_end - time.time()
    if wait_secs > 0:
        time.sleep(wait_secs)

    for p in processes:
        if p.is_alive():
            print(f'Process {p.name} is still alive. Will wait...')
            p.join()


if __name__ == '__main__':
    main()
