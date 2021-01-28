import multiprocessing as mp
import time
from datetime import datetime

import click
from jina import Client, Document
from jina.parsers import set_client_cli_parser

DEFAULT_NUM_DOCS = 500
TOP_K = 3
REQUEST_SIZE = 4
IMG_HEIGHT = 224
IMG_WIDTH = 224


def create_random_img_array(img_height, img_width):
    import numpy as np
    return np.random.randint(0, 256, (img_height, img_width, 3))


def validate_img(resp):
    for d in resp.search.docs:
        if len(d.matches) != TOP_K:
            print(f' MATCHES LENGTH IS NOT TOP_K but {len(d.matches)}')
        for m in d.matches:
            print(f' match {m.id}')
            assert 'filename' in m.tags.keys()
            # to test that the data from the KV store is retrieved
            assert 'image ' in m.tags['filename']
        #assert len(d.matches) == TOP_K, f'Number of actual matches: {len(d.matches)} vs expected number: {TOP_K}'


def random_docs(start, end):
    for idx in range(start, end + start):
        with Document() as doc:
            doc.id = idx
            doc.content = create_random_img_array(IMG_HEIGHT, IMG_WIDTH)
            doc.mime_type = 'image/png'
            doc.tags['filename'] = f'image {idx}'
        yield doc


def wrapper(args, docs, id, function, time_end, req_size):
    client = Client(args)
    while True:
        print(f'Process {id}: Running function {function.__name__} with {len(docs)} docs...')
        client.check_input(docs)
        function(client, docs, req_size)
        if time.time() >= time_end:
            print(f'Process {id}: end reached')
            # close Process
            return


def index_done(resp):
    print(f'done with indexing...')
    print(f'len of resp = {len(resp.index.docs)}')


def index(client, docs, req_size):
    print('indexing!!!')
    client.index(docs, request_size=req_size, on_done=index_done)


def query(client, docs, req_size):
    print(f' heeey query')
    client.search(input_fn=docs, on_done=validate_img, top_k=TOP_K, request_size=req_size)


@click.command()
@click.option('--task', '-t')
@click.option('--host', '-h', default='0.0.0.0')
@click.option('--port', '-p', default=45678)
@click.option('--load', '-l', default=60)  # time (seconds)
@click.option('--nr', '-n', default=DEFAULT_NUM_DOCS)
@click.option('--concurrency', '-c', default=1)
@click.option('--req_size', '-r', default=REQUEST_SIZE)
def main(task, host, port, load, nr, concurrency, req_size):
    print(f'task = {task}; port = {port}; load = {load}; nr = {nr}; concurrency = {concurrency}')
    if task not in ['index', 'query']:
        raise NotImplementedError(
            f'unknown task: {task}. A valid task is either `index` or `query`.')

    function = index
    if task == 'query':
        function = query

    args = set_client_cli_parser().parse_args(
        ['--host', host, '--port-expose', str(port)])

    time_end = time.time() + load
    print(f'Will end at {datetime.fromtimestamp(time_end).isoformat()}')

    # needs to be a list otherwise it gets exhausted
    docs = list(random_docs(0, nr))
    # FIXME(cristianmtr): remote clients?
    if concurrency == 1:
        print(f'Starting only one process. Not using multiprocessing...')
        wrapper(args, docs, 1, function, time_end, req_size)
    else:
        print(f'Using multiprocessing to start {concurrency} processes...')
        processes = [
            mp.Process(
                target=wrapper,
                args=(),
                name=f'{function.__name__}-{id}'
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
