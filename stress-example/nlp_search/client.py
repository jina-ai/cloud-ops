import multiprocessing as mp
import time
from datetime import datetime

import click
from jina import Client, Document
from jina.parsers import set_client_cli_parser

DEFAULT_NUM_DOCS = 500
REQUEST_SIZE = 4
TOP_K = 3
HOST = '0.0.0.0'


def document_generator(num_docs):
    import numpy as np
    import random
    chunk_id = num_docs
    for idx in range(num_docs):
        with Document() as doc:
            doc.id = idx
            doc.text = f'I have {idx} cats'
            doc.embedding = np.random.random([9])
            doc.tags['filename'] = f'filename {idx}'
            num_chunks = random.randint(1, 10)
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
    print(f'got {len(resp.search.docs)} docs in resp.search')
    for d in resp.search.docs:
        for m in d.matches:
            # to test that the data from the KV store is retrieved
            assert 'filename' in m.tags.keys()
        assert len(d.matches) == TOP_K, f'Number of actual matches: {len(d.matches)} vs expected number: {TOP_K}'


def wrapper(args, docs, id, function, time_end, req_size):
    client = Client(args)
    print(f'Process {id}: Running function {function.__name__} with {len(docs)} docs...')
    while True:
        client.check_input(docs)
        function(client, docs, req_size)
        if time.time() >= time_end:
            print(f'Process {id}: end reached')
            # close Process
            return


def index(client, docs, req_size):
    client.index(docs, request_size=req_size)


def query(client, docs, req_size):
    client.search(input_fn=docs, on_done=validate_text, top_k=TOP_K, request_size=req_size)


@click.command()
@click.option('--task', '-t')
@click.option('--port', '-p', default=45678)
@click.option('--load', '-l', default=60)  # time (seconds)
@click.option('--nr', '-n', default=DEFAULT_NUM_DOCS)
@click.option('--concurrency', '-c', default=1)
@click.option('--req_size', '-r', default=REQUEST_SIZE)
def main(task, port, load, nr, concurrency, req_size):
    print(f'task = {task}; port = {port}; load = {load}; nr = {nr}; concurrency = {concurrency}')
    if task not in ['index', 'query']:
        raise NotImplementedError(
            f'unknown task: {task}. A valid task is either `index` or `query`.')

    function = index
    if task == 'query':
        function = query

    args = set_client_cli_parser().parse_args(
        ['--host', HOST, '--port-expose', str(port)])

    time_end = time.time() + load
    print(f'Will end at {datetime.fromtimestamp(time_end).isoformat()}')

    # needs to be a list otherwise it gets exhausted
    docs = list(document_generator(nr))
    # FIXME(cristianmtr): remote clients?
    processes = [
        mp.Process(
            target=wrapper,
            args=(args, docs, id, function, time_end, req_size),
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
