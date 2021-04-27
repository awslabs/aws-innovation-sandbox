import logging
import boto3
import time
from boto3.session import Session
import sys
import traceback
import json
import uuid
import requests
from botocore.config import Config
from utils.innovation_sbx_helpers import *
import traceback
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


def create_scp_sbx(client, name, tb, scp_name):
    try:
        response = requests.get(
            tb+scp_name)
        scp = response.json()
        scp = str(scp).replace("'", "\"")
        response = client.create_policy(
            Content=scp,
            Description=name,
            Name=name,
            Type='SERVICE_CONTROL_POLICY'
        )
    except Exception as e:
        message = {'MESSAGE': 'Exception while creating Service Control Policy',
                              'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise
    return response['Policy']['PolicySummary']['Id']


def create(event, context):

    logger.info("Attaching SCPs")
    

    try:

        props = event["ResourceProperties"]

        sbx = props['Sandbox_Account_ID']
        sbx_ou = props['Sandbox_OU']
        scp_gd = props['SCPGD']
        scp_ntwrk = props['SCPNTWRK']
        tb = props['Template_Base_Path']

        client = boto3.client('organizations', config=config)

        scp_guardrails = create_scp_sbx(client, scp_gd, tb, 'innovation_sbx_guardrails_scp.json')
        scp_network = create_scp_sbx(client, scp_ntwrk, tb, 'innovation_sbx_network_controls_scp.json')

        client.attach_policy(PolicyId=scp_guardrails, TargetId=sbx_ou)
        client.attach_policy(PolicyId=scp_network, TargetId=sbx_ou)

        logger.info("Attached Service Control Policies")

        responseData = {
            "Message": "Sandbox SCPs Attached"
        }

        send(event, context, SUCCESS, responseData, "Sbx_Attach_SCPs")

    except Exception as e:
        message = {'MESSAGE': 'Exception occurred while creating and attaching SCPs',
                              'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        errorResponseData = {
            "Message": "Sandbox SCP Attachment Failed"
        }
        send(event, context, FAILED, errorResponseData, "Sbx_Attach_SCPs")


def main(event, context):

    if event['RequestType'] == 'Create':
        create(event, context)
        return
    elif event['RequestType'] == 'Update':
        responseData = {"message": "No updates were made"}
        send(event, context, SUCCESS, responseData, "Sbx_Attach_SCPs")
        return
    elif event['RequestType'] == 'Delete':
        responseData = {"message": "SCPs were not deleted. Please delete them manually"}
        send(event, context, SUCCESS, responseData, "Sbx_Attach_SCPs")
        return
    else:
        responseData = {"message": "Unsupported opration"}
        send(event, context, FAILED, responseData, "Sbx_Attach_SCPs")
