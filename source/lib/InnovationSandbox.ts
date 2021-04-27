import cfn = require("@aws-cdk/aws-cloudformation");
import lambda = require("@aws-cdk/aws-lambda");
import cdk = require("@aws-cdk/core");
import iam = require("@aws-cdk/aws-iam");
import s3 = require("@aws-cdk/aws-s3");
import { CfnParameter, CfnResource } from '@aws-cdk/core';


export class InnovationSandbox extends cdk.Stack {
  public readonly response: string;
  constructor(
    scope: cdk.App,
    id: string,
    props?: any,
    s?: string
  ) {
    super(scope, id);

 


    const solutionsBucket = s3.Bucket.fromBucketAttributes(this, 'SolutionsBucket', {
      bucketName: props["solutionBucket"] + '-' + this.region
    });

    
    


    const mgmt_account_name = new cdk.CfnParameter(
      this,
      "Appstream Management Account Name",
      {
        type: "String",
        description: "Account Name for Appstream Management Account",
      }
    );

    const sbx_account_name = new cdk.CfnParameter(
      this,
      "Sandbox Account Name",
      {
        type: "String",
        description: "Account Name for Sandbox Account",
      }
    );

    const mgmt_email = new cdk.CfnParameter(
      this,
      "Appstream Management Account Email",
      {
        type: "String",
        description: "Email for Appstream Management Account",
      }
    );

    const sbx_email = new cdk.CfnParameter(this, "Sandbox Account Email", {
      type: "String",
      description: "Email for Sandbox Account",
    });

    const sbx_ou_name = new cdk.CfnParameter(this, "Sandbox OU Name", {
      type: "String",
      description: "OU Name for Sandbox Account",
    });

    const mgmt_ou_name = new cdk.CfnParameter(
      this,
      "Appstream Management OU Name",
      {
        type: "String",
        description: "OU Name for Appstream Management Account",
      }
    );

    // Create Accounts, OUs

   
   

    const l0_role_policy = new iam.Policy(this, "Create_Account_OU_Role_Policy", {
      statements:[ 
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          resources: [cdk.Fn.sub("arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${AWS::StackName}*:*")],
          actions: ["logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents" ]
        })
        ,new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: ["arn:aws:iam::*:role/SandboxAdminExecutionRole"],
        actions: ["sts:AssumeRole"]
      }),
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: ["*"],
        actions: ["organizations:ListRoots",
        "organizations:MoveAccount",
        "organizations:DescribeCreateAccountStatus",
        "organizations:ListParents",
        "organizations:ListAccounts",
        "organizations:ListOrganizationalUnitsForParent",
        "organizations:CreateOrganizationalUnit",
        "organizations:CreateAccount"]
      })
      
    ]
    });

    const l0_cfn_role_policy = l0_role_policy.node.defaultChild as iam.CfnPolicy;

    l0_cfn_role_policy.addMetadata('cfn_nag', {
      rules_to_suppress: [
        {
          id: 'W12',
          reason: 'Specified actions do not apply to specific resources'
        }
      ]
    });


    const l0_role = new iam.Role(this, "l0role",{
      assumedBy:new iam.ServicePrincipal('lambda.amazonaws.com')
    });

    l0_role.attachInlinePolicy(l0_role_policy);

    l0_role_policy.node.addDependency(l0_role);


    const l0 = new lambda.Function(this, "Create_Account_OU", {
      code: lambda.Code.fromBucket(solutionsBucket, props["solutionTradeMarkName"] + '/' + props["solutionVersion"] + '/InnovationSandbox.zip'),
      handler: "innovation_create_account_ou.main",
      timeout: cdk.Duration.minutes(15),
      runtime: lambda.Runtime.PYTHON_3_8,
      role: l0_role
    });

    const l0_cfn = l0.node.defaultChild as lambda.CfnFunction;

    l0_cfn.addMetadata('cfn_nag', {
      rules_to_suppress: [
        {
          id: 'W58',
          reason: 'Lambda function already has permission to write CloudWatch Logs'
        }
      ]
    });

    l0.node.addDependency(l0_role_policy);

    const create_account_ou = new cfn.CustomResource(
      this,
      "Innovation_Create_Account_OU",
      {
        provider: cfn.CustomResourceProvider.lambda(l0),
        properties: {
          Mgmt_Name: mgmt_account_name.valueAsString,
          Mgmt_Email: mgmt_email.valueAsString,
          Sbx_Name: sbx_account_name.valueAsString,
          Sbx_Email: sbx_email.valueAsString,
          Sbx_OU_Name: sbx_ou_name.valueAsString,
          Mgmt_OU_Name: mgmt_ou_name.valueAsString,
        },
      }
    );

   
  
   
    var _Mgmt = create_account_ou.getAtt("Appstream_Account_ID").toString();
    var _Sbx = create_account_ou.getAtt("Sandbox_Account_ID").toString();
    var _Sbx_OU = create_account_ou.getAtt("Sandbox_OU").toString();
    var S3_Templates_Base_Path = "https://"+props["solutionBucket"] + '-' + this.region+".s3.amazonaws.com/"+props["solutionTradeMarkName"] + '/' + props["solutionVersion"]+"/";



    const l1_role = new iam.Role(this, "l1role",{
      assumedBy:new iam.ServicePrincipal('lambda.amazonaws.com')
    });

    l1_role.addToPolicy(  new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      resources: [cdk.Fn.sub("arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${AWS::StackName}*:*")],
      actions: ["logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents" ]
    }));

    l1_role.addToPolicy( 
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: ["arn:aws:iam::*:role/SandboxAdminExecutionRole"],
        actions: ["sts:AssumeRole"]
      })
    );

    // Delete default VPCs

    const l1 = new lambda.Function(this, "Delete_Default_VPCs", {
      code: lambda.Code.fromBucket(solutionsBucket, props["solutionTradeMarkName"] + '/' + props["solutionVersion"] + '/InnovationSandbox.zip'),
      handler: "innovation_delete_default_vpcs.main",
      timeout: cdk.Duration.minutes(15),
      runtime: lambda.Runtime.PYTHON_3_8,
      role:l1_role
    });

    const l1_cfn = l1.node.defaultChild as lambda.CfnFunction;

    l1_cfn.addMetadata('cfn_nag', {
      rules_to_suppress: [
        {
          id: 'W58',
          reason: 'Lambda function already has permission to write CloudWatch Logs'
        }
      ]
    });

    const delete_default_vpcs = new cfn.CustomResource(
      this,
      "Innovation_Delete_Default_VPCs",
      {
        provider: cfn.CustomResourceProvider.lambda(l1),
        properties: {
          Appstream_Account_ID: _Mgmt,
          Sandbox_Account_ID: _Sbx
        },
      }
    );

    delete_default_vpcs.node.addDependency(create_account_ou);

    // Run Mgmt Stack

    const l2_role = new iam.Role(this, "l2role",{
      assumedBy:new iam.ServicePrincipal('lambda.amazonaws.com')
    });

    l2_role.addToPolicy(  new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      resources: [cdk.Fn.sub("arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${AWS::StackName}*:*")],
      actions: ["logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents" ]
    }));

    l2_role.addToPolicy( 
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: ["arn:aws:iam::*:role/SandboxAdminExecutionRole"],
        actions: ["sts:AssumeRole"]
      })
    );

    const l2 = new lambda.Function(this, "Run_Mgmt_Stack", {
      code: lambda.Code.fromBucket(solutionsBucket, props["solutionTradeMarkName"] + '/' + props["solutionVersion"] + '/InnovationSandbox.zip'),
      handler: "innovation_run_mgmt_stack.main",
      timeout: cdk.Duration.minutes(15),
      runtime: lambda.Runtime.PYTHON_3_8,
      role: l2_role
    });

    const l2_cfn = l2.node.defaultChild as lambda.CfnFunction;

    l2_cfn.addMetadata('cfn_nag', {
      rules_to_suppress: [
        {
          id: 'W58',
          reason: 'Lambda function already has permission to write CloudWatch Logs'
        }
      ]
    });


    
    const run_mgmt_stack = new cfn.CustomResource(
      this,
      "Innovation_Run_Mgmt_Stack",
      {
        provider: cfn.CustomResourceProvider.lambda(l2),
        properties: {
          Appstream_Account_ID: _Mgmt,
          Sandbox_Account_ID: _Sbx,
          Template_Base_Path: S3_Templates_Base_Path
        },
      }
    );

    run_mgmt_stack.node.addDependency(delete_default_vpcs);

    var _Tgw_ID = run_mgmt_stack.getAtt("TGW_ID").toString();
    var _Egress_Attach_ID = run_mgmt_stack
      .getAtt("EGRESS_ATTACH_ID")
      .toString();
    var _EIP = run_mgmt_stack.getAtt("EIP").toString();
    var _EIP2 = run_mgmt_stack.getAtt("EIP2").toString();

    // Accept resource share

    const l3_role = new iam.Role(this, "l3role",{
      assumedBy:new iam.ServicePrincipal('lambda.amazonaws.com')
    });

    l3_role.addToPolicy(  new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      resources: [cdk.Fn.sub("arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${AWS::StackName}*:*")],
      actions: ["logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents" ]
    }));

    l3_role.addToPolicy( 
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: ["arn:aws:iam::*:role/SandboxAdminExecutionRole"],
        actions: ["sts:AssumeRole"]
      })
    );

    const l3 = new lambda.Function(this, "TGW_Resource_Share", {
      code: lambda.Code.fromBucket(solutionsBucket, props["solutionTradeMarkName"] + '/' + props["solutionVersion"] + '/InnovationSandbox.zip'),
      handler: "innovation_accept_resource_share.main",
      timeout: cdk.Duration.minutes(15),
      runtime: lambda.Runtime.PYTHON_3_8,
      role: l3_role
    });

    const l3_cfn = l3.node.defaultChild as lambda.CfnFunction;

    l3_cfn.addMetadata('cfn_nag', {
      rules_to_suppress: [
        {
          id: 'W58',
          reason: 'Lambda function already has permission to write CloudWatch Logs'
        }
      ]
    });


    const accept_resource_share = new cfn.CustomResource(
      this,
      "Innovation_Accept_Resource_Share",
      {
        provider: cfn.CustomResourceProvider.lambda(l3),
        properties: {
          Sandbox_Account_ID: _Sbx,
        },
      }
    );

    accept_resource_share.node.addDependency(run_mgmt_stack);

    // Run SBX Stack

    const l4_role = new iam.Role(this, "l4role",{
      assumedBy:new iam.ServicePrincipal('lambda.amazonaws.com')
    });

    l4_role.addToPolicy(  new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      resources: [cdk.Fn.sub("arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${AWS::StackName}*:*")],
      actions: ["logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents" ]
    }));

    l4_role.addToPolicy( 
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: ["arn:aws:iam::*:role/SandboxAdminExecutionRole"],
        actions: ["sts:AssumeRole"]
      })
    );

    const l4 = new lambda.Function(this, "Run_Sbx_Stack", {
      code: lambda.Code.fromBucket(solutionsBucket, props["solutionTradeMarkName"] + '/' + props["solutionVersion"] + '/InnovationSandbox.zip'),
      handler: "innovation_run_sbx_stack.main",
      timeout: cdk.Duration.minutes(15),
      runtime: lambda.Runtime.PYTHON_3_8,
      role: l4_role
    });

    const l4_cfn = l4.node.defaultChild as lambda.CfnFunction;

    l4_cfn.addMetadata('cfn_nag', {
      rules_to_suppress: [
        {
          id: 'W58',
          reason: 'Lambda function already has permission to write CloudWatch Logs'
        }
      ]
    });


    const run_sbx_stack = new cfn.CustomResource(
      this,
      "Innovation_Run_Sbx_Stack",
      {
        provider: cfn.CustomResourceProvider.lambda(l4),
        properties: {
          Appstream_Account_ID: _Mgmt,
          Sandbox_Account_ID: _Sbx,
          Tgw_ID: _Tgw_ID,
          EIP: _EIP,
          EIP2: _EIP2,
          Template_Base_Path: S3_Templates_Base_Path
        },
      }
    );

    run_sbx_stack.node.addDependency(accept_resource_share);

    var _Sbx_Attach_ID = run_sbx_stack.getAtt("SBX_Attach_ID").toString();

    // Run Transit gateway setup

    const l5_role = new iam.Role(this, "l5role",{
      assumedBy:new iam.ServicePrincipal('lambda.amazonaws.com')
    });

    l5_role.addToPolicy(  new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      resources: [cdk.Fn.sub("arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${AWS::StackName}*:*")],
      actions: ["logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents" ]
    }));

    l5_role.addToPolicy( 
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: ["arn:aws:iam::*:role/SandboxAdminExecutionRole"],
        actions: ["sts:AssumeRole"]
      })
    );

    const l5 = new lambda.Function(this, "TGW_Route_Tables", {
      code: lambda.Code.fromBucket(solutionsBucket, props["solutionTradeMarkName"] + '/' + props["solutionVersion"] + '/InnovationSandbox.zip'),
      handler: "innovation_tgw_route_tables.main",
      timeout: cdk.Duration.minutes(15),
      runtime: lambda.Runtime.PYTHON_3_8,
      role: l5_role
    });

    const l5_cfn = l5.node.defaultChild as lambda.CfnFunction;

    l5_cfn.addMetadata('cfn_nag', {
      rules_to_suppress: [
        {
          id: 'W58',
          reason: 'Lambda function already has permission to write CloudWatch Logs'
        }
      ]
    });


    const tgw_route_tables = new cfn.CustomResource(
      this,
      "Innovation_TGW_Route_Tables",
      {
        provider: cfn.CustomResourceProvider.lambda(l5),
        properties: {
          Appstream_Account_ID: _Mgmt,
          Tgw_ID: _Tgw_ID,
          Egress_Attach: _Egress_Attach_ID,
          Sbx_Attach: _Sbx_Attach_ID,
          Template_Base_Path: S3_Templates_Base_Path
        },
      }
    );

    tgw_route_tables.node.addDependency(run_sbx_stack);

    // Attach SCPs

    const l6_role = new iam.Role(this, "l6role",{
      assumedBy:new iam.ServicePrincipal('lambda.amazonaws.com')
    });

    const l6_role_policy = new iam.Policy(this, "SBX_SCP_Role_Policy", {
      statements:[ new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: [cdk.Fn.sub("arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${AWS::StackName}*:*")],
        actions: ["logs:CreateLogGroup",
                  "logs:CreateLogStream",
                  "logs:PutLogEvents" ]
      }),
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: ["arn:aws:iam::*:role/SandboxAdminExecutionRole"],
        actions: ["sts:AssumeRole"]
      }),
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        // resources: [cdk.Fn.sub("arn:aws:organizations::${AWS::AccountId}:policy/*")],
        resources: ["*"],
        actions: ["organizations:CreatePolicy"]
      }),
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: [cdk.Fn.sub("arn:aws:organizations::${AWS::AccountId}:*/*")],
        actions: ["organizations:AttachPolicy"]
      })
    ]
    });

    const l6_cfn_role_policy = l6_role_policy.node.defaultChild as iam.CfnPolicy;

    l6_cfn_role_policy.addMetadata('cfn_nag', {
      rules_to_suppress: [
        {
          id: 'W12',
          reason: 'CreatePolicy action does not apply to specific resource'
        }
      ]
    });

    l6_role.attachInlinePolicy(l6_role_policy);

    l6_role_policy.node.addDependency(l6_role);

    const l6 = new lambda.Function(this, "SBX_SCP", {
      code: lambda.Code.fromBucket(solutionsBucket, props["solutionTradeMarkName"] + '/' + props["solutionVersion"] + '/InnovationSandbox.zip'),
      handler: "innovation_sbx_attach_scp.main",
      timeout: cdk.Duration.minutes(15),
      runtime: lambda.Runtime.PYTHON_3_8,
      role:l6_role
    });

    l6.node.addDependency(l6_role_policy);

    const l6_cfn = l6.node.defaultChild as lambda.CfnFunction;

    l6_cfn.addMetadata('cfn_nag', {
      rules_to_suppress: [
        {
          id: 'W58',
          reason: 'Lambda function already has permission to write CloudWatch Logs'
        }
      ]
    });


    const attach_scp = new cfn.CustomResource(this, "Innovation_Attach_SCPs", {
      provider: cfn.CustomResourceProvider.lambda(l6),
      properties: {
        Sandbox_Account_ID: _Sbx,
        Sandbox_OU: _Sbx_OU,
        SCPGD: cdk.Fn.sub("${AWS::StackName}_guardrails_scp"),
        SCPNTWRK: cdk.Fn.sub("${AWS::StackName}_network_scp"),
        Template_Base_Path: S3_Templates_Base_Path
      },
    });

    attach_scp.node.addDependency(tgw_route_tables);

    const mgmt_id_output = new cdk.CfnOutput(this, "Management-Account-ID", {
      value: _Mgmt,
      description: "Account ID of the Management Account"
    });

    const sbx_id_output = new cdk.CfnOutput(this, "Sandbox-Account-ID", {
      value: _Sbx,
      description: "Account ID of the Sandbox Account"
    });
  }
}
