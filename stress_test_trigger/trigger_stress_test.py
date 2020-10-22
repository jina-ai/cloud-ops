import sys

import click

sys.path.append('..')

from aws.helper import file_exists, read_file_content, random_text, is_aws_cred_set
from aws.logger import get_logger
from aws.excepts import StackCreationFailed, StackUpdateFailed, SSMDocumentCreationFailed

from aws.services.cloudformation import CFNStack
from aws.services.ssm import SSMDocument


@click.command()
@click.option('--cfn',
              default='cloud_ymls/cfn-stress-test.yml',
              help='CFN Stack to be used for deployment (Default - cloud_ymls/cfn-stress-test.yml)')
@click.option('--ssm',
              default='cloud_ymls/ssm-stress-test.yml',
              help='SSM Document to be used for command exec (Default - cloud_ymls/ssm-stress-test.yml)')
def trigger(cfn, ssm):
    logger = get_logger(__name__)

    if not is_aws_cred_set():
        logger.error('AWS Creds are not set! Exiting!')
        sys.exit(1)

    if not file_exists(filepath=cfn) or not file_exists(filepath=ssm):
        logger.error('Invalid cfn yaml or ssm yaml. Exiting!')
        sys.exit(1)

    cfn_yml = read_file_content(filepath=cfn)
    ssm_yml = read_file_content(filepath=ssm)

    _random_text = random_text(7)
    s3_bucket_name = 'stress-test-jina'
    stack_name = f'stress-test-stack-{_random_text}'
    ssm_doc_name = f'stress-test-ssm-{_random_text}'

    try:
        with CFNStack(name=stack_name, template=cfn_yml, delete_at_exit=True) as st_cfn_stack:
            if st_cfn_stack.exists:
                _resources_dict = {resource['LogicalResourceId']: resource['PhysicalResourceId']
                                   for resource in st_cfn_stack.resources}
                ec2_instance_id = _resources_dict['EC2Instance']
                logger.info(f'CFNStack: Name: `{st_cfn_stack.name}` ID:`{st_cfn_stack.id}`')
                logger.info(f'EC2 Instance: `{ec2_instance_id}`')

                try:
                    with SSMDocument(name=ssm_doc_name, template=ssm_yml,
                                     plugin='runStressTest') as ssm_document:
                        if ssm_document.is_created:
                            logger.info(f'SSMDocument: Name: `{ssm_document.name}`')

                            ssm_document.run(instance_id=ec2_instance_id,
                                             s3_bucket_name=s3_bucket_name,
                                             s3_key_prefix=_random_text)
                            logger.info(f'Execution status: {ssm_document.command_status}')
                            logger.info(f'Stdout url: {ssm_document.command_s3_stdout}')
                            logger.info(f'Stderr url: {ssm_document.command_s3_stderr}')
                            logger.info(f'Start time: {ssm_document.command_start_time}')
                            logger.info(f'End time: {ssm_document.command_end_time}')

                except SSMDocumentCreationFailed as ssm_exp:
                    logger.exception(f'SSM Doc creation failed. Exiting context \n{ssm_exp}')

                if not ssm_document.is_deleted:
                    logger.error(f'SSM Doc couldn\'t get deleted. Please check in AWS console')

    except (StackCreationFailed, StackUpdateFailed) as cfn_exp:
        logger.exception(f'Stack create/update failed. Exiting context \n{cfn_exp}')
        sys.exit(1)


if __name__ == "__main__":
    trigger()
