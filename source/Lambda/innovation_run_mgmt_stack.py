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
from utils.innovation_sbx_helpers import *
import inspect


SUCCESS = "SUCCESS"
FAILED = "FAILED"

config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_transit_gateway_id_mgmt(credentials):
    try:
        ec2 = boto3.client('ec2'
                       ,
                       aws_access_key_id=credentials['AccessKeyId'],
                       aws_secret_access_key=credentials['SecretAccessKey'],
                       aws_session_token=credentials['SessionToken'],
                       region_name=boto3.session.Session().region_name + "",
                       config=config
                       )
        vpcs = ec2.describe_vpcs()
        tgws = ec2.describe_transit_gateways()
        tgw = tgws['TransitGateways'][0]['TransitGatewayId']
        tgw_attchs = ec2.describe_transit_gateway_attachments()
        tgw_attch_id = tgw_attchs['TransitGatewayAttachments'][0]['TransitGatewayAttachmentId']
    except Exception as e:
        message = {'MESSAGE': 'Exception while fetching transit gateway IDs',
                              'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise

    return (tgw, tgw_attch_id)


def get_elastic_ip_mgmt(credentials):
    try:
        ec2 = boto3.client('ec2',
                       aws_access_key_id=credentials['AccessKeyId'],
                       aws_secret_access_key=credentials['SecretAccessKey'],
                       aws_session_token=credentials['SessionToken'],
                       region_name=boto3.session.Session().region_name + "",
                       config=config)
        addresses = ec2.describe_addresses()
        eip = []
        for eip_dict in addresses['Addresses']:
            eip.append(eip_dict['PublicIp'])
        if len(eip) != 2:
            raise Exception("Could not find 2 Elastic IP addresses. This solution needs 2 EIPs to be created.")
    except Exception as e:
        message = {'MESSAGE': 'Exception while fetching Elastic IPs',
                              'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise
    
    return eip


def create(event, context):

    logger.info(event)

    try:

        props = event["ResourceProperties"]

        appstream_act_id= props['Appstream_Account_ID']
        sbx_act_id = props['Sandbox_Account_ID']
        tb = props['Template_Base_Path']

        credentials = assume_role(appstream_act_id)

        s3_public_settings(appstream_act_id, credentials)

        logger.info("Running Management Stack")
        run_stack(
            appstream_act_id, tb + "InnovationSandboxManagementAccount.template", credentials, [{
                'ParameterKey': 'SbxAccountId',
                'ParameterValue': sbx_act_id
            },
                {
                    'ParameterKey': 'UUID',
                    'ParameterValue': str(uuid.uuid4()).replace('-', '')
                }
            ], 'InnovationSbxMgmtStack')

        tgw_id_details = get_transit_gateway_id_mgmt(credentials)

        tgw_id = tgw_id_details[0]

        egress_attach_id = tgw_id_details[1]

        eip = get_elastic_ip_mgmt(credentials)

        responseData = {
            "TGW_ID": tgw_id,
            "EGRESS_ATTACH_ID": egress_attach_id,
            "EIP": eip[0],
            "EIP2": eip[1]
        }

        send(event, context, SUCCESS,
             responseData, "AppStream_Account_Network_Setup")
    except Exception as e:
        message = {'MESSAGE': 'Error while launching the stack in the AppStream Account',
                              'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise


def delete(event, context):
    props = event["ResourceProperties"]
    _appstream_act = props['Appstream_Account_ID']
    credentials = assume_role(_appstream_act)

    try:
        delete_stack('InnovationSbxMgmtStack', credentials)
    except Exception as e:
        raise

    return


def main(event, context):

    try:
        if event['RequestType'] == 'Create':
            create(event, context)
        elif event['RequestType'] == 'Update':
            responseData = {"message": "No updates were made"}
            send(event, context, SUCCESS, responseData, "AppStream_Account_Network_Setup")
        elif event['RequestType'] == 'Delete':
            delete(event, context)
            responseData = {"message": "Deleted Appstream resources."}
            send(event, context, SUCCESS, responseData, "AppStream_Account_Network_Setup")
        else:
            responseData = {"message": "Unsupported opration"}
            send(event, context, FAILED,
                 responseData, "AppStream_Account_Network_Setup")
    except Exception as e:
        message = {'MESSAGE': 'Exception occurred during '+event['RequestType']+' stack action on AppStream account',
                          'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        errorResponseData = {
            "Message": "Appstream stack creation failed"
        }
        send(event, context, FAILED,
             errorResponseData, "AppStream_Account_Network_Setup")
