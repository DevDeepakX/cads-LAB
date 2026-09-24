import json

from .cloud_provider import SimulatorProvider

ALLOWED_COMMANDS = {
    "aws sts get-caller-identity",
    "aws iam get-user",
    "aws iam list-users",
    "aws iam list-roles",
    "aws iam get-role",
    "aws iam list-attached-user-policies",
    "aws iam list-attached-role-policies",
    "aws iam get-policy",
    "aws iam get-policy-version",
    "aws iam attach-user-policy",
    "aws iam detach-user-policy",
    "aws iam delete-access-key",
    "aws s3 ls",
    "aws s3api get-bucket-policy",
    "aws s3api get-public-access-block",
    "aws s3api get-bucket-encryption",
    "aws s3api put-public-access-block",
    "aws s3 cp",
    "aws ec2 describe-instances",
    "aws ec2 describe-security-groups",
    "aws ec2 describe-security-group-rules",
    "aws ec2 revoke-security-group-ingress",
    "aws ec2 authorize-security-group-ingress",
    "aws cloudtrail describe-trails",
    "aws cloudtrail get-trail-status",
    "aws cloudtrail lookup-events",
    "ls",
    "pwd",
    "whoami",
    "id",
    "help",
    "history",
    "clear",
    "nmap -sV 10.0.0.5",
    "netstat -an",
}

_PROVIDER = SimulatorProvider()


def _resource_config_values(config):
    if isinstance(config, str):
        try:
            return json.loads(config)
        except Exception:
            return {}
    return config or {}


def get_resource(session_id, resource_name):
    return _PROVIDER.get_resource(session_id, resource_name)


def list_resources(session_id, resource_type=None):
    return _PROVIDER.list_resources(session_id, resource_type)


def create_cloud_resource(session_id, resource_type, resource_name, region="ap-south-1", configuration=None, status="ACTIVE"):
    return _PROVIDER.create_resource(session_id, resource_type, resource_name, region=region, configuration=configuration, status=status)


def update_resource(session_id, resource_name, updates):
    return _PROVIDER.update_resource(session_id, resource_name, updates)


def delete_resource(session_id, resource_name):
    return _PROVIDER.delete_resource(session_id, resource_name)


def reset_environment(session_id):
    return _PROVIDER.reset_environment(session_id)


def list_iam_users(session_id):
    resources = list_resources(session_id, "IAM_USER")
    return [{"UserName": item["resource_name"], "Arn": f"arn:aws:iam::{session_id}:user/{item['resource_name']}"} for item in resources]


def list_iam_roles(session_id):
    resources = list_resources(session_id, "IAM_ROLE")
    return [{"RoleName": item["resource_name"], "Arn": f"arn:aws:iam::{session_id}:role/{item['resource_name']}"} for item in resources]


def list_s3_buckets(session_id):
    resources = list_resources(session_id, "S3_BUCKET")
    return [{"Name": item["resource_name"], "Region": item.get("region", "ap-south-1")} for item in resources]


def get_s3_bucket_policy(session_id, bucket_name):
    resource = get_resource(session_id, bucket_name)
    config = _resource_config_values(resource.get("configuration") if resource else {})
    statement = config.get("policy", {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": f"arn:aws:s3:::{bucket_name}/*"}],
    })
    return {"Bucket": bucket_name, "Policy": statement}


def list_s3_objects(session_id, bucket_name):
    resource = get_resource(session_id, bucket_name)
    config = _resource_config_values(resource.get("configuration") if resource else {})
    return config.get("objects", [])


def describe_instances(session_id):
    resources = list_resources(session_id, "EC2_INSTANCE")
    return [{"InstanceId": item["resource_name"], "State": item.get("status", "running")} for item in resources]


def describe_security_groups(session_id):
    resources = list_resources(session_id, "SECURITY_GROUP")
    return [{"GroupName": item["resource_name"], "VpcId": "vpc-cads-001"} for item in resources]


def get_cloudtrail_status(session_id):
    return {"IsLogging": True, "TrailARN": f"arn:aws:cloudtrail:{session_id}:trail/cads-trail"}


def get_guardduty_status(session_id):
    return {"Status": "Enabled", "FindingCount": 1}


def create_cloud_event(session_id, service, event_name, actor="student", resource_type="UNKNOWN", source_ip="10.0.0.15", region="ap-south-1", outcome="SUCCESS", severity="MEDIUM", metadata=None):
    metadata = metadata or {}
    return _PROVIDER.create_event(
        session_id,
        service=service,
        event_name=event_name,
        actor=actor,
        resource_type=resource_type,
        outcome=outcome,
        severity=severity,
        resource_name=metadata.get("resource_name") if isinstance(metadata, dict) else None,
        metadata=metadata,
    )


def list_events(session_id):
    return _PROVIDER.list_events(session_id)


def is_allowed_command(command: str) -> bool:
    command = (command or "").strip()
    if not command:
        return False
    if any(token in command for token in (";", "&&", "|", ">", "<")):
        return False
    for allowed in ALLOWED_COMMANDS:
        if command.startswith(allowed):
            return True
    return False
