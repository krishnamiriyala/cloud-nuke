#!/usr/bin/env python3
import argparse

from boto3_client import ec2_client_iterator


def list_amis(ec2_client, owner_id):
    return ec2_client.describe_images(Owners=[owner_id])["Images"]


def delete_amis(ec2_client, region, amis, prefix, live_action=False):
    if live_action:
        log = print
    else:

        def log(text):
            return print(f"[DRYRUN] {text}")

    for ami in amis:
        if ami["Name"].startswith(prefix):
            log(f"{region}/{ami['Name']} {ami['Name']} Deleting ...")
            if live_action:
                ec2_client.deregister_image(ImageId=ami["ImageId"])
        else:
            if live_action:
                log(f"{region}/{ami['Name']} {ami['Name']} Skipping ...")


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

    for ec2_client, region in ec2_client_iterator():
        delete_amis(
            ec2_client,
            region,
            list_amis(ec2_client, args.owner_id),
            args.prefix,
            args.live_action,
        )

    if not args.live_action:
        rerun_live = input("Do you want to rerun in live mode? (Y/N): ").strip().lower()
        if rerun_live == "y":
            args.live_action = True
            for ec2_client, region in ec2_client_iterator():
                delete_amis(
                    ec2_client,
                    region,
                    list_amis(ec2_client, args.owner_id),
                    args.prefix,
                    args.live_action,
                )


if __name__ == "__main__":
    main()
