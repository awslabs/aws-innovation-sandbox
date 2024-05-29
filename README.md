# Deprecation Notice

This AWS Solution has been archived and is no longer maintained by AWS. To discover other solutions, please visit the [AWS Solutions Library](https://aws.amazon.com/solutions/).

# AWS Innovation Sandbox

Innovation Sandbox Solution

## Getting Started

To get started with the AWS Innovation Sandbox, please review the solution documentation. [AWS Innovation Sandbox](https://docs.aws.amazon.com/solutions/latest/aws-innovation-sandbox/welcome.html)

## Building from GitHub
***

### Overview of the process

Building from GitHub source will allow you to modify the solution. The process consists of downloading the source from GitHub, creating buckets to be used for deployment, building the solution, and uploading the artifacts needed for deployment.

#### You will need:

* a Linux client with the AWS CLI v2 installed and python 3.8+, AWS CDK
* source code downloaded from GitHub
* two S3 buckets (minimum): 1 global and 1 for each region where you will deploy

### Download from GitHub

Clone or download the repository to a local directory on your linux client. Note: if you intend to modify Ops Automator you may wish to create your own fork of the GitHub repo and work from that. This allows you to check in any changes you make to your private copy of the solution.

**Git Clone example:**

```
git clone <Git URL>
```



#### Repository Organization

```
|- deployment/                - contains build scripts, deployment templates, and dist folders for staging assets.
  |- cdk-solution-helper/     - helper function for converting CDK output to a format compatible with the AWS Solutions pipelines.
  |- build-s3-dist.sh         - builds the solution and copies artifacts to the appropriate /global-s3-assets or /regional-s3-assets folders.
|- source/                    - all source code, scripts, tests, etc.
  |- bin/
    |- innovation-sandbox.ts  - the AWS Innovation Sandbox cdk app.
  |- cloudformation_templates/
    |- innovation_sandbox_appstream.yaml - Cloudformation Template to setup AppStream. Please refer to the deployment guide for more information.
  |- lambda/                  - Lambda function with source code and test cases.        
  |- lib/
    |- InnovationSandbox.ts  - the main CDK stack for the solution.
    |- InnovationSandboxManagementAccount.ts  -  stack for deploying resources in the Management Account created by the solution.
    |- InnovationSandboxSbxAccount.ts - stack for deploying resources in the Sandbox Account created by the solution.
    |- InnovationSandboxTransitGatewaySetup.ts - stack for setting up Transit Gateway.
  |- service_control_policies/  - Service Control Policies for OUs created by the solution
  |- test/
    |- __snapshots__/         - unit and snapshot tests for the solution
  |- cdk.json                 - config file for CDK.
  |- jest.config.js           - config file for unit tests.
  |- package.json             - package file for the aws instance scheduler CDK project.
  |- README.md                - doc file for the CDK project.
|- .gitignore
|- .viperlightignore          - Viperlight scan ignore configuration  (accepts file, path, or line item).
|- .viperlightrc              - Viperlight scan configuration.
|- buildspec.yml              - main build specification for CodeBuild to perform builds and execute unit tests.
|- CHANGELOG.md               - required for every solution to include changes based on version to auto-build release notes.
|- CODE_OF_CONDUCT.md         - standardized open source file for all solutions.
|- CONTRIBUTING.md            - standardized open source file for all solutions.
|- LICENSE.txt                - required open source file for all solutions - should contain the Apache 2.0 license.
|- NOTICE.txt                 - required open source file for all solutions - should contain references to all 3rd party libraries.
|- README.md                  - required file for all solutions.

```

### Build

AWS Solutions use two buckets: a bucket for global access to templates, which is accessed via HTTPS, and regional buckets for access to assets within the region, such as Lambda code. You will need:

* One global bucket that is access via the http end point. AWS CloudFormation templates are stored here. Ex. "mybucket"
* One regional bucket for each region where you plan to deploy using the name of the global bucket as the root, and suffixed with the region name. Ex. "mybucket-us-east-1"
* The regional bucket should be public

**Build the solution**

From the *deployment* folder in your cloned repo, run build-s3-dist.sh, passing the root name of your bucket (ex. mybucket), name of the solution i.e. aws-innovation-sandbox and the version you are building (ex. v1.3.3). We recommend using a similar version based on the version downloaded from GitHub (ex. GitHub: v1.3.3, your build: v1.3.3.mybuild)

```
chmod +x build-s3-dist.sh
build-s3-dist.sh <bucketname> aws-innovation-sandbox <version>
```


**Upload to your buckets**

Upload the InnovationSandbox.template to your global bucket.

Upload the files listed below to your regional bucket in the following pattern:

```
s3://mybucket-us-east-1/aws-innovation-sandbox/v1.3.3/<file name> (lambda Code)
```

* `InnovationSandboxManagementAccount.ts` 
* `InnovationSandboxSbxAccount.ts`
* `InnovationSandboxTransitGatewaySetup.ts` 
* `innovation_sbx_guardrails_scp.json`
* `innovation_sbx_network_controls_scp.json`
* `InnovationSandbox.zip`

## Deploy

See the [AWS Innovation Sandbox Implementation Guide](https://docs.aws.amazon.com/solutions/latest/aws-innovation-sandbox/automated-deployment.html) for deployment instructions, using the CloudFormation templates published to your own S3.

## CDK Documentation

AWS Innovation Sandbox templates are generated using AWS CDK, for further information on CDK please refer to the [documentation](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html)


***

Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://www.apache.org/licenses/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.
