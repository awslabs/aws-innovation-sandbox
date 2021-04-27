import boto3
import time
from boto3.session import Session
import sys
import traceback
import json
import uuid
import requests
import botocore
from botocore.config import Config
from utils.innovation_sbx_helpers import *
import logging
import inspect


SUCCESS = "SUCCESS"
FAILED = "FAILED"

config = Config(
   retries = {
      'max_attempts': 10,
      'mode': 'standard'
   }
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def delete(event, context):
    props = event["ResourceProperties"]
    sbx = props['Sandbox_Account_ID']

    credentials = assume_role(sbx)

    try:
        delete_stack('InnovationSbxSBXStack', credentials)
    except Exception as e:
        raise

    return


def get_transit_gateway_id_mgmt(credentials):
    ec2 = boto3.client('ec2',
                       aws_access_key_id=credentials['AccessKeyId'],
                       aws_secret_access_key=credentials['SecretAccessKey'],
                       aws_session_token=credentials['SessionToken'],
                       region_name=boto3.session.Session().region_name+"",
                       config=config
                       )
    vpcs = ec2.describe_vpcs()
    vpc_id = vpcs["Vpcs"][0]["VpcId"]
    tgws = ec2.describe_transit_gateways()
    tgw = tgws['TransitGateways'][0]['TransitGatewayId']
    tgw_attchs = ec2.describe_transit_gateway_attachments()
    tgw_attch_id = tgw_attchs['TransitGatewayAttachments'][0]['TransitGatewayAttachmentId']
    return [tgw, tgw_attch_id]

    
def create(event, context):

    logger.info(event)

    try:

        props = event["ResourceProperties"]

        mgmt = props['Appstream_Account_ID']
        sbx = props['Sandbox_Account_ID']
        eip = props['EIP']
        eip2 = props['EIP2']
        tgw_id = props['Tgw_ID']
        tb = props['Template_Base_Path']

        credentials_sbx = assume_role(sbx)

     

        s3_public_settings(sbx, credentials_sbx)

        logger.info("Running Sandbox Stack")
        run_stack(sbx, tb+"InnovationSandboxSbxAccount.template", credentials_sbx, [
            {
                'ParameterKey': 'TgwID',
                'ParameterValue': tgw_id
            },
            {
                'ParameterKey': 'MgmtID',
                'ParameterValue': mgmt
            },
            {
                'ParameterKey': 'UUID',
                'ParameterValue': str(uuid.uuid4()).replace('-', '')
            },
            {
                'ParameterKey': 'EIP',
                'ParameterValue': eip
            },
            {
                'ParameterKey': 'EIP2',
                'ParameterValue': eip2
            }
        ], 'InnovationSbxSBXStack')

        tgw_sbx_details = get_transit_gateway_id_mgmt(credentials_sbx)

        sbx_attach_id = tgw_sbx_details[1]

        responseData = {"SBX_Attach_ID": sbx_attach_id}

        send(event, context, SUCCESS,
                         responseData, "Run_Sbx_Setup")

    except Exception as e:
        message = {'MESSAGE': 'Exception while launching the stack in the Sandbox Account',
                              'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        errorResponseData = {
            "Message": "Sandbox Stack Run Failed"
        }
        send(event, context, FAILED,
                             errorResponseData, "Run_Sbx_Setup")


def main(event, context):

    try:

        if event['RequestType'] == 'Create':
            create(event, context)
            return
        elif event['RequestType'] == 'Update':
            responseData = {"message": "No updates were made"}
            send(event, context, SUCCESS,
                             responseData, "Run_Sbx_Setup")
            return
        elif event['RequestType'] == 'Delete':
            delete(event, context)
            responseData = {"message": "Deleted Sandbox resources."}
            send(event, context, SUCCESS,responseData, "Run_Sbx_Setup")
            return
        else:
            responseData = {"message": "Unsupported opration"}
            send(event, context, FAILED,
                             responseData, "Run_Sbx_Setup")

    except Exception as e:

        message = {'MESSAGE': 'Exception occurred during '+event['RequestType']+' stack action on Sandbox account',
                              'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        errorResponseData = {
            "Message": "Sandbox stack creation failed"
        }
        send(event, context, FAILED,
             errorResponseData, "Run_Sbx_Setup")