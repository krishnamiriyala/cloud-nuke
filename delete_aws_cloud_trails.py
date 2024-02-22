import argparse

from boto3_client import cloudtrail_client_iterator


def delete_cloudtrails(cloudtrail_client, region, prefix, live_action):
    if live_action:
        log = print
    else:

        def log(text):
            return print(f"[DRYRUN] {text}")

    # Retrieve all trails
    response = cloudtrail_client.describe_trails()
    trails = response.get("trailList", [])

    # Delete each trail
    for trail in trails:
        trail_name = trail["Name"]
        if not prefix or trail_name.startswith(prefix):
            log(f"{region}/{trail_name} Deleting ...")
            if live_action:
                try:
                    cloudtrail_client.delete_trail(Name=trail_name)
                except Exception as e:
                    print(e)
        else:
            log(f"{region}/{trail_name} Skipping (Prefix does not match)...")


def main():
    parser = argparse.ArgumentParser(description="Delete CloudTrail trails")
    parser.add_argument("--prefix", help="Prefix to check for in trail names")
    parser.add_argument(
        "--live-action",
        action="store_true",
        help="Perform live actions instead of dry run",
    )
    args = parser.parse_args()

    for cloudtrail_client, region in cloudtrail_client_iterator():
        delete_cloudtrails(cloudtrail_client, region, args.prefix, args.live_action)


if __name__ == "__main__":
    main()
