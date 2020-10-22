from ..client import AWSClientWrapper
from ..helper import file_exists
from ..logger import get_logger


class S3:
    """Wrapper around boto3 to upload to S3 bucket
    """

    def __init__(self, bucket: str):
        self.logger = get_logger(context=self.__class__.__name__)
        self._client_wrapper = AWSClientWrapper(service='s3')
        self._client = self._client_wrapper.client
        self._bucket = bucket

    def put(self, filepath, key):
        if not file_exists(filepath):
            self.logger.error(f'File {filepath} doesn\'t exist! Nothing to upload!')
            return
        try:
            self.logger.info(f'Uploading object from `{filepath}` to S3 bucket `{self._bucket}` key `{key}`')
            with open(filepath, 'rb') as data:
                self._client.upload_fileobj(data, self._bucket, key)
        except Exception as exp:
            self.logger.error(f'Got following exception while uploading object to S3 \n{exp}')
