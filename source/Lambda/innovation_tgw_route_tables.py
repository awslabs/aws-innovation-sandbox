from __future__ import print_function
import boto3
import time
from boto3.session import Session
import sys, traceback
import json
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
    
    mgmt = props['Appstream_Account_ID']
    
    credentials = assume_role(mgmt)

    try:
        delete_stack('InnovationMgmtTGWStack', credentials)
    except Exception as e:
        raise

    return


def create(event, context):

    logger.info(event)

    try:
        props = event["ResourceProperties"]
    
        mgmt = props['Appstream_Account_ID']
        tgw_id = props['Tgw_ID']
        egress_attach_id = props['Egress_Attach']
        sbx_attach_id = props['Sbx_Attach']
        tb = props['Template_Base_Path']
    
        credentials = assume_role(mgmt)

        logger.info("Running TGW Stack")
        run_stack( mgmt, tb+"InnovationSandboxTransitGatewaySetup.template", credentials, [
        {
            'ParameterKey': 'TGID',
            'ParameterValue': tgw_id
        },
        {
            'ParameterKey': 'EGREEATTCH',
            'ParameterValue': egress_attach_id
        },
        {
            'ParameterKey': 'SBXTGATTCH',
            'ParameterValue': sbx_attach_id
        }
        ],'InnovationMgmtTGWStack')
    
        responseData = {"Message":"Successfly Deployed Innovation Architecture"}
    
        send(event, context, SUCCESS,
                         responseData, "TGW_RT_Setup")

    except Exception as e:
        message = {'MESSAGE': 'Exception occurred while creating/attaching SCPs',
                              'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        errorResponseData = {
            "Message":"TGW Route Tables Setup Failed"
        }
        send(event, context, FAILED,
                             errorResponseData, "TGW_RT_Setup")

def main(event, context):

    try:

        if event['RequestType'] == 'Create':
            create(event, context)
            return
        elif event['RequestType'] == 'Update':
            responseData = {"message": "No updates were made"}
            send(event, context, SUCCESS, responseData, "TGW_RT_Setup")
            return
        elif event['RequestType'] == 'Delete':
            delete(event, context)
            responseData = {"message":"Deleted Transit Gateway Setup."}
            send(event, context, SUCCESS,responseData, "TGW_RT_Setup")
            return
        else:
            responseData = {"message": "Unsupported operation"}
            send(event, context, FAILED, responseData, "TGW_RT_Setup")

    except Exception as e:

        message = {'MESSAGE': 'Exception occurred during '+event['RequestType']+' stack action while setting up TGW',
                              'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)

        errorResponseData = {
            "Message": "TGW Setup Failed"
        }
        send(event, context, FAILED,
             errorResponseData, "TGW_RT_Setup")
