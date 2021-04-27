import boto3
import time
from boto3.session import Session
import sys, traceback
import json
import requests
from botocore.config import Config
import logging
from utils.innovation_sbx_helpers import *
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


def accept_resource_share_sbx(credentials):
    client = boto3.client('ram',
                          aws_access_key_id=credentials['AccessKeyId'],
                          aws_secret_access_key=credentials['SecretAccessKey'],
                          aws_session_token=credentials['SessionToken'],
                          region_name=boto3.session.Session().region_name+"",
                          config=config
                          )

    # Check if resource share invitation is auto-accepted
    try:
        resource_shares = client.get_resource_shares(resourceOwner='OTHER-ACCOUNTS')
        if len(resource_shares["resourceShares"]) > 0:
            for r in resource_shares["resourceShares"]:
                if r["name"] == "ISTGWShareAppStream" and r["status"] == "ACTIVE":
                    return
    except Exception as e:
        message = {'MESSAGE': 'Exception while getting resource shares in the Sandbox Account','FILE': __file__.split('/')[-1], 
                                             'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise

    rs_arn = None

    try:
        response = client.get_resource_share_invitations()
        logger.info(response)
        if len(response['resourceShareInvitations']) != 0:
            for r in response['resourceShareInvitations']:
                if r["resourceShareName"] == "ISTGWShareAppStream":
                    rs_arn = r["resourceShareInvitationArn"]
                    break
    except Exception as e:
        message = {'MESSAGE': 'Exception ocurred while fetching TGW resource share invitation in the Sandbox Account',
                                   'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise

    if rs_arn is None:
        message = {'MESSAGE': 'No resource share invitations found', 'FILE': __file__.split('/')[-1], 
                                'METHOD': inspect.stack()[0][3], 'MESSAGE': 'No resource share invitations found'}
        logger.exception(message)
        raise Exception("No resource share invitations found")
    
    try:
        accept_inv = client.accept_resource_share_invitation(
            resourceShareInvitationArn=rs_arn,
            clientToken='xyz_abcd9991'
        )
    except Exception as e:
        message = {'MESSAGE': 'Unable to accept TGW resource share invitation in the Sandbox Account', 'FILE': __file__.split('/')[-1], 
                                                     'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise

    return


def create(event, context):

    logger.info("Accepting Resource Share for Transit Gateway")
    logger.info(event)

    try:

        props = event["ResourceProperties"]
    
        sbx = props['Sandbox_Account_ID']
    
        credentials_sbx = assume_role(sbx)
    
        accept_resource_share_sbx(credentials_sbx)

        responseData = {
            "Message": "TGW resource sharing accepted"
        }
        send(event, context, SUCCESS, responseData, "Accept_TGW_Resource_Share")

    except Exception as e:
        message = {'MESSAGE': 'Exception occurred while attempting to accept TGW resource share', 
                              'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        errorResponseData = {
            "Message": "Resource Sharing Failed"
        }
        send(event, context, FAILED, errorResponseData, "Accept_TGW_Resource_Share")


def main(event, context):

    if event['RequestType'] == 'Create':
        create(event, context)
        return
    elif event['RequestType'] == 'Update':
        responseData = {"message": "No updates were made"}
        send(event, context, SUCCESS, responseData, "Accept_TGW_Resource_Share")
        return
    elif event['RequestType'] == 'Delete':
        responseData = {"message":"No deletes were made."}
        send(event, context, SUCCESS, responseData, "Accept_TGW_Resource_Share")
        return
    else:
        responseData = {"message": "Unsupported operation"}
        send(event, context, FAILED, responseData, "Accept_TGW_Resource_Share")


