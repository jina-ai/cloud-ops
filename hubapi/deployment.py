import os
import sys
import base64

import click

sys.path.append('..')

from aws.helper import file_exists, read_file_content, is_aws_cred_set, is_db_envs_set
from aws.logger import get_logger
from aws.excepts import StackCreationFailed, StackUpdateFailed
from aws.services.s3 import S3
from aws.services.cloudformation import CFNStack


def str_to_ascii_to_base64_to_str(text):
    return base64.b64encode(text.encode('ascii')).decode('ascii')


def read_environment():
    hostname = str_to_ascii_to_base64_to_str(os.environ.get('JINA_DB_HOSTNAME'))
    username = str_to_ascii_to_base64_to_str(os.environ.get('JINA_DB_USERNAME'))
    password = str_to_ascii_to_base64_to_str(os.environ.get('JINA_DB_PASSWORD'))
    database_name = str_to_ascii_to_base64_to_str(os.environ.get('JINA_DB_NAME'))
    hubpod_collection = str_to_ascii_to_base64_to_str(os.environ.get('JINA_HUBPOD_COLLECTION'))
    metadata_collection = str_to_ascii_to_base64_to_str(os.environ.get('JINA_METADATA_COLLECTION'))
    docker_username = str_to_ascii_to_base64_to_str(os.environ.get('JINA_DOCKER_USERNAME'))
    docker_password = str_to_ascii_to_base64_to_str(os.environ.get('JINA_DOCKER_PASSWORD'))
    return hostname, username, password, database_name, hubpod_collection, \
        metadata_collection, docker_username, docker_password


@click.command()
@click.option('--list-deployment-zip',
              help='Deployment package zip to be used with HubList Lambda function')
@click.option('--push-deployment-zip',
              help='Deployment package zip to be used with HubPush Lambda function')
@click.option('--authorize-deployment-zip',
              help='Deployment package zip to be used with HubPush Lambda function')
@click.option('--docker-cred-deployment-zip',
              help='Deployment package zip to be used with DockerCredFetcher Lambda function')
@click.option('--key-id',
              help='Enter folder to be created in S3 (will take PR# in GH Action)')
@click.option('--stack-name',
              default='jinahub-api-stack2',
              help='Name of the CFN Stack (Defaults to jinahub-api-stack2)')
@click.option('--template',
              default='cloud_ymls/apigateway.yml',
              help='CFN Template to be used for deployment (Default - cloud_ymls/apigateway.yml)')
@click.option('--deployment-stage',
              default='dev',
              help='Deployment stage for API Gateway (Default - dev)')
def trigger(list_deployment_zip, push_deployment_zip, authorize_deployment_zip, docker_cred_deployment_zip, key_id,
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
        zip_filename = os.path.basename(push_deployment_zip)
        s3_push_key = f'hubapi_push/{key_id}/{zip_filename}'
        s3.put(filepath=push_deployment_zip,
               key=s3_push_key)

    if authorize_deployment_zip is not None:
        zip_filename = os.path.basename(authorize_deployment_zip)
        s3_authorize_key = f'hubapi_authorize/{key_id}/{zip_filename}'
        s3.put(filepath=authorize_deployment_zip,
               key=s3_authorize_key)

    if docker_cred_deployment_zip is not None:
        zip_filename = os.path.basename(docker_cred_deployment_zip)
        s3_docker_cred_key = f'docker_auth/{key_id}/{zip_filename}'
        s3.put(filepath=docker_cred_deployment_zip,
               key=s3_docker_cred_key)

    cfn_yml = read_file_content(filepath=template)

    hostname, username, password, database_name, hubpod_collection, metadata_collection, \
        docker_username, docker_password = read_environment()

    parameters = [
        {'ParameterKey': 'DefS3Bucket', 'ParameterValue': S3_DEFAULT_BUCKET},
        {'ParameterKey': 'HubListLambdaFnS3Key', 'ParameterValue': s3_list_key},
        {'ParameterKey': 'HubPushLambdaFnS3Key', 'ParameterValue': s3_push_key},
        {'ParameterKey': 'HubAPIAuthorizeLambdaFnS3Key', 'ParameterValue': s3_authorize_key},
        {'ParameterKey': 'DockerCredFetcherLambdaFnS3Key', 'ParameterValue': s3_docker_cred_key},
        {'ParameterKey': 'DefLambdaRole', 'ParameterValue': 'arn:aws:iam::416454113568:role/lambda-role'},
        {'ParameterKey': 'DeploymentStage', 'ParameterValue': deployment_stage},
        {'ParameterKey': 'JinaDBHostname', 'ParameterValue': hostname},
        {'ParameterKey': 'JinaDBUsername', 'ParameterValue': username},
        {'ParameterKey': 'JinaDBPassword', 'ParameterValue': password},
        {'ParameterKey': 'JinaHubpodCollection', 'ParameterValue': hubpod_collection},
        {'ParameterKey': 'JinaMetadataCollection', 'ParameterValue': metadata_collection},
        {'ParameterKey': 'JinaDBName', 'ParameterValue': database_name},
        {'ParameterKey': 'JinaDockerUsername', 'ParameterValue': docker_username},
        {'ParameterKey': 'JinaDockerPassword', 'ParameterValue': docker_password}
    ]

    try:
        with CFNStack(name=stack_name, template=cfn_yml,
                      parameters=parameters, delete_at_exit=False) as api_cfn_stack:
            if not api_cfn_stack.exists:
                logger.error(f'Stack creation/update failed. Exiting context \n')
                sys.exit(1)
            logger.info('Resources description -- ')
            for resource in api_cfn_stack.resources:
                logger.info(f'Name: `{resource["LogicalResourceId"]}`\t\tType: `{resource["ResourceType"]}`\t'
                            f'ID: `{resource["PhysicalResourceId"]}`')
    except (StackCreationFailed, StackUpdateFailed) as cfn_exp:
        logger.exception(f'Stack creation/update failed. Exiting context \n{cfn_exp}')
        sys.exit(1)


if __name__ == "__main__":
    trigger()
