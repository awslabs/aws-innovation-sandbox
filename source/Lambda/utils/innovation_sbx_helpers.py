from __future__ import print_function
import boto3
import time
from boto3.session import Session
import sys, traceback
import json
import uuid
import requests
import botocore
from botocore.config import Config
import logging


config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)

logger = logging.getLogger()


def send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False):
    responseUrl = event['ResponseURL']
    responseBody = {}
    responseBody['Status'] = responseStatus
    responseBody['Reason'] = 'See the details in CloudWatch Log Stream: ' + context.log_stream_name
    responseBody['PhysicalResourceId'] = physicalResourceId or context.log_stream_name
    responseBody['StackId'] = event['StackId']
    responseBody['RequestId'] = event['RequestId']
    responseBody['LogicalResourceId'] = event['LogicalResourceId']
    responseBody['NoEcho'] = noEcho
    responseBody['Data'] = responseData

    json_responseBody = json.dumps(responseBody)

    logger.info("Response body:\n" + json_responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        response = requests.put(responseUrl,
                                data=json_responseBody,
                                headers=headers)
        logger.info("Status code: " + response.reason)
    except Exception as e:
        logger.exception("send(..) failed executing requests.put(..): " + str(e))


def assume_role(act):
    sts_client = boto3.client('sts', config=config)
    response = sts_client.assume_role(
        RoleArn="arn:aws:iam::" + act + ":role/SandboxAdminExecutionRole",
        RoleSessionName='Master2')
    credentials = response['Credentials']
    return credentials


def delete_stack(stack_name, credentials):

    cft = boto3.client('cloudformation',
                       aws_access_key_id=credentials['AccessKeyId'],
                       aws_secret_access_key=credentials['SecretAccessKey'],
                       aws_session_token=credentials['SessionToken'],
                       region_name=boto3.session.Session().region_name + "",
                       config=config
                       )
    try:
        response = cft.delete_stack(StackName=stack_name)
        waiter = cft.get_waiter('stack_delete_complete')
        waiter.wait(StackName=stack_name,
                    WaiterConfig={
                        'Delay': 30,
                        'MaxAttempts': 30
                    })
        logger.info(stack_name + ": Stack Delete Complete")
    except Exception as e:
        logging.exception("EXCEPTION while deleting the stack \n %s, %s", e, traceback.format_exc())
        raise
    return response


def run_stack(act, template_url, credentials, params, stack_name):
    cft = boto3.client('cloudformation',
                       aws_access_key_id=credentials['AccessKeyId'],
                       aws_secret_access_key=credentials['SecretAccessKey'],
                       aws_session_token=credentials['SessionToken'],
                       region_name=boto3.session.Session().region_name + "",
                       config=config
                       )
    try:
        cft.create_stack(
            StackName=stack_name,
            TemplateURL=template_url,
            NotificationARNs=[],
            Capabilities=[
                'CAPABILITY_NAMED_IAM',
            ],
            OnFailure='ROLLBACK',
            Tags=[
                {
                    'Key': 'ManagedResource',
                    'Value': 'True'
                }
            ],
            Parameters=params
        )
    except Exception as e:
        raise

    waiter = cft.get_waiter('stack_create_complete')
    waiter.wait(StackName=stack_name,
                WaiterConfig={
                    'Delay': 40,
                    'MaxAttempts': 50
                })

    logger.info(stack_name + " : Stack Creation Completed")
    return


def s3_public_settings(act, credentials):
    s3 = boto3.client('s3control',
                       aws_access_key_id=credentials['AccessKeyId'],
                       aws_secret_access_key=credentials['SecretAccessKey'],
                       aws_session_token=credentials['SessionToken'],
                       config=config
                       )
    try:
        response = s3.put_public_access_block(
            PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
            },
            AccountId=act
            )
    except Exception as e:
        logger.exception("Exception occured while setting S3 public access block at account level : %s \n %s", e, traceback.format_exc())
    logger.info("Blocked S3 public access at account level")