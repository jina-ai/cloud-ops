import os
import time
from enum import Enum
import signal
from random import choice
from string import ascii_lowercase

from .logger import get_logger


def is_aws_cred_set():
    """ Checks if access key id & secret access key env variables set """
    keys = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    return all(len(os.environ.get(k, '')) > 0 for k in keys) 


def file_exists(filepath):
    return os.path.isfile(path=filepath)


def random_text(length):
    return "".join([choice(ascii_lowercase) for i in range(length)])


def read_file_content(filepath):
    if not file_exists(filepath):
        return 
    with open(filepath) as f:
        content = f.read()
    return content

class TimeContext:
    def __init__(self, msg: str):
        self.logger = get_logger(self.__class__.__name__)
        self._msg = msg
        self.duration = 0

    def __enter__(self):
        self.start = time.perf_counter()
        self.logger.info(self._msg + '...')
        return self

    def __exit__(self, typ, value, traceback):
        self.duration = time.perf_counter() - self.start
        self.logger.info(f'{self._msg} took {self.duration:.2f} secs')


class TimeOut:
    """
    Class to handle timeout operations (works on Linux only)
    """
    def __init__(self, seconds=1, message='Timeout'):
        self._seconds = seconds
        self._message = message
        
    def handle(self, signum, frame):
        raise TimeoutError(self._message)
    
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle)
        signal.alarm(self._seconds)
 
    def __exit__(self, type, value, traceback):
        signal.alarm(0)
        

def waiter(func: callable, logger, success_status: list, wait_status: list, failure_status: list,
           time_to_wait: int, time_to_sleep: int = 5, *args, **kwargs):
    """
    waiter function for aws operations that don't have support for default waiter
    Args:
        func (callable): function to invoke that returns `desired_status`
        logger: class logger
        success_status (list): desired status post which call will be success
        wait_status (list): status which will make the waiter sleep
        failure_status (list): status which will make the waiter exit
        time_to_wait (int): total wait time for the operation (seconds)
        time_to_sleep (int): sleep time for the operation (seconds)
    """
    logger.info(f'Success status: {success_status}, Wait status: {wait_status}, ' 
                f'Failure status: {failure_status}')
    with TimeOut(seconds=time_to_wait, 
                 message=f'Waited for {time_to_wait} seconds before timing out!'):
        try:
            while True:
                status = func(*args, **kwargs)
                if status in success_status:
                    logger.info(f'Got successful status `{status}`. Operation completed!')
                    return True
                elif status in failure_status:
                    logger.exception(f'Got status `{status}`. Exiting!')
                    return False
                elif status in wait_status:
                    logger.info(f'Current status: `{status}`. Sleeping for {time_to_sleep} seconds!')
                    time.sleep(time_to_sleep)
                else:
                    logger.info(f'Current status: `{status}`. Sleeping for {time_to_sleep} seconds!')
                    time.sleep(time_to_sleep)
        
        except TimeoutError:
            logger.error(f'Timeout after waiting for {time_to_wait} seconds! Nothing to do!')
            return False
            
        except Exception as exp:
            logger.exception(f'Got the following exception - `{exp}`')
