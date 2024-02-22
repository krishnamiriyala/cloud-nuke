import argparse
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

from azure.identity import DefaultAzureCredential
from azure.mgmt.recoveryservices import RecoveryServicesClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.locks import ManagementLockClient
from azure.mgmt.network import NetworkManagementClient
from azure.core.exceptions import HttpResponseError


def check_resource_group_lock(lock_client, resource_group, log):
    locks = list(
        lock_client.management_locks.list_at_resource_group_level(resource_group.name)
    )
    if locks:
        log(
            f"Resource group {resource_group.name} has {len(locks)} lock(s): {[l.name for l in locks]}"
        )
    else:
        log(f"Resource group {resource_group.name} does not have any locks.")
    return locks


def delete_resource_group(
    resource_client, recovery_client, network_client, resource_group, log
):
    for nsg in network_client.network_security_groups.list(resource_group.name):
        print(f"Deleting network security group '{nsg.name}'...")
        try:
            network_client.network_security_groups.begin_delete(
                resource_group.name, nsg.name
            ).wait()
            print(f"Network security group '{nsg.name}' deleted.")
        except HttpResponseError as ex:
            print(f"Failed to delete network security group '{nsg.name}': {ex.message}")

    recovery_vaults = list(
        recovery_client.vaults.list_by_resource_group(resource_group.name)
    )
    for vault in recovery_vaults:
        log(
            f"Deleting recovery vault {vault.name} in resource group {resource_group.name}"
        )
        try:
            recovery_client.vaults.delete(resource_group.name, vault.name)
            log(
                f"Deleted recovery vault {vault.name} in resource group {resource_group.name} successfully"
            )
        except Exception as e:
            log(
                f"Deleting recovery vault {vault.name} in resource group {resource_group.name} failed: {str(e)}"
            )

    log(f"Deleting resource group {resource_group.name}")
    try:
        delete_async_operation = resource_client.resource_groups.begin_delete(
            resource_group.name
        )
        delete_async_operation.wait()
        log(f"Deleted resource group {resource_group.name} successfully")
    except Exception as e:
        log(f"Deleting resource group {resource_group.name} failed: {str(e)}")


def delete_resource_groups(
    resource_client,
    lock_client,
    recovery_client,
    network_client,
    live_action,
    num_workers,
    prefix,
):
    resource_groups = list(resource_client.resource_groups.list())
    if live_action:
        log = print
    else:

        def log(text):
            return print(f"[DRYRUN] {text}")

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        filtered_resource_groups = []
        for resource_group in resource_groups:
            if prefix is not None and not resource_group.name.startswith(prefix):
                log(
                    f"Skipping resource group {resource_group.name} not starting with {prefix}."
                )
                continue

            if check_resource_group_lock(lock_client, resource_group, log):
                log(f"Skipping deletion {resource_group.name} due to locks.")
                continue

            if not live_action:
                log(f"Skipping deletion {resource_group.name} due to dry run.")
                continue
            filtered_resource_groups.append(resource_group)

        futures = [
            executor.submit(
                delete_resource_group,
                resource_client,
                recovery_client,
                network_client,
                resource_group,
                log,
            )
            for resource_group in filtered_resource_groups
        ]

        for future in futures:
            future.result()


def main():
    parser = argparse.ArgumentParser(
        description="Delete Azure resource groups.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("subscription_id", type=str, help="Azure Subscription ID")
    parser.add_argument(
        "--live-action",
        action="store_true",
        help="Specify to perform the deletion instead of dry-run",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=multiprocessing.cpu_count(),
        help="Number of worker threads",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        help="Prefix to filter resource groups by name",
        default="foobar",
    )

    args = parser.parse_args()

    # Authenticate using the default Azure credentials
    credential = DefaultAzureCredential()

    resource_client = ResourceManagementClient(credential, args.subscription_id)
    lock_client = ManagementLockClient(credential, args.subscription_id)
    recovery_client = RecoveryServicesClient(credential, args.subscription_id)
    network_client = NetworkManagementClient(credential, args.subscription_id)

    delete_resource_groups(
        resource_client,
        lock_client,
        recovery_client,
        network_client,
        args.live_action,
        args.num_workers,
        args.prefix,
    )


if __name__ == "__main__":
    main()
