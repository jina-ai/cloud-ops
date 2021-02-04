import multiprocessing as mp
import os
import random
import time
from datetime import datetime
from typing import Generator, Callable

import click
import numpy as np
from jina import Client, Document
from jina.parsers import set_client_cli_parser

DEFAULT_NUM_DOCS = 500
TOP_K = 3
REQUEST_SIZE = 4
IMG_HEIGHT = 224
IMG_WIDTH = 224

FLOW_HOST = os.environ.get('FLOW_HOST')
FLOW_PORT_GRPC = os.environ.get('FLOW_PORT_GRPC')

if FLOW_HOST is None or FLOW_PORT_GRPC is None:
    raise ValueError(
        f'Make sure you set both FLOW_HOST and FLOW_PORT_GRPC. \
        Current FLOW_HOST = {FLOW_HOST}; FLOW_PORT_GRPC = {FLOW_PORT_GRPC}')


def create_random_img_array(img_height, img_width):
    return np.random.randint(0, 256, (img_height, img_width, 3))


def validate_img(resp):
    for d in resp.search.docs:
        if len(d.matches) != TOP_K:
            print(f' MATCHES LENGTH IS NOT TOP_K but {len(d.matches)}')
        for m in d.matches:
            if 'filename' not in m.tags.keys():
                print(f'filename not in tags: {m.tags}')
            # to test that the data from the KV store is retrieved
            if 'image ' not in m.tags['filename']:
                print(f'"image" not in m.tags["filename"]: {m.tags["filename"]}')
        # assert len(d.matches) == TOP_K, f'Number of actual matches: {len(d.matches)} vs expected number: {TOP_K}'


def random_docs(end, start=0):
    for idx in range(start, end + start):
        with Document() as doc:
            doc.id = idx
            doc.content = create_random_img_array(IMG_HEIGHT, IMG_WIDTH)
            doc.mime_type = 'image/png'
            doc.tags['filename'] = f'image {idx}'
        yield doc


ClientFunction = Callable[[Client, Callable[[int], Generator], int, str, int], None]


def wrapper(
        args,
        docs_gen_func: Callable[[int], Generator],
        id,
        function: ClientFunction,
        time_end: int,
        req_size: int,
        dataset: str,
        nr_docs: int
):
    client = Client(args)
    while True:
        # add counter for docs and log to file {id}
        print(
            f'Process {id}: Running function {function.__name__} with {nr_docs} docs via {docs_gen_func.__name__}...')
        client.check_input(docs_gen_func(nr_docs))
        function(client, docs_gen_func, req_size, dataset, nr_docs)
        if time.time() >= time_end:
            print(f'Process {id}: end reached')
            # close Process
            # log to file {function.__name__} - {id}
            return


def index_done(resp):
    print(f'done with indexing...')
    print(f'len of resp = {len(resp.index.docs)}')


def index(client: Client, docs_gen_func: Callable[[int], Generator], req_size: int, dataset: str, nr_docs: int):
    on_done = index_done
    if dataset == 'text':
        # TODO maybe specific validation?
        pass
    client.index(docs_gen_func(nr_docs), request_size=req_size, on_done=on_done)


def validate_text(resp):
    print(f'got {len(resp.search.docs)} docs in resp.search')
    for d in resp.search.docs:
        for m in d.matches:
            # to test that the data from the KV store is retrieved
            assert 'filename' in m.tags.keys()
        assert len(d.matches) == TOP_K, f'Number of actual matches: {len(d.matches)} vs expected number: {TOP_K}'


def query(client: Client, docs_gen_func: Callable[[int], Generator], req_size: int, dataset: str, nr_docs: int):
    print(f' heeey query')
    on_done = validate_img
    if dataset == 'text':
        on_done = validate_text
    client.search(docs_gen_func(nr_docs), on_done=on_done, top_k=TOP_K, request_size=req_size)


def document_generator(num_docs):
    chunk_id = num_docs
    for idx in range(num_docs):
        with Document() as doc:
            doc.id = idx
            length = random.randint(5, 30)
            doc.text = 'some text'
            doc.tags['filename'] = f'filename {idx}'
            num_chunks = random.randint(1, 10)
            for chunk_idx in range(num_chunks):
                with Document() as chunk:
                    chunk.id = chunk_id
                    chunk.tags['id'] = chunk_idx
                    length = random.randint(5, 30)
                    chunk.text = 'some more text'
                chunk_id += 1
                doc.chunks.append(chunk)
        yield doc


def get_dataset_docs_gens(dataset) -> Callable[[int], Generator]:
    if dataset == 'image':
        return random_docs

    elif dataset == 'text':
        return document_generator


@click.command()
@click.option('--task', '-t')
@click.option('--load', '-l', default=60)  # time (seconds)
@click.option('--nr', '-n', default=DEFAULT_NUM_DOCS)
@click.option('--concurrency', '-c', default=1)
@click.option('--req_size', '-r', default=REQUEST_SIZE)
@click.option('--dataset', default=None, type=click.Choice(['image', 'text']))
def main(task, load, nr, concurrency, req_size, dataset):
    print(f'task = {task}; load = {load}; nr = {nr}; concurrency = {concurrency}; \
req_size = {req_size}; dataset = {dataset}')
    print(f'connecting to gRPC gateway at {FLOW_HOST}:{FLOW_PORT_GRPC}')
    if task not in ['index', 'query']:
        raise NotImplementedError(
            f'unknown task: {task}. A valid task is either `index` or `query`.')

    function = index
    if task == 'query':
        function = query

    grpc_args = set_client_cli_parser().parse_args(
        ['--host', FLOW_HOST, '--port-expose', str(FLOW_PORT_GRPC)])

    time_end = time.time() + load
    print(f'Will end at {datetime.fromtimestamp(time_end).isoformat()}')

    docs_generator = get_dataset_docs_gens(dataset)

    if concurrency == 1:
        print(f'Starting only one process. Not using multiprocessing...')
        wrapper(grpc_args, docs_generator, 1, function, time_end, req_size, dataset, nr)
    else:
        print(f'Using multiprocessing to start {concurrency} processes...')
        processes = [
            mp.Process(
                target=wrapper,
                args=(grpc_args, docs_generator, id, function, time_end, req_size, dataset, nr),
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

    # glob process logs file and sum the total processed
    # by indexing and querying


if __name__ == '__main__':
    import nltk

    nltk.download('words')
    main()
