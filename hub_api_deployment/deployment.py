import os
import sys

import click

sys.path.append('..')

from aws.helper import file_exists, read_file_content, is_aws_cred_set, is_db_envs_set
from aws.logger import get_logger
from aws.excepts import StackCreationFailed, StackUpdateFailed
from aws.services.s3 import S3
from aws.services.cloudformation import CFNStack


@click.command()
@click.option('--list-deployment-zip',
              help='Deployment package zip to be used with HubList Lambda function')
@click.option('--push-deployment-zip',
              help='Deployment package zip to be used with HubPush Lambda function')
@click.option('--authorize-deployment-zip',
              help='Deployment package zip to be used with HubPush Lambda function')
@click.option('--key-id',
              help='Enter folder to be created in S3 (will take PR# in GH Action)')
@click.option('--stack-name',
              default='jinahub-api-stack2',
              help='Name of the CFN Stack (Defaults to jinahub-api-stack2)')
@click.option('--template',
              default='cloud_ymls/cfn-api-gateway.yml',
              help='CFN Template to be used for deployment (Default - cloud_ymls/cfn-api-gateway.yml)')
@click.option('--deployment-stage',
              default='dev',
              help='Deployment stage for API Gateway (Default - dev)')
def trigger(list_deployment_zip, push_deployment_zip, authorize_deployment_zip, key_id,
            stack_name, template, deployment_stage):
    logger = get_logger(__name__)

    if not is_aws_cred_set():
        logger.error('AWS Creds are not set! Exiting!')
        sys.exit(1)

    if not is_db_envs_set():
        logger.error('MongoDB environment vars needed for lambda functions are not set! Exiting!')
        sys.exit(1)

    if not file_exists(filepath=list_deployment_zip) and not file_exists(filepath=push_deployment_zip):
        logger.error('Both zip file locations are invalid. Exiting!')
        sys.exit(1)

    if not file_exists(filepath=template):
        logger.error('Invalid cfn yaml. Exiting!')
        sys.exit(1)

    S3_DEFAULT_BUCKET = 'lambda-handlers-jina'
    s3 = S3(bucket=S3_DEFAULT_BUCKET)

    if list_deployment_zip is not None:
        zip_filename = os.path.basename(list_deployment_zip)
        s3_list_key = f'hubapi_list/{key_id}/{zip_filename}'
        s3.put(filepath=list_deployment_zip,
               key=s3_list_key)

    if push_deployment_zip is not None:
        zip_filename = os.path.basename(list_deployment_zip)
        s3_push_key = f'hubapi_push/{key_id}/{zip_filename}'
        s3.put(filepath=push_deployment_zip,
               key=s3_push_key)

    if push_deployment_zip is not None:
        zip_filename = os.path.basename(list_deployment_zip)
        s3_authorize_key = f'hubapi_authorize/{key_id}/{zip_filename}'
        s3.put(filepath=authorize_deployment_zip,
               key=s3_authorize_key)

    cfn_yml = read_file_content(filepath=template)

    parameters = [
        {'ParameterKey': 'DefS3Bucket', 'ParameterValue': S3_DEFAULT_BUCKET},
        {'ParameterKey': 'HubListLambdaFnS3Key', 'ParameterValue': s3_list_key},
        {'ParameterKey': 'HubPushLambdaFnS3Key', 'ParameterValue': s3_push_key},
        {'ParameterKey': 'HubAPIAuthorizeLambdaFnS3Key', 'ParameterValue': s3_authorize_key},
        {'ParameterKey': 'DefLambdaRole', 'ParameterValue': 'arn:aws:iam::416454113568:role/lambda-role'},
        {'ParameterKey': 'DeploymentStage', 'ParameterValue': deployment_stage},
        {'ParameterKey': 'JinaDBHostname', 'ParameterValue': os.environ['JINA_DB_HOSTNAME']},
        {'ParameterKey': 'JinaDBCollection', 'ParameterValue': os.environ['JINA_DB_COLLECTION']},
        {'ParameterKey': 'JinaDBName', 'ParameterValue': os.environ['JINA_DB_NAME']},
        {'ParameterKey': 'JinaDBUsername', 'ParameterValue': os.environ['JINA_DB_USERNAME']},
        {'ParameterKey': 'JinaDBPassword', 'ParameterValue': os.environ['JINA_DB_PASSWORD']}
    ]

    try:
        with CFNStack(name=stack_name, template=cfn_yml,
                      parameters=parameters, delete_at_exit=False) as api_cfn_stack:
            if not api_cfn_stack.exists:
                logger.error(f'Stack creation/update failed. Exiting context \n')
                sys.exit(1)
            logger.info('Resources description --')
            for resource in api_cfn_stack.resources:
                logger.info(f'Name: `{resource["LogicalResourceId"]}`\t\tType: `{resource["ResourceType"]}`\t'
                            f'ID: `{resource["PhysicalResourceId"]}`')
    except (StackCreationFailed, StackUpdateFailed) as cfn_exp:
        logger.exception(f'Stack creation/update failed. Exiting context \n{cfn_exp}')
        sys.exit(1)


if __name__ == "__main__":
    trigger()
