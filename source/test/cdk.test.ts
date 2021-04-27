import { SynthUtils, expect as expectCDK, matchTemplate, MatchStyle } from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import * as invsbxmain from '../lib/InnovationSandbox';
import * as invsbxmgmt from '../lib/InnovationSandboxManagementAccount';
import * as invsbxsbx from '../lib/InnovationSandboxSbxAccount';
import * as invsbxtgw from '../lib/InnovationSandboxTransitGatewaySetup';


test('InnovationSandboxMain', () => {
    const app = new cdk.App();
    const stack = 
    new invsbxmain.InnovationSandbox(app, 'InnovationSandboxTestStack',
      {
        description: "Test",
        solutionId: "InvSbx",
        solutionTradeMarkName: "InvSbx",
        solutionProvider: "AWS",
        solutionBucket: "Sample",
        solutionName: "InvSbx",
        solutionVersion: "v1.0.0"
    }
    );
    // THEN
    expect(SynthUtils.toCloudFormation(stack)).toMatchSnapshot();
});


test('InnovationSandboxMgmt', () => {
  const app = new cdk.App();
  const stack = 
  new invsbxmgmt.InnovationSandboxManagementAccount(app, 'InnovationSandboxManagementTestStack'
  );
  // THEN
  expect(SynthUtils.toCloudFormation(stack)).toMatchSnapshot();
});

test('InnovationSandboxSbx', () => {
  const app = new cdk.App();
  const stack = 
  new invsbxsbx.InnovationSandboxSbxAccount(app, 'InnovationSandboxSbxTestStack'
  );
  // THEN
  expect(SynthUtils.toCloudFormation(stack)).toMatchSnapshot();
});

test('InnovationSandboxTgw', () => {
  const app = new cdk.App();
  const stack = 
  new invsbxtgw.InnovationSandboxTransitGatewaySetup(app, 'InnovationSandboxTgwTestStack'
  );
  // THEN
  expect(SynthUtils.toCloudFormation(stack)).toMatchSnapshot();
});