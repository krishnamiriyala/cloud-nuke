#!/usr/bin/env python3
import argparse

from boto3_client import ec2_client_iterator


def list_amis(ec2_client, owner_id):
    return ec2_client.describe_images(Owners=[owner_id])["Images"]


def delete_amis(ec2_client, amis, prefix, live_action=False):
    log = print
    if not live_action:
        log = lambda text: print(f"[DRYRUN] {text}")

    for ami in amis:
        if ami["Name"].startswith(prefix):
            if live_action:
                log(f"Deleting AMI: {ami['ImageId']} (Name: {ami['Name']})")
                ec2_client.deregister_image(ImageId=ami["ImageId"])
            else:
                log(f"Deleting AMI: {ami['ImageId']} (Name: {ami['Name']})")
        else:
            if live_action:
                log(f"Skipped AMI: {ami['ImageId']} (Name: {ami['Name']})")


def main():
    parser = argparse.ArgumentParser(
        description="Delete AMIs with a given prefix in their name"
    )
    parser.add_argument("owner_id", help="Owner ID of the AMIs")
    parser.add_argument("prefix", help="Prefix to check for in AMI names")
    parser.add_argument(
        "--live-action",
        action="store_true",
        help="Perform live actions instead of dry run",
    )
    args = parser.parse_args()

    for ec2_client in ec2_client_iterator():
        delete_amis(
            ec2_client,
            list_amis(ec2_client, args.owner_id),
            args.prefix,
            args.live_action,
        )


if __name__ == "__main__":
    main()
