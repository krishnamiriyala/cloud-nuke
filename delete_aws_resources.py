#!/usr/bin/env python3
import boto3


def list_unused_snapshots(ec2_client):
    try:
        # Describe private images
        response = ec2_client.describe_images(
            Filters=[{"Name": "is-public", "Values": ["False"]}]
        )

        # Cache snapshot IDs used by private images
        snapshot_ids_in_use = set()
        for image in response["Images"]:
            for block_device_mapping in image.get("BlockDeviceMappings", []):
                ebs = block_device_mapping.get("Ebs")
                if ebs and "SnapshotId" in ebs:
                    snapshot_ids_in_use.add(ebs["SnapshotId"])
                    print(snapshot_ids_in_use)

        # Describe all snapshots
        response = ec2_client.describe_snapshots(OwnerIds=["self"])

        # Find unused snapshots
        unused_snapshots = []
        for snapshot in response["Snapshots"]:
            snapshot_id = snapshot["SnapshotId"]
            if snapshot_id not in snapshot_ids_in_use:
                unused_snapshots.append(snapshot_id)

        return unused_snapshots
    except Exception as e:
        print(f"Error listing unused snapshots: {e}")
        return []


def delete_unused_snapshots(ec2_client, snapshot_ids):
    for snapshot_id in snapshot_ids:
        try:
            ec2_client.delete_snapshot(SnapshotId=snapshot_id)
            print(f"Snapshot {snapshot_id} deleted successfully.")
        except Exception as e:
            print(f"Error deleting snapshot {snapshot_id}: {e}")


def list_unused_volumes(ec2_client):
    try:
        response = ec2_client.describe_volumes()
        volumes = [
            volume["VolumeId"]
            for volume in response["Volumes"]
            if not volume.get("Attachments")
        ]
        return volumes
    except Exception as e:
        print(f"Error listing volumes: {e}")
        return []


def delete_unused_volumes(ec2_client, volume_ids):
    for volume_id in volume_ids:
        try:
            ec2_client.delete_volume(VolumeId=volume_id)
            print(f"Volume {volume_id} deleted successfully.")
        except Exception as e:
            print(f"Error deleting volume {volume_id}: {e}")


def list_unused_eips(ec2_client):
    try:
        response = ec2_client.describe_addresses()
        eips = [
            eip["AllocationId"]
            for eip in response["Addresses"]
            if not eip.get("InstanceId") and not eip.get("NetworkInterfaceId")
        ]
        return eips
    except Exception as e:
        print(f"Error listing Elastic IPs: {e}")
        return []


def delete_unused_eips(ec2_client, eip_ids):
    for eip_id in eip_ids:
        try:
            ec2_client.release_address(AllocationId=eip_id)
            print(f"Elastic IP {eip_id} released successfully.")
        except Exception as e:
            print(f"Error releasing Elastic IP {eip_id}: {e}")


def list_unused_placement_groups(ec2_client):
    try:
        response = ec2_client.describe_placement_groups()
        placement_groups = [
            pg["GroupName"]
            for pg in response["PlacementGroups"]
            if pg["State"] == "available"
        ]
        return placement_groups
    except Exception as e:
        print(f"Error listing unused placement groups: {e}")
        return []


def delete_unused_placement_groups(ec2_client, placement_groups):
    for pg_name in placement_groups:
        try:
            ec2_client.delete_placement_group(GroupName=pg_name)
            print(f"Placement group {pg_name} deleted successfully.")
        except Exception as e:
            print(f"Error deleting placement group {pg_name}: {e}")


def delete_aws_resources():
    # Create a Boto3 client for EC2
    ec2_client = boto3.client("ec2", region_name="us-east-1")

    # Get all AWS regions
    regions = [
        region["RegionName"] for region in ec2_client.describe_regions()["Regions"]
    ]

    # Iterate through each region
    for region in regions:

        # Create a Boto3 client for EC2 in the current region
        ec2_client = boto3.client("ec2", region_name=region)

        print(f"Deleting unused snapshots in region: {region}")
        delete_unused_snapshots(ec2_client, list_unused_snapshots(ec2_client))

    # Iterate through each region
    for region in regions:

        # Create a Boto3 client for EC2 in the current region
        ec2_client = boto3.client("ec2", region_name=region)

        print(f"Deleting unused Placement Groups in region: {region}")
        delete_unused_placement_groups(
            ec2_client, list_unused_placement_groups(ec2_client)
        )

        print(f"Deleting unused EIPs in region: {region}")
        delete_unused_eips(ec2_client, list_unused_eips(ec2_client))

        print(f"Deleting unused volumes in region: {region}")
        delete_unused_volumes(ec2_client, list_unused_volumes(ec2_client))

        print(f"Deleting VPN connections in region: {region}")
        vpn_connections = ec2_client.describe_vpn_connections()["VpnConnections"]
        vpn_connection_ids = [
            vpn_connection["VpnConnectionId"] for vpn_connection in vpn_connections
        ]

        # Delete VPN connections
        for vpn_connection_id in vpn_connection_ids:
            print(f"Deleting VPN connection {vpn_connection_id} in region {region}")
            try:
                ec2_client.delete_vpn_connection(VpnConnectionId=vpn_connection_id)
            except Exception as e:
                print(e)

        print(f"Deleting VPC peering connections in region: {region}")
        peering_connections = ec2_client.describe_vpc_peering_connections()[
            "VpcPeeringConnections"
        ]
        peering_connection_ids = [
            peering_connection["VpcPeeringConnectionId"]
            for peering_connection in peering_connections
        ]

        # Delete VPC peering connections
        for peering_connection_id in peering_connection_ids:
            print(
                f"Deleting VPC peering connection {peering_connection_id} in region {region}"
            )
            try:
                ec2_client.delete_vpc_peering_connection(
                    VpcPeeringConnectionId=peering_connection_id
                )
            except Exception as e:
                print(e)

        # Fetching IDs of all transit gateway attachments
        response = ec2_client.describe_transit_gateway_attachments()
        attachment_ids = [
            attachment["TransitGatewayAttachmentId"]
            for attachment in response["TransitGatewayAttachments"]
        ]

        # Iterate through each attachment and delete it
        for attachment_id in attachment_ids:
            print(f"Deleting attachment with ID: {attachment_id}")
            try:
                ec2_client.delete_transit_gateway_vpc_attachment(
                    TransitGatewayAttachmentId=attachment_id
                )
            except Exception as e:
                print(e)
        try:
            response = ec2_client.describe_vpn_gateways()
            for vgw_id in [vgw["VpnGatewayId"] for vgw in response["VpnGateways"]]:
                try:
                    ec2_client.delete_vpn_gateway(VpnGatewayId=vgw_id)
                    print(f"Virtual Private Gateway {vgw_id} deleted successfully.")
                except Exception as e:
                    print(f"Error deleting Virtual Private Gateway {vgw_id}: {e}")
        except Exception as e:
            print(f"Error listing Virtual Private Gateways: {e}")

        # Fetching IDs of all transit gateways
        response = ec2_client.describe_transit_gateways()
        gateway_ids = [
            gateway["TransitGatewayId"] for gateway in response["TransitGateways"]
        ]

        # Iterate through each transit gateway and delete it
        for gateway_id in gateway_ids:
            print(f"Deleting transit gateway with ID: {gateway_id}")
            try:
                ec2_client.delete_transit_gateway(TransitGatewayId=gateway_id)
            except Exception as e:
                print(e)

        # Fetching IDs of all VPCs
        response = ec2_client.describe_vpcs()
        vpc_ids = [vpc["VpcId"] for vpc in response["Vpcs"]]

        # Iterate through each VPC and delete it
        for vpc_id in vpc_ids:
            print(f"Deleting VPC with ID: {vpc_id}")
            try:
                ec2_client.delete_vpc(VpcId=vpc_id)
            except Exception as e:
                print(e)
    # Iterate through each region
    for region in regions:
        print(f"Deleting RDS instances in region: {region}")

        # Create a Boto3 client for RDS in the current region
        rds_client = boto3.client("rds", region_name=region)

        # Fetching IDs of all RDS instances in the current region
        response = rds_client.describe_db_instances()
        instance_identifiers = [
            instance["DBInstanceIdentifier"] for instance in response["DBInstances"]
        ]

        # Iterate through each RDS instance and delete it
        for instance_identifier in instance_identifiers:
            print(f"Deleting RDS instance {instance_identifier} in region {region}")
            rds_client.delete_db_instance(
                DBInstanceIdentifier=instance_identifier, SkipFinalSnapshot=True
            )


if __name__ == "__main__":
    delete_aws_resources()
