import argparse
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobServiceClient


def delete_blobs_in_storage_containers(subscription_id, prefix, live_action):
    if live_action:
        log = print
    else:

        def log(text):
            return print(f"[DRYRUN] {text}")

    try:
        # Create a DefaultAzureCredential object
        credential = DefaultAzureCredential()

        # Create a ResourceManagementClient using the default credential
        resource_client = ResourceManagementClient(credential, subscription_id)

        # List all resource groups in the subscription
        resource_groups = resource_client.resource_groups.list()

        # Iterate over each resource group
        for resource_group in resource_groups:
            log(f"Scanning resource group {resource_group.name}")
            # Create a StorageManagementClient using the default credential
            storage_client = StorageManagementClient(credential, subscription_id)

            # List all storage accounts in the resource group
            storage_accounts = storage_client.storage_accounts.list_by_resource_group(
                resource_group.name
            )

            # Iterate over each storage account
            for account in storage_accounts:
                # Get the account keys
                keys = storage_client.storage_accounts.list_keys(
                    resource_group.name, account.name
                )

                # Create a BlobServiceClient using the account name and key
                blob_service_client = BlobServiceClient(
                    account_url=f"https://{account.name}.blob.core.windows.net",
                    credential=keys.keys[0].value,
                )

                # List containers in the storage account
                containers = blob_service_client.list_containers()

                # Print the name of each container
                for container in containers:
                    # Get the container client
                    container_client = blob_service_client.get_container_client(
                        container.name
                    )

                    # List blobs with the specified prefix in the container
                    blob_list = container_client.list_blobs(name_starts_with=prefix)
                    # Print the name of each blob
                    for blob in blob_list:
                        log(
                            f"Deleting blob {account.name}/{container.name}/{blob.name}"
                        )
                        if live_action:
                            blob_client = container_client.get_blob_client(blob.name)
                            blob_client.delete_blob()

    except Exception as e:
        log(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="List containers in storage accounts within all resource groups."
    )
    parser.add_argument("--subscription_id", help="Azure subscription ID")
    parser.add_argument("--prefix", help="Prefix to filter containers")
    parser.add_argument(
        "--live-action", action="store_true", help="Perform deletion action on blobs"
    )

    args = parser.parse_args()

    delete_blobs_in_storage_containers(
        args.subscription_id, args.prefix, args.live_action
    )

    if not args.live_action:
        rerun_live = input("Do you want to rerun in live mode? (Y/N): ").strip().lower()
        if rerun_live == "y":
            args.live_action = True
            delete_blobs_in_storage_containers(
                args.subscription_id, args.prefix, args.live_action
            )


if __name__ == "__main__":
    main()
