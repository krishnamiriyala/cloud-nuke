#!/usr/bin/env python3
import argparse

from boto3_client import ec2_client_iterator


def delete_key_pairs(ec2_client, region, prefix, live_action):
    if live_action:
        log = print
    else:

        def log(text):
            return print(f"[DRYRUN] {text}")

    key_pairs = ec2_client.describe_key_pairs()["KeyPairs"]

    for key_pair in key_pairs:
        key_name = key_pair["KeyName"]
        if key_name.startswith(prefix):
            log(f"{region}/{key_name} Deleting Key Pair ...")
            if live_action:
                ec2_client.delete_key_pair(KeyName=key_name)


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
        delete_key_pairs(ec2_client, region, args.prefix, args.live_action)

    if not args.live_action:
        rerun_live = input("Do you want to rerun in live mode? (Y/N): ").strip().lower()
        if rerun_live == "y":
            args.live_action = True
            for ec2_client, region in ec2_client_iterator():
                delete_key_pairs(ec2_client, region, args.prefix, args.live_action)


if __name__ == "__main__":
    main()
