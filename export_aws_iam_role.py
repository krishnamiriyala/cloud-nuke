import argparse
import boto3
import json


def export_role_permissions(role_name):
    # Initialize IAM client for the source account
    source_iam = boto3.client("iam")

    # Get the source role's details
    try:
        source_role = source_iam.get_role(RoleName=role_name)
    except source_iam.exceptions.NoSuchEntityException:
        print(f"Role '{role_name}' not found in the source account.")
        return

    # Extract the assume role policy
    trust_policy = source_role["Role"]["AssumeRolePolicyDocument"]

    # Extract attached policy ARNs if available
    if "AttachedPolicies" in source_role["Role"]:
        attached_policies = [
            policy["PolicyArn"] for policy in source_role["Role"]["AttachedPolicies"]
        ]
    else:
        attached_policies = []

    # Extract inline policies and their permissions
    inline_policies_permissions = {}
    for policy_name in source_iam.list_role_policies(RoleName=role_name)["PolicyNames"]:
        permissions = source_iam.get_role_policy(
            RoleName=role_name, PolicyName=policy_name
        )["PolicyDocument"]
        print(permissions)
        inline_policies_permissions[policy_name] = permissions

    # Write assume role policy to JSON file
    with open("trust_policy.json", "w") as trust_file:
        json.dump(trust_policy, trust_file)

    # Write attached policy ARNs to a text file
    with open("attached_policies.txt", "w") as policies_file:
        for arn in attached_policies:
            policies_file.write(arn + "\n")

    # Write inline policies and their permissions to JSON file
    with open("inline_policies_permissions.json", "w") as inline_file:
        json.dump(inline_policies_permissions, inline_file)

    print("Role details exported successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export IAM role details and permissions."
    )
    parser.add_argument("--role", required=True, help="Name of the IAM role to export.")
    args = parser.parse_args()

    export_role_permissions(args.role)
