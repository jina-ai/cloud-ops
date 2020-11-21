from typing import Any

import numpy as np

from jina.executors.encoders import BaseEncoder


class MWUEncoder(BaseEncoder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> Any:
        self.logger.info(f'enter MWUEncoder with input shape {data.shape}')
        return np.random.random([data.shape[0], 3])
