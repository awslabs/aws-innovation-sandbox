import logging
import boto3
import time
from boto3.session import Session
import sys, traceback
import json
import requests
import botocore
from botocore.config import Config
from utils.innovation_sbx_helpers import *
import inspect

SUCCESS = "SUCCESS"
FAILED = "FAILED"
VPC_CHECK_MAX_RETRIES = 20

config = Config(
   retries = {
      'max_attempts': 10,
      'mode': 'standard'
   }
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_regions(client):
    try:
        reg_list = []
        regions = client.describe_regions()
        data_str = json.dumps(regions)
        resp = json.loads(data_str)
        region_str = json.dumps(resp['Regions'])
        region = json.loads(region_str)
        for reg in region:
            reg_list.append(reg['RegionName'])
    except Exception as e:
        message = {'MESSAGE': 'Exception occured while fetching list of regions', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
    return reg_list
    

def get_default_vpcs(client):
    try:
        vpc_list = []
        vpcs = client.describe_vpcs(
            Filters=[
                {
                    'Name': 'isDefault',
                    'Values': [
                        'true',
                    ],
                },
            ]
        )
        vpcs_str = json.dumps(vpcs)
        resp = json.loads(vpcs_str)
        data = json.dumps(resp['Vpcs'])
        vpcs = json.loads(data)

        for vpc in vpcs:
            vpc_list.append(vpc['VpcId'])
    except Exception as e:
        message = {'MESSAGE': 'Exception occured while fetching VPCs', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
    
    return vpc_list


def del_igw(ec2, vpc_id):
    try:
        response = ec2.describe_internet_gateways(
            Filters=[
                {
                    'Name': 'attachment.vpc-id',
                    'Values': [
                        vpc_id
                    ],
                },
            ]
        )
        igws = response['InternetGateways']
    except Exception as e:
        message = {'MESSAGE': 'Exception occured while fetching Internet Gateways in default VPC', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise

    try:
        for igw in igws:
            igw_id = igw['InternetGatewayId']
            ec2.detach_internet_gateway(
                InternetGatewayId = igw_id,
                VpcId = vpc_id
            )
    except Exception as e:
        message = {'MESSAGE': 'Exception occured while detaching Internet Gateway in default VPC', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise


def del_sub(ec2, vpc_id):
    """ Delete the subnets """
    try:
        response = ec2.describe_subnets(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [
                        vpc_id
                    ],
                },
            ]
        )
        
    except Exception as e:
        message = {'MESSAGE': 'Exception occured while fetching Subnets in default VPC', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise

    subnets = response['Subnets']
    try:
        for subnet in subnets:
            if 'DefaultForAz' in subnet.keys() and subnet['DefaultForAz'] is True:
                subnet_id = subnet['SubnetId']
                ec2.delete_subnet(SubnetId = subnet_id)
    except Exception as e:
        message = {'MESSAGE': 'Exception occured while deleting Subnets in default VPC', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise



def del_rtb(ec2, vpc_id):
    """ Delete the route-tables """
    try:
        response = ec2.describe_route_tables(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [
                        vpc_id
                    ],
                },
            ]
        )
    except Exception as e:
        message = {'MESSAGE': 'Exception occured while fetching Route Tables in default VPC', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise

    route_tables = response['RouteTables']
    try:
        for route_table in route_tables:
            route_table_id = route_table['RouteTableId']
            assoc = route_table["Associations"]
            main = False
            for a in assoc:
                if "Main" in a.keys() and a["Main"] is True:
                    continue
                else:
                    ec2.delete_route_table(RouteTableId = route_table_id)
    except Exception as e:
        message = {'MESSAGE': 'Exception occured while deleting Route Tables in default VPC', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise


def del_acl(ec2, vpc_id):
    """ Delete the network-access-lists """
    try:
        response = ec2.describe_network_acls(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [
                        vpc_id
                    ],
                },
            ]
        )
    except Exception as e:
        message = {'MESSAGE': 'Exception occured while fetching Network ACLs for default VPC', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise

    network_acls = response['NetworkAcls']
    try:
        for acl in network_acls:
            if "IsDefault" in acl.keys() and acl["IsDefault"] is True:
                continue
            for assoc in acl['Associations']:
                network_acl_id = assoc['NetworkAclId']
                ec2.delete_network_acl(NetworkAclId = network_acl_id)
    except Exception as e:
        message = {'MESSAGE': 'Exception occured while deleting Network ACL for default VPC', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise
            


def del_sgp(ec2, vpc_id):
    """ Delete any security-groups """
    try:
        response = ec2.describe_security_groups(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [
                        vpc_id
                    ],
                },
            ]
        )
    except Exception as e:
        message = {'MESSAGE': 'Exception occured while fetching Security Groups in default VPC', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise

    security_groups = response['SecurityGroups']
    try:
        for sg in security_groups:
            sg_id = sg['GroupId']
            if sg["GroupName"] != "default":
                ec2.delete_security_group(GroupId = sg_id)
    except Exception as e:
        message = {'Lambda':'innovation_delete_default_vpcs', 'Message': 'Exception occured while deleting Security Groups in default VPC', 'EXCEPTION:': str(e)}
        logger.exception(message)
        raise
            


def del_vpc(ec2, vpc_id):
    try:
        response = ec2.delete_vpc(
            VpcId=vpc_id
        )
    except Exception as e:
        message = {'MESSAGE': 'Exception occured while deleting default VPC', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logger.exception(message)
        raise


def del_main(credentials, client):
    logger.info("Deleting Default VPC and resources")
    regions = get_regions(client)

    for region in regions:
        try:
            ec2 = boto3.client('ec2', aws_access_key_id=credentials['AccessKeyId'],
                                  aws_secret_access_key=credentials['SecretAccessKey'],
                                  aws_session_token=credentials['SessionToken'],
                                  region_name=region, config=config)
            vpcs = get_default_vpcs(ec2)
        except boto3.exceptions.Boto3Error as e:
            message = {'MESSAGE': 'Exception occured while fetching default VPCs', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
            logger.exception(message)
            raise
        else:
            for vpc in vpcs:
                logger.info("REGION:" +
                      region + "\n" + "VPC Id:" + vpc)
                del_igw(ec2, vpc)
                del_sub(ec2, vpc)
                del_rtb(ec2, vpc)
                del_acl(ec2, vpc)
                del_sgp(ec2, vpc)
                del_vpc(ec2, vpc)


def delete_default_VPC(credentials):

    ec2 = boto3.client('ec2',
                       aws_access_key_id=credentials['AccessKeyId'],
                       aws_secret_access_key=credentials['SecretAccessKey'],
                       aws_session_token=credentials['SessionToken'],
                       region_name=boto3.session.Session().region_name, config=config)
    desc_vpc = False
    iters = 0
    while desc_vpc is False and iters < VPC_CHECK_MAX_RETRIES:
        iters = iters+1
        try:
            default_vpc = ec2.describe_vpcs()
            desc_vpc = True
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'OptInRequired':
                logger.error("Caught exception 'OptInRequired', waiting for VPCs to be available: \n %s, %s", e, traceback.format_exc())
            else:
                logger.error("Error while fetching VPCs: \n %s, %s", e, traceback.format_exc())
                raise
            desc_vpc = False
            time.sleep(10)
    
    if desc_vpc is False:
        message = {'MESSAGE': 'Exception occured while fetching default VPCs', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3]}
        logger.exception(message)
        raise Exception("Error occured while fetching default VPCs")
    try:
        del_main(credentials, ec2)
    except Exception as e:
        raise
    return "Default VPCs deleted"


def create(event, context):

    logger.info(event)

    try:
        props = event["ResourceProperties"]

        appstream_act = props['Appstream_Account_ID']

        sbx_act = props['Sandbox_Account_ID']
    
        credentials = assume_role(appstream_act)
    
        delete_default_VPC(credentials)
    
        credentials_sbx = assume_role(sbx_act)
    
        delete_default_VPC(credentials_sbx)
        
        responseData = {
            "Appstream_Account_ID" : appstream_act,
            "Sandbox_Account_ID" : sbx_act
            }
    
        send(event, context, SUCCESS,
                         responseData, "Delete_Default_VPCs")
    except Exception as e:
        message = {'MESSAGE': 'Error occurred while deleting default VPCs', 'FILE': __file__.split('/')[-1], 
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e), 'TRACE': traceback.format_exc()}
        logging.exception(message)
        errorResponseData = {
            "Message":"Delete VPCs Failed"
        }
        send(event, context, FAILED,
                             errorResponseData, "Delete_Default_VPCs")

def main(event, context):


    if event['RequestType'] == 'Create':
        create(event, context)
        return
    elif event['RequestType'] == 'Update':
        responseData = {"message": "No updates were made"}
        send(event, context, SUCCESS, responseData, "Delete_Default_VPCs")
        return
    elif event['RequestType'] == 'Delete':
        responseData = {"message":"Default VPCs were deleted during the first run. Please recreate default VPCs manually."}
        send(event, context, SUCCESS, responseData, "Delete_Default_VPCs")
    else:
        responseData = {"message": "Unsupported opration"}
        send(event, context, FAILED, responseData, "Delete_Default_VPCs")

    