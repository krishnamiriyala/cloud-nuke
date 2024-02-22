import argparse
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

from boto3_client import s3_client_iterator


def delete_objects(s3_client, bucket_name, prefix, live_action, num_workers):
    if live_action:
        log = print
    else:

        def log(text):
            return print(f"[DRYRUN] {text}")

    paginator = s3_client.get_paginator("list_objects_v2")
    operation_parameters = {"Bucket": bucket_name}
    page_iterator = paginator.paginate(**operation_parameters)

    def delete_object(key):
        if not prefix or obj["Key"].startswith(prefix):
            log(f"{bucket_name}/{key} Deleting object ...")
            if live_action:
                s3_client.delete_object(Bucket=bucket_name, Key=key)
            else:
                log(
                    f"{bucket_name}/{obj['Key']} Skipping object (Prefix does not match) ..."
                )

    try:
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for page in page_iterator:
                for obj in page["Contents"]:
                    futures.append(executor.submit(delete_object, obj["Key"]))
            for future in futures:
                future.result()

    except Exception as e:
        print(e)

    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if "Contents" not in response or not response["Contents"]:
            s3_client.delete_bucket(Bucket=bucket_name)
    except Exception as e:
        print(e)


def delete_buckets(s3_client, prefix, live_action, num_workers):
    # Retrieve bucket names
    response = s3_client.list_buckets()
    buckets = [bucket["Name"] for bucket in response["Buckets"]]

    # Delete objects in each bucket
    for bucket_name in buckets:
        delete_objects(s3_client, bucket_name, prefix, live_action, num_workers)


def main():
    parser = argparse.ArgumentParser(description="Delete S3 buckets")
    parser.add_argument(
        "--num-workers",
        type=int,
        default=multiprocessing.cpu_count(),
        help="Number of worker threads",
    )
    parser.add_argument("--prefix", help="Prefix to check for in object names")
    parser.add_argument(
        "--live-action",
        action="store_true",
        help="Perform live actions instead of dry run",
    )
    args = parser.parse_args()

    for s3_client in s3_client_iterator():
        delete_buckets(s3_client, args.prefix, args.live_action, args.num_workers)


if __name__ == "__main__":
    main()
