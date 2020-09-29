import os
import time
import click

import sys
sys.path.append('..')

from aws.helper import file_exists, random_text, is_aws_cred_set
from aws.logger import get_logger
from aws.excepts import LambdaCreateFailed, LambdaUpdateFailed
from aws.services.lambda_ import Lambda


@click.command()
@click.option('--lambda-name', 
              help='Name of the Lambda function')
@click.option('--description', 
              default='',
              help='Description of the Lambda function')
@click.option('--deployment-zip', 
              default='.',
              help='Deployment package zip to be used with Lambda function')
def trigger(lambda_name, description, deployment_zip):
    logger = get_logger(__name__)
    
    if not is_aws_cred_set():
        logger.error('AWS Creds are not set! Exiting!')
        sys.exit(1)
    
    if not file_exists(filepath=deployment_zip):
        logger.error('Invalid zip file location. Exiting!')
        sys.exit(1)
    
    try:
        with Lambda(name=lambda_name, zip_location=deployment_zip, description=description) as _lambda:
            logger.info(f'Lambda function ARN: `{_lambda.arn}`')
    except LambdaCreateFailed:
        logger.exception(f'Lambda function creation failed!')
        sys.exit(1)
    except LambdaUpdateFailed:
        logger.exception(f'Lambda function update failed!')
        sys.exit(1)


if __name__ == "__main__":
    trigger()
