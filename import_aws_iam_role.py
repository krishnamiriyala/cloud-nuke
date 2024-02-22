import argparse
import boto3
import json


def import_role_permissions(role_name):
    # Initialize IAM client for the target account
    target_iam = boto3.client("iam")

    # Read assume role policy from JSON file
    with open("trust_policy.json", "r") as trust_file:
        trust_policy = json.load(trust_file)

    # Read attached policy ARNs from text file
    with open("attached_policies.txt", "r") as policies_file:
        attached_policies = [line.strip() for line in policies_file]

    # Read inline policies and their permissions from JSON file
    with open("inline_policies_permissions.json", "r") as inline_file:
        inline_policies_permissions = json.load(inline_file)

    # Create the role in the target account
    target_role = target_iam.create_role(
        RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust_policy)
    )

    # Attach policies to the target role
    for policy_arn in attached_policies:
        target_iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)

    # Create inline policies for the target role
    for policy_name, policy_document in inline_policies_permissions.items():
        target_iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
        )

    print("Role imported successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import IAM role details and permissions."
    )
    parser.add_argument("--role", required=True, help="Name of the IAM role to import.")
    args = parser.parse_args()

    import_role_permissions(args.role)
