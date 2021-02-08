from jina.flow import Flow
from jina import Document
import numpy as np


def index_docs():
    for i in range(0, 100):
        d = Document()
        d.embedding = np.array([i, i])
        d.tags['filename'] = f' hey here {i}'
        yield d


def query_docs():
    for i in range(0, 5):
        d = Document()
        d.embedding = np.array([i, i])
        d.tags['filename'] = f' hey here {i}'
        yield d


def read_tags(resp):
    for doc in resp.search.docs:
        for match in doc.matches:
            print(f' match {match.tags}')


with Flow.load_config('index.yml') as f:
    f.index(input_fn=index_docs())


with Flow.load_config('query.yml') as f:
    f.search(input_fn=query_docs(), on_done=read_tags)