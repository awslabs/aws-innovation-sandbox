
import cdk = require('@aws-cdk/core');
import ec2 = require('@aws-cdk/aws-ec2');


export class InnovationSandboxTransitGatewaySetup extends cdk.Stack {

  public readonly response: string;
  constructor(scope: cdk.App, id: string, props?: any, s?: string) {
    super(scope, id);


    const TGID = new cdk.CfnParameter(this, "TGID", {
      type: "String",
      description: "TGID"
    });

    const EGREEATTCH = new cdk.CfnParameter(this, "EGREEATTCH", {
      type: "String",
      description: "EGREEATTCH"
    });

    const SBXTGATTCH = new cdk.CfnParameter(this, "SBXTGATTCH", {
      type: "String",
      description: "SBXTGATTCH"
    });


    
    const TGRouteTableTowardsSBX = new ec2.CfnTransitGatewayRouteTable(this, "RouteTowardsSBX", {
      transitGatewayId: TGID.valueAsString,
      tags: [{
        key: 'Name',
        value: "Route Towards SBX - Innovation Sandbox"
      }],
    }); 
    const TransitGatewayRouteTableTowardsSBX = new ec2.CfnTransitGatewayRoute(this, "RouteFromEgressVPCToSbxForCallBack", {
      transitGatewayRouteTableId: TGRouteTableTowardsSBX.ref,
      transitGatewayAttachmentId: SBXTGATTCH.valueAsString,
      destinationCidrBlock: "192.168.0.0/16"
    });
    const TGRouteTableAssociationForEGRESSVPC = new ec2.CfnTransitGatewayRouteTableAssociation(this, 'AssocForEgressVPC', {
      transitGatewayAttachmentId: EGREEATTCH.valueAsString,
      transitGatewayRouteTableId: TransitGatewayRouteTableTowardsSBX.transitGatewayRouteTableId,
    });


    const TGRouteTableTowardsIGW = new ec2.CfnTransitGatewayRouteTable(this, "RouteTowardsIGW", {
      transitGatewayId: TGID.valueAsString,
      tags: [{
        key: 'Name',
        value: "Route Towards IGW - Innovation Sandbox"
      }],
    }); 
    const TransitGatewayRouteTableTowardsIGW = new ec2.CfnTransitGatewayRoute(this, "RouteFromSbxToEgressVPC", {
      transitGatewayRouteTableId: TGRouteTableTowardsIGW.ref,
      transitGatewayAttachmentId: EGREEATTCH.valueAsString,
      destinationCidrBlock: "0.0.0.0/0"
    });
    const TGRouteTableAssociationForSBXVPC = new ec2.CfnTransitGatewayRouteTableAssociation(this, 'AssocForSbx', {
      transitGatewayAttachmentId: SBXTGATTCH.valueAsString,
      transitGatewayRouteTableId: TransitGatewayRouteTableTowardsIGW.transitGatewayRouteTableId,
    });

  }

}
