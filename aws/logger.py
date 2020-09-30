import os
import sys
import logging
from datetime import datetime


class LengthFilter(logging.Filter):
    def filter(self, record):
        record.file_func_lineno = f'{record.filename}:{record.funcName}():L{record.lineno}' 
        return True

def default_formatter():
    _fmt = '%(asctime)s | %(levelname)8s | %(file_func_lineno)42s | %(message)s'
    _datefmt = '%b %d %H:%M:%S'
    return logging.Formatter(fmt=_fmt, datefmt=_datefmt)

def _console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(default_formatter())
    return console_handler

def _file_handler():
    file_handler = logging.FileHandler(
        filename=datetime.now().strftime('_logs/cloud_trigger_%b_%d_%m_%Y.log'))
    file_handler.setFormatter(default_formatter())
    return file_handler

def get_logger(context='generic', file=True):
    logger = logging.getLogger(context)
    logger.addFilter(filter=LengthFilter())
    logger.propagate = False
    logger.addHandler(_console_handler())
    logger.setLevel(logging.DEBUG)
    if file:
        os.makedirs('_logs', exist_ok=1)
        logger.addHandler(_file_handler())
    return logger
