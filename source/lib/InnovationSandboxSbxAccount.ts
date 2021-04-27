
import cdk = require("@aws-cdk/core");
import ec2 = require("@aws-cdk/aws-ec2");
import iam = require("@aws-cdk/aws-iam");
import cloudtrail = require("@aws-cdk/aws-cloudtrail");
import s3 = require("@aws-cdk/aws-s3");

export class InnovationSandboxSbxAccount extends cdk.Stack {
  public readonly response: string;
  constructor(
    scope: cdk.App,
    id: string,
    props?: any,
    s?: string
  ) {
    super(scope, id);

    const tgw_id = new cdk.CfnParameter(this, "TgwID", {
      type: "String",
      description: "TgwID",
    });

    const appstream_account_id = new cdk.CfnParameter(this, "MgmtID", {
      type: "String",
      description: "MgmtID",
    });

    const _uuid = new cdk.CfnParameter(this, "UUID", {
      type: "String",
      description: "UUID",
    });

    const _eip = new cdk.CfnParameter(this, "EIP", {
      type: "String",
      description: "EIP",
    });

    const _eip2 = new cdk.CfnParameter(this, "EIP2", {
      type: "String",
      description: "EIP",
    });

    // const tgw_rt_id = new cdk.CfnParameter(this, "TgwRTID", {
    //     type: "String",
    //     description: "TgwRTID"
    //   });

    const vpc_sbx = new ec2.Vpc(this, "ISSBXVPC", {
      cidr: "192.168.0.0/16",
      maxAzs: 1,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: "private_innovation_sandbox_1",
          subnetType: ec2.SubnetType.ISOLATED
        },
        {
          cidrMask: 24,
          name: "private_innovation_sandbox_2",
          subnetType: ec2.SubnetType.ISOLATED
        }
      ],
    });

    const TransitGatewayAttachmentSbx = new ec2.CfnTransitGatewayAttachment(
      this,
      "ISTransitGatewayAttachmentSbx",
      {
        transitGatewayId: tgw_id.valueAsString,
        vpcId: vpc_sbx.vpcId,
        subnetIds: [vpc_sbx.isolatedSubnets[0].subnetId],
        tags: [
          {
            key: "Name",
            value: "IS-TG-Sbx-VPC-Private_SubNet-Attachment",
          },
        ],
      }
    );

    for (let subnet of vpc_sbx.isolatedSubnets) {
      new ec2.CfnRoute(this, subnet.node.uniqueId, {
        routeTableId: subnet.routeTable.routeTableId,
        destinationCidrBlock: "0.0.0.0/0",
        transitGatewayId: tgw_id.valueAsString,
      }).addDependsOn(TransitGatewayAttachmentSbx);
    }

    const role = new iam.Role(this, "SandboxLoginRole", {
      assumedBy: new iam.AccountPrincipal(appstream_account_id.valueAsString),
      roleName: "SandboxLoginRole"
    });

    // role.addToPolicy(
    //   new iam.PolicyStatement({
    //     resources: ["*"],
    //     actions: ["*"],
    //     conditions: [],
    //   })
    // );

    const policyDocument = {
      Version: "2012-10-17",
      Statement: [
        {
          Sid: "AllowAppStreamIPs",
          Effect: "Allow",
          Action: "*",
          Resource: "*",
          Condition: {
            IpAddress: {
              "aws:SourceIp": [
                _eip.valueAsString,
                _eip2.valueAsString,
                "10.0.0.0/16",
                "172.16.0.0/12",
                "192.168.0.0/16",
              ],
            },
          },
        },
        {
          Sid: "AllowAWSServiceCalls",
          Effect: "Allow",
          Action: "*",
          Resource: "*",
          Condition: {
            Bool: {
              "aws:ViaAWSService": "true",
            },
          },
        },
      ],
    };

    const newPolicyDocument = iam.PolicyDocument.fromJson(policyDocument);

    const mp = new iam.ManagedPolicy(this, "ManagedPolicy", {
      document: newPolicyDocument,
    });

    role.addManagedPolicy(mp);

    const service_role = new iam.Role(this, "SandboxServiceRole", {
      assumedBy: new iam.CompositePrincipal(
        new iam.ServicePrincipal("apigateway.amazonaws.com"),
        new iam.ServicePrincipal("athena.amazonaws.com"),
        new iam.ServicePrincipal("autoscaling.amazonaws.com"),
        new iam.ServicePrincipal("cloudtrail.amazonaws.com"),
        new iam.ServicePrincipal("config-multiaccountsetup.amazonaws.com"),
        new iam.ServicePrincipal("config.amazonaws.com"),
        new iam.ServicePrincipal("dynamodb.amazonaws.com"),
        new iam.ServicePrincipal(
          "dynamodb.application-autoscaling.amazonaws.com"
        ),
        new iam.ServicePrincipal("ec2.amazonaws.com"),
        new iam.ServicePrincipal("ec2.application-autoscaling.amazonaws.com"),
        new iam.ServicePrincipal("ec2fleet.amazonaws.com"),
        new iam.ServicePrincipal("ec2scheduled.amazonaws.com"),
        new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        new iam.ServicePrincipal("ecs.amazonaws.com"),
        new iam.ServicePrincipal("ecs.application-autoscaling.amazonaws.com"),
        new iam.ServicePrincipal("edgelambda.amazonaws.com"),
        new iam.ServicePrincipal("eks.amazonaws.com"),
        new iam.ServicePrincipal("firehose.amazonaws.com"),
        new iam.ServicePrincipal("glue.amazonaws.com"),
        new iam.ServicePrincipal("greengrass.amazonaws.com"),
        new iam.ServicePrincipal("guardduty.amazonaws.com"),
        new iam.ServicePrincipal("health.amazonaws.com"),
        new iam.ServicePrincipal("iam.amazonaws.com"),
        new iam.ServicePrincipal("kinesis.amazonaws.com"),
        new iam.ServicePrincipal("kinesisanalytics.amazonaws.com"),
        new iam.ServicePrincipal("kms.amazonaws.com"),
        new iam.ServicePrincipal("lakeformation.amazonaws.com"),
        new iam.ServicePrincipal("lambda.amazonaws.com"),
        new iam.ServicePrincipal("macie.amazonaws.com"),
        new iam.ServicePrincipal("opsworks-cm.amazonaws.com"),
        new iam.ServicePrincipal("opsworks.amazonaws.com"),
        new iam.ServicePrincipal("organizations.amazonaws.com"),
        new iam.ServicePrincipal("quicksight.amazonaws.com"),
        new iam.ServicePrincipal("rds.amazonaws.com"),
        new iam.ServicePrincipal("redshift.amazonaws.com"),
        new iam.ServicePrincipal("rekognition.amazonaws.com"),
        new iam.ServicePrincipal("s3.amazonaws.com"),
        new iam.ServicePrincipal("sagemaker.amazonaws.com"),
        new iam.ServicePrincipal("secretsmanager.amazonaws.com"),
        new iam.ServicePrincipal("servicecatalog.amazonaws.com"),
        new iam.ServicePrincipal("sns.amazonaws.com"),
        new iam.ServicePrincipal("spotfleet.amazonaws.com"),
        new iam.ServicePrincipal("sqs.amazonaws.com"),
        new iam.ServicePrincipal("ssm.amazonaws.com"),
        new iam.ServicePrincipal("sso.amazonaws.com"),
        new iam.ServicePrincipal("states.amazonaws.com"),
        new iam.ServicePrincipal("storagegateway.amazonaws.com"),
        new iam.ServicePrincipal("sts.amazonaws.com"),
        new iam.ServicePrincipal("support.amazonaws.com"),
        new iam.ServicePrincipal("swf.amazonaws.com")
      ),
      roleName:"SandboxServiceRole"
    });

    

    service_role.addToPolicy(
      new iam.PolicyStatement({
        resources: ["*"],
        actions: ["*"],
      })
    );

    const ip = new iam.CfnInstanceProfile(this, "Sandbox-EC2-Instance-Profile",{
      roles:[service_role.roleName]
    })

    const trail_bucket_access_logs = new s3.Bucket(this, "sandbox-bucket-al", {
      bucketName: "sandbox" + "-ct-" + _uuid.valueAsString+"-al",
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: new s3.BlockPublicAccess({
        blockPublicAcls: true,
        blockPublicPolicy: true,
        ignorePublicAcls:true
      })
    });

    const trail_bucket = new s3.Bucket(this, "sandbox-bucket", {
      bucketName: "sandbox" + "-ct-" + _uuid.valueAsString,
      encryption: s3.BucketEncryption.S3_MANAGED,
      serverAccessLogsBucket: trail_bucket_access_logs,
      blockPublicAccess: new s3.BlockPublicAccess({
        blockPublicAcls: true,
        blockPublicPolicy: true,
        ignorePublicAcls:true
      })
    });

    trail_bucket.addToResourcePolicy(new iam.PolicyStatement({
      effect: iam.Effect.DENY,
      actions: ["s3:*"],
      principals: [ new iam.AnyPrincipal],
      resources:  ["arn:aws:s3:::" + trail_bucket.bucketName, "arn:aws:s3:::" + trail_bucket.bucketName+"/*"],
      conditions:{
        "Bool": {
          "aws:SecureTransport": "false"
      }
      }                          
        }));

    const fl_bucket_access_logs = new s3.Bucket(this, "sandbox-flowlogs-bucket-al", {
      bucketName: "sandbox" + "-fl-" + _uuid.valueAsString+"-al",
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: new s3.BlockPublicAccess({
        blockPublicAcls: true,
        blockPublicPolicy: true,
        ignorePublicAcls:true
      })
    });


    const fl_bucket = new s3.Bucket(this, "sandbox-flowlogs-bucket", {
      bucketName: "sandbox" + "-fl-" + _uuid.valueAsString,
      encryption: s3.BucketEncryption.S3_MANAGED,
      serverAccessLogsBucket: fl_bucket_access_logs,
      blockPublicAccess: new s3.BlockPublicAccess({
        blockPublicAcls: true,
        blockPublicPolicy: true,
        ignorePublicAcls:true
      })
    });

    fl_bucket.addToResourcePolicy(new iam.PolicyStatement({
      effect: iam.Effect.DENY,
      actions: ["s3:*"],
      principals: [ new iam.AnyPrincipal],
      resources:  ["arn:aws:s3:::" + fl_bucket.bucketName, "arn:aws:s3:::" + fl_bucket.bucketName+"/*"],
      conditions:{
        "Bool": {
          "aws:SecureTransport": "false"
      }
      }                          
        }));

    const trail = new cloudtrail.Trail(this, "CloudTrail", {
      bucket: trail_bucket,
      trailName: "sandbox-cloudtrail"
    });

    const flow_logs = new ec2.FlowLog(this, "FlowLogs", {
      flowLogName: "sandbox-vpc-flowlogs",
      resourceType: ec2.FlowLogResourceType.fromVpc(vpc_sbx),
      destination: ec2.FlowLogDestination.toS3(fl_bucket),
    });

    

  }
}
