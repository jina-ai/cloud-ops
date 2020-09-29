import os
import time
import click

import sys
sys.path.append('..')

from aws.helper import file_exists, read_file_content, random_text, is_aws_cred_set
from aws.logger import get_logger
from aws.excepts import LambdaCreateFailed, LambdaUpdateFailed, StackCreationFailed, StackUpdateFailed
from aws.services.lambda_ import Lambda
from aws.services.cloudformation import CFNStack


@click.command()
@click.option('--lambda-name', 
              help='Name of the Lambda function')
@click.option('--lambda-description', 
              default='',
              help='Description of the Lambda function')
@click.option('--deployment-zip', 
              default='.',
              help='Deployment package zip to be used with Lambda function')
@click.option('--stack_name',
              default='jinahub-api-stack',
              help='Name of the CFN Stack')
@click.option('--template',
              default='cloud_ymls/cfn-api-gateway.yml',
              help='CFN Template to be used for deployment (Default - cloud_ymls/cfn-api-gateway.yml)')
@click.option('--stage',
              default='dev',
              help='Deployment stage for API Gateway (Default - dev)')
def trigger(lambda_name, lambda_description, deployment_zip, stack_name, template, stage):
    logger = get_logger(__name__)
    
    if not is_aws_cred_set():
        logger.error('AWS Creds are not set! Exiting!')
        sys.exit(1)
    
    if not file_exists(filepath=deployment_zip):
        logger.error('Invalid zip file location. Exiting!')
        sys.exit(1)
    
    if not file_exists(filepath=template):
        logger.error('Invalid cfn yaml. Exiting!')
        sys.exit(1)
        
    cfn_yml = read_file_content(filepath=template)
        
    try:
        with Lambda(name=lambda_name, zip_location=deployment_zip, 
                    handler='lambda_function.lambda_handler', description=lambda_description) as _lambda:
            logger.info(f'Lambda function ARN: `{_lambda.arn}`')
    except LambdaCreateFailed:
        logger.exception(f'Lambda function creation failed!')
        sys.exit(1)
    except LambdaUpdateFailed:
        logger.exception(f'Lambda function update failed!')
        sys.exit(1)
    
    parameters = [
        {'ParameterKey': 'DeploymentStage', 'ParameterValue': stage},
        {'ParameterKey': 'HubListLambdaArn', 'ParameterValue': _lambda.arn},
        {'ParameterKey': 'HubPushLambdaArn', 'ParameterValue': _lambda.arn}
    ]
    
    try:
        with CFNStack(name=stack_name, template=cfn_yml, 
                      parameters=parameters, delete_at_exit=False) as api_cfn_stack:
            logger.info('Resources description --')
            for resource in api_cfn_stack.resources:
                logger.info(f'Name: `{resource["LogicalResourceId"]}`\t\tType: `{resource["ResourceType"]}`\t'
                            f'ID: `{resource["PhysicalResourceId"]}`')
    except (StackCreationFailed, StackUpdateFailed) as cfn_exp:
        logger.exception(f'Stack creation/update failed. Exiting context \n{cfn_exp}')
        sys.exit(1)


if __name__ == "__main__":
    trigger()
