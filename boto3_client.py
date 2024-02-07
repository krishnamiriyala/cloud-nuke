import boto3


def ec2_client_iterator():
    for region in boto3.client("ec2", region_name="us-east-1").describe_regions()[
        "Regions"
    ]:
        yield boto3.client("ec2", region_name=region["RegionName"])
