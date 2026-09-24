import json
import shlex

from app.security.auth import enforce_safe_command

from .cloud_provider import SimulatorProvider
from .event_processor import EventProcessor


class CommandEngine:
    def __init__(self, provider=None):
        self.provider = provider or SimulatorProvider()
        if getattr(self.provider, "_event_processor", None) is None:
            self.provider.set_event_processor(EventProcessor(self.provider))

    @staticmethod
    def _build_output(data, *, kind="text"):
        if kind == "json":
            return json.dumps(data, indent=2, sort_keys=True)
        if isinstance(data, str):
            return data
        return json.dumps(data, indent=2, sort_keys=True)

    @staticmethod
    def _extract_flag(parts, flag_name, default=None):
        for idx, token in enumerate(parts):
            if token.startswith(f"{flag_name}="):
                return token.split("=", 1)[1]
            if token == flag_name and idx + 1 < len(parts):
                return parts[idx + 1]
        return default

    def parse(self, command: str):
        cleaned = enforce_safe_command(command)
        parts = shlex.split(cleaned) if cleaned else []
        if not parts:
            return {"handler": None, "parts": [], "name": None, "raw": cleaned, "supported": False}

        lookup = {
            "aws sts get-caller-identity": "sts.get-caller-identity",
            "aws iam get-user": "iam.get-user",
            "aws iam list-users": "iam.list-users",
            "aws iam list-roles": "iam.list-roles",
            "aws iam get-role": "iam.get-role",
            "aws iam list-attached-user-policies": "iam.list-attached-user-policies",
            "aws iam list-attached-role-policies": "iam.list-attached-role-policies",
            "aws iam get-policy": "iam.get-policy",
            "aws iam get-policy-version": "iam.get-policy-version",
            "aws iam attach-user-policy": "iam.attach-user-policy",
            "aws iam detach-user-policy": "iam.detach-user-policy",
            "aws iam delete-access-key": "iam.delete-access-key",
            "aws s3 ls": "s3.list",
            "aws s3api get-bucket-policy": "s3.get_bucket_policy",
            "aws s3api get-public-access-block": "s3.get_public_access_block",
            "aws s3api get-bucket-encryption": "s3.get_bucket_encryption",
            "aws s3api put-public-access-block": "s3.put_public_access_block",
            "aws s3 cp": "s3.copy_object",
            "aws ec2 describe-instances": "ec2.describe-instances",
            "aws ec2 describe-security-groups": "ec2.describe-security-groups",
            "aws ec2 describe-security-group-rules": "ec2.describe-security-group-rules",
            "aws ec2 revoke-security-group-ingress": "ec2.revoke-security-group-ingress",
            "aws ec2 authorize-security-group-ingress": "ec2.authorize-security-group-ingress",
            "aws cloudtrail describe-trails": "cloudtrail.describe-trails",
            "aws cloudtrail get-trail-status": "cloudtrail.get-trail-status",
            "aws cloudtrail lookup-events": "cloudtrail.lookup-events",
        }

        key = None
        for n in (4, 3, 2):
            if len(parts) >= n:
                prefix = " ".join(parts[:n])
                if prefix in lookup:
                    key = lookup[prefix]
                    break

        name = " ".join(parts[:3]) if len(parts) >= 3 else " ".join(parts)
        return {"raw": cleaned, "parts": parts, "name": name, "handler": key, "supported": key is not None}

    def execute(self, session_id, command: str):
        if not session_id:
            return {"status": "denied", "output": "CADS Simulator: Session is required to execute command actions.", "event": None}

        payload = self.parse(command)
        if not payload["supported"]:
            return {"status": "unsupported", "output": "CADS Simulator: Command not supported in this lab environment.", "event": None, "command": payload["raw"]}

        handler = getattr(self, f"_handle_{payload['handler'].replace('.', '_').replace('-', '_')}", None)
        if handler is None:
            return {"status": "unsupported", "output": "CADS Simulator: Command not supported in this lab environment.", "event": None, "command": payload["raw"]}

        return handler(session_id, payload)

    def _handle_sts_get_caller_identity(self, session_id, parsed):
        payload = {"UserId": "CADS-STUDENT", "Account": "CADS-000001", "Arn": f"arn:aws:iam::CADS-000001:user/student-{session_id[:8]}"}
        self.provider.create_event(session_id, "STS", "GetCallerIdentity", actor="student", resource_type="IAM_USER", outcome="SUCCESS", severity="LOW", metadata={"account": "CADS-000001"})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "STS", "event_name": "GetCallerIdentity"}}

    def _handle_iam_get_user(self, session_id, parsed):
        name = self._extract_flag(parsed["parts"], "--user-name")
        users = self.provider.list_resources(session_id, "IAM_USER")
        user_res = next((u for u in users if u["resource_name"] == name), users[0] if users else None)
        user_name = user_res["resource_name"] if user_res else (name or "student-user")
        config = (user_res or {}).get("configuration", {})
        payload = {
            "User": {
                "UserName": user_name,
                "UserId": config.get("user_id", f"AIDA{user_name.upper()}CADS"),
                "Arn": config.get("arn", f"arn:aws:iam::CADS-000001:user/{user_name}"),
                "Path": "/",
                "CreateDate": "2026-09-24T08:00:00Z",
            }
        }
        self.provider.create_event(session_id, "IAM", "GetUser", actor="student", resource_type="IAM_USER", outcome="SUCCESS", severity="LOW", resource_name=user_name, metadata={"user_name": user_name})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "IAM", "event_name": "GetUser"}}

    def _handle_iam_list_users(self, session_id, parsed):
        users = self.provider.list_resources(session_id, "IAM_USER")
        payload = {"Users": [{"UserName": item["resource_name"], "Arn": f"arn:aws:iam::CADS-000001:user/{item['resource_name']}"} for item in users] or [{"UserName": "student-user", "Arn": "arn:aws:iam::CADS-000001:user/student-user"}]}
        self.provider.create_event(session_id, "IAM", "ListUsers", actor="student", resource_type="IAM_USER", outcome="SUCCESS", severity="LOW", metadata={"count": len(payload["Users"])})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "IAM", "event_name": "ListUsers"}}

    def _handle_iam_list_roles(self, session_id, parsed):
        roles = self.provider.list_resources(session_id, "IAM_ROLE")
        payload = {"Roles": [{"RoleName": role["resource_name"], "Arn": f"arn:aws:iam::CADS-000001:role/{role['resource_name']}"} for role in roles]}
        self.provider.create_event(session_id, "IAM", "ListRoles", actor="student", resource_type="IAM_ROLE", outcome="SUCCESS", severity="LOW", metadata={"count": len(payload["Roles"])})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "IAM", "event_name": "ListRoles"}}

    def _handle_iam_get_role(self, session_id, parsed):
        name = self._extract_flag(parsed["parts"], "--role-name", "cads-dev-role")
        payload = {"Role": {"RoleName": name, "Arn": f"arn:aws:iam::CADS-000001:role/{name}", "AssumeRolePolicyDocument": {"Statement": [{"Effect": "Allow", "Principal": {"AWS": "*"}}]}}}
        self.provider.create_event(session_id, "IAM", "GetRole", actor="student", resource_type="IAM_ROLE", outcome="SUCCESS", severity="MEDIUM", metadata={"role": name})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "IAM", "event_name": "GetRole"}}

    def _handle_iam_list_attached_user_policies(self, session_id, parsed):
        user_name = self._extract_flag(parsed["parts"], "--user-name")
        users = self.provider.list_resources(session_id, "IAM_USER")
        user_res = next((u for u in users if u["resource_name"] == user_name), users[0] if users else None)
        config = (user_res or {}).get("configuration", {})
        attached = config.get("attached_policies", ["ExcessiveDeveloperPolicy"])
        policy_list = [{"PolicyName": p, "PolicyArn": f"arn:aws:iam::aws:policy/{p}" if p == "AdministratorAccess" else f"arn:aws:iam::CADS-000001:policy/{p}"} for p in attached]
        payload = {"AttachedPolicies": policy_list}
        self.provider.create_event(session_id, "IAM", "ListAttachedUserPolicies", actor="student", resource_type="IAM_USER", outcome="SUCCESS", severity="LOW", resource_name=user_res["resource_name"] if user_res else user_name, metadata={"user_name": user_name, "policy_count": len(policy_list)})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "IAM", "event_name": "ListAttachedUserPolicies"}}

    def _handle_iam_list_attached_role_policies(self, session_id, parsed):
        payload = {"AttachedPolicies": [{"PolicyName": "AdministratorAccess", "PolicyArn": "arn:aws:iam::aws:policy/AdministratorAccess"}]}
        self.provider.create_event(session_id, "IAM", "ListAttachedRolePolicies", actor="student", resource_type="IAM_POLICY", outcome="SUCCESS", severity="MEDIUM", metadata={"policy_count": 1})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "IAM", "event_name": "ListAttachedRolePolicies"}}

    def _handle_iam_get_policy(self, session_id, parsed):
        policy_arn = self._extract_flag(parsed["parts"], "--policy-arn", "arn:aws:iam::CADS-000001:policy/ExcessiveDeveloperPolicy")
        policy_name = policy_arn.split("/")[-1]
        policies = self.provider.list_resources(session_id, "IAM_POLICY")
        pol_res = next((p for p in policies if p["resource_name"] == policy_name), policies[0] if policies else None)
        payload = {
            "Policy": {
                "PolicyName": pol_res["resource_name"] if pol_res else policy_name,
                "PolicyArn": policy_arn,
                "DefaultVersionId": "v1",
                "AttachmentCount": 1,
                "IsAttachable": True,
            }
        }
        self.provider.create_event(session_id, "IAM", "GetPolicy", actor="student", resource_type="IAM_POLICY", outcome="SUCCESS", severity="MEDIUM", resource_name=pol_res["resource_name"] if pol_res else policy_name, metadata={"policy_arn": policy_arn})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "IAM", "event_name": "GetPolicy"}}

    def _handle_iam_get_policy_version(self, session_id, parsed):
        policy_arn = self._extract_flag(parsed["parts"], "--policy-arn", "arn:aws:iam::CADS-000001:policy/ExcessiveDeveloperPolicy")
        policy_name = policy_arn.split("/")[-1]
        policies = self.provider.list_resources(session_id, "IAM_POLICY")
        pol_res = next((p for p in policies if p["resource_name"] == policy_name), policies[0] if policies else None)
        doc = (pol_res or {}).get("configuration", {}).get("document", {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": ["s3:ListAllMyBuckets", "s3:GetObject", "s3:PutObject", "iam:ListUsers", "iam:GetUser", "iam:ListAttachedUserPolicies", "iam:GetPolicy", "iam:AttachUserPolicy"], "Resource": "*"}],
        })
        payload = {"PolicyVersion": {"Document": doc, "VersionId": "v1", "IsDefaultVersion": True}}
        self.provider.create_event(session_id, "IAM", "GetPolicyVersion", actor="student", resource_type="IAM_POLICY", outcome="SUCCESS", severity="HIGH", resource_name=pol_res["resource_name"] if pol_res else policy_name, metadata={"policy_arn": policy_arn})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "IAM", "event_name": "GetPolicyVersion"}}

    def _handle_iam_attach_user_policy(self, session_id, parsed):
        user_name = self._extract_flag(parsed["parts"], "--user-name", "student-user")
        policy_arn = self._extract_flag(parsed["parts"], "--policy-arn", "arn:aws:iam::aws:policy/AdministratorAccess")
        policy_name = policy_arn.split("/")[-1]
        user_res = self.provider.get_resource(session_id, user_name)
        if user_res:
            attached = list(user_res.get("configuration", {}).get("attached_policies", []))
            if policy_name not in attached:
                attached.append(policy_name)
            self.provider.update_resource(session_id, user_name, {"attached_policies": attached, "escalated": True})
        event = self.provider.create_event(session_id, "IAM", "AttachUserPolicy", actor="student", resource_type="IAM_USER", outcome="SUCCESS", severity="HIGH", resource_name=user_name, metadata={"user_name": user_name, "policy_arn": policy_arn, "action": "PrivilegeEscalation"})
        return {"status": "ok", "output": f"Attached policy {policy_arn} to user {user_name}.", "data": {"Attached": True, "PolicyArn": policy_arn}, "event": event}

    def _handle_iam_detach_user_policy(self, session_id, parsed):
        user_name = self._extract_flag(parsed["parts"], "--user-name", "student-user")
        policy_arn = self._extract_flag(parsed["parts"], "--policy-arn", "arn:aws:iam::aws:policy/AdministratorAccess")
        policy_name = policy_arn.split("/")[-1]
        user_res = self.provider.get_resource(session_id, user_name)
        if user_res:
            attached = [p for p in user_res.get("configuration", {}).get("attached_policies", []) if p != policy_name and p != "ExcessiveDeveloperPolicy"]
            self.provider.update_resource(session_id, user_name, {"attached_policies": attached, "escalated": False, "compromised": False})
        event = self.provider.create_event(session_id, "IAM", "DetachUserPolicy", actor="student", resource_type="IAM_USER", outcome="SUCCESS", severity="LOW", resource_name=user_name, metadata={"user_name": user_name, "policy_arn": policy_arn})
        return {"status": "ok", "output": f"Detached policy {policy_arn} from user {user_name}.", "data": {"Detached": True, "PolicyArn": policy_arn}, "event": event}

    def _handle_iam_delete_access_key(self, session_id, parsed):
        user_name = self._extract_flag(parsed["parts"], "--user-name", "compromised-user")
        key_id = self._extract_flag(parsed["parts"], "--access-key-id", "AKIAEXAMPLEROOTKEY")
        user_res = self.provider.get_resource(session_id, user_name)
        if user_res:
            self.provider.update_resource(session_id, user_name, {"access_keys": [], "compromised": False})
        event = self.provider.create_event(session_id, "IAM", "DeleteAccessKey", actor="student", resource_type="IAM_USER", outcome="SUCCESS", severity="LOW", resource_name=user_name, metadata={"user_name": user_name, "access_key_id": key_id})
        return {"status": "ok", "output": f"Deleted access key {key_id} for user {user_name}.", "data": {"Deleted": True}, "event": event}

    def _handle_s3_list(self, session_id, parsed):
        buckets = self.provider.list_resources(session_id, "S3_BUCKET")
        names = [bucket["resource_name"] for bucket in buckets]
        payload = {"Buckets": [{"Name": name, "CreationDate": "2026-09-24T00:00:00Z"} for name in names]}
        self.provider.create_event(session_id, "S3", "ListAllMyBuckets", actor="student", resource_type="S3_BUCKET", outcome="SUCCESS", severity="LOW", resource_name=names[0] if names else None, metadata={"count": len(names)})
        return {"status": "ok", "output": "\n".join(f"2026-09-24 10:21:33 {name}" for name in names), "data": payload, "event": {"service": "S3", "event_name": "ListAllMyBuckets"}}

    def _handle_s3_get_bucket_policy(self, session_id, parsed):
        bucket_name = self._extract_bucket_name(parsed["parts"])
        resource = self.provider.get_resource(session_id, bucket_name)
        config = resource.get("configuration", {}) if resource else {}
        payload = {"Bucket": bucket_name, "Policy": config.get("policy", {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": f"arn:aws:s3:::{bucket_name}/*"}]})}
        self.provider.create_event(session_id, "S3", "GetBucketPolicy", actor="student", resource_type="S3_BUCKET", outcome="SUCCESS", severity="MEDIUM", resource_name=bucket_name, metadata={"bucket": bucket_name})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "S3", "event_name": "GetBucketPolicy"}}

    def _handle_s3_get_public_access_block(self, session_id, parsed):
        bucket_name = self._extract_bucket_name(parsed["parts"])
        resource = self.provider.get_resource(session_id, bucket_name)
        config = resource.get("configuration", {}) if resource else {}
        payload = {"PublicAccessBlockConfiguration": {"BlockPublicAcls": not config.get("public_access", True), "IgnorePublicAcls": False, "BlockPublicPolicy": not config.get("public_access", True), "RestrictPublicBuckets": False}}
        self.provider.create_event(session_id, "S3", "GetPublicAccessBlock", actor="student", resource_type="S3_BUCKET", outcome="SUCCESS", severity="MEDIUM", resource_name=bucket_name, metadata={"bucket": bucket_name})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "S3", "event_name": "GetPublicAccessBlock"}}

    def _handle_s3_get_bucket_encryption(self, session_id, parsed):
        bucket_name = self._extract_bucket_name(parsed["parts"])
        resource = self.provider.get_resource(session_id, bucket_name)
        config = resource.get("configuration", {}) if resource else {}
        payload = {"Encryption": {"ServerSideEncryptionConfiguration": [{"BucketKeyEnabled": False, "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256" if not config.get("encryption") else "aws:kms"}}]}}
        self.provider.create_event(session_id, "S3", "GetBucketEncryption", actor="student", resource_type="S3_BUCKET", outcome="SUCCESS", severity="MEDIUM", resource_name=bucket_name, metadata={"bucket": bucket_name})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "S3", "event_name": "GetBucketEncryption"}}

    def _handle_s3_copy_object(self, session_id, parsed):
        source = next((token for token in parsed["parts"] if token.startswith("s3://")), "s3://cads-public-data/employee-data.csv")
        bucket_name, _, key = source[5:].partition("/")
        resource = self.provider.get_resource(session_id, bucket_name)
        if not resource:
            return {"status": "unsupported", "output": "CADS Simulator: Command not supported in this lab environment.", "event": None}
        config = resource.get("configuration", {}) if resource else {}
        if key not in config.get("objects", []) or not config.get("public_access", False):
            event = self.provider.create_event(session_id, "S3", "GetObject", actor="student", resource_type="S3_OBJECT", outcome="DENIED", severity="MEDIUM", resource_name=bucket_name, metadata={"object": key})
            return {"status": "denied", "output": "CADS Cloud Simulator: Object access denied.", "event": event}
        classification = "SENSITIVE" if key in {"employee-data.csv", "company-config.json", "customer-pii.parquet"} else "PUBLIC"
        event = self.provider.create_event(session_id, "S3", "GetObject", actor="student", resource_type="S3_OBJECT", outcome="SUCCESS", severity="HIGH", resource_name=bucket_name, metadata={"object": key, "classification": classification})
        output = f"CADS Cloud Simulator\n\nSimulated object retrieved:\n\n{key}\n\n[SIMULATION ONLY]\nNo real filesystem access occurred."
        return {"status": "ok", "output": output, "data": {"Bucket": bucket_name, "Key": key, "Classification": classification}, "event": event}

    def _handle_s3_put_public_access_block(self, session_id, parsed):
        bucket_name = self._extract_bucket_name(parsed["parts"])
        event = self.provider.remediate_s3_bucket(session_id, bucket_name)
        return {"status": "ok", "output": f"CADS Cloud Simulator: Public access blocked for {bucket_name}.", "event": event}

    def _handle_ec2_describe_instances(self, session_id, parsed):
        instances = self.provider.list_resources(session_id, "EC2_INSTANCE")
        payload = {"Reservations": [{"Instances": [{"InstanceId": i["resource_name"], "InstanceType": i.get("configuration", {}).get("instance_type", "t3.medium"), "PublicIpAddress": i.get("configuration", {}).get("public_ip", "198.51.100.25"), "SecurityGroups": [{"GroupName": sg} for sg in i.get("configuration", {}).get("security_groups", ["sg-cads-web"])], "State": {"Name": i.get("status", "running")}} for i in instances]}]}
        self.provider.create_event(session_id, "EC2", "DescribeInstances", actor="student", resource_type="EC2_INSTANCE", outcome="SUCCESS", severity="LOW", metadata={"count": len(instances)})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "EC2", "event_name": "DescribeInstances"}}

    def _handle_ec2_describe_security_groups(self, session_id, parsed):
        groups = self.provider.list_resources(session_id, "SECURITY_GROUP")
        payload = {"SecurityGroups": [{"GroupId": item.get("configuration", {}).get("group_id", "sg-01a2b3c4d5e6f7g8h"), "GroupName": item["resource_name"], "Description": item.get("configuration", {}).get("description", "Security group"), "IpPermissions": item.get("configuration", {}).get("inbound_rules", [])} for item in groups]}
        self.provider.create_event(session_id, "EC2", "DescribeSecurityGroups", actor="student", resource_type="SECURITY_GROUP", outcome="SUCCESS", severity="LOW", resource_name=groups[0]["resource_name"] if groups else None, metadata={"count": len(groups)})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "EC2", "event_name": "DescribeSecurityGroups"}}

    def _handle_ec2_describe_security_group_rules(self, session_id, parsed):
        groups = self.provider.list_resources(session_id, "SECURITY_GROUP")
        rules = []
        for g in groups:
            for rule in g.get("configuration", {}).get("inbound_rules", []):
                rules.append({
                    "GroupId": g.get("configuration", {}).get("group_id", "sg-01a2b3c4d5e6f7g8h"),
                    "GroupName": g["resource_name"],
                    "IpProtocol": rule.get("protocol", "tcp"),
                    "FromPort": rule.get("port", 22),
                    "ToPort": rule.get("port", 22),
                    "CidrIpv4": rule.get("source", "0.0.0.0/0"),
                    "Description": rule.get("description", ""),
                })
        payload = {"SecurityGroupRules": rules}
        self.provider.create_event(session_id, "EC2", "DescribeSecurityGroupRules", actor="student", resource_type="SECURITY_GROUP", outcome="SUCCESS", severity="LOW", resource_name=groups[0]["resource_name"] if groups else None, metadata={"rule_count": len(rules)})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "EC2", "event_name": "DescribeSecurityGroupRules"}}

    def _handle_ec2_revoke_security_group_ingress(self, session_id, parsed):
        group_name = self._extract_flag(parsed["parts"], "--group-name", "sg-cads-web")
        port = int(self._extract_flag(parsed["parts"], "--port", 22))
        cidr = self._extract_flag(parsed["parts"], "--cidr", "0.0.0.0/0")
        group_res = self.provider.get_resource(session_id, group_name)
        if group_res:
            rules = group_res.get("configuration", {}).get("inbound_rules", [])
            updated_rules = [r for r in rules if not (int(r.get("port", 0)) == port and r.get("source") == cidr)]
            self.provider.update_resource(session_id, group_name, {"inbound_rules": updated_rules})
        event = self.provider.create_event(session_id, "EC2", "RevokeSecurityGroupIngress", actor="student", resource_type="SECURITY_GROUP", outcome="SUCCESS", severity="LOW", resource_name=group_name, metadata={"group_name": group_name, "port": port, "cidr": cidr})
        return {"status": "ok", "output": f"Revoked security group ingress for port {port} from {cidr}.", "data": {"Return": True}, "event": event}

    def _handle_ec2_authorize_security_group_ingress(self, session_id, parsed):
        group_name = self._extract_flag(parsed["parts"], "--group-name", "sg-cads-web")
        port = int(self._extract_flag(parsed["parts"], "--port", 22))
        cidr = self._extract_flag(parsed["parts"], "--cidr", "10.0.0.0/16")
        group_res = self.provider.get_resource(session_id, group_name)
        if group_res:
            rules = list(group_res.get("configuration", {}).get("inbound_rules", []))
            rules.append({"protocol": "tcp", "port": port, "source": cidr, "description": "Restricted Access"})
            self.provider.update_resource(session_id, group_name, {"inbound_rules": rules})
        event = self.provider.create_event(session_id, "EC2", "AuthorizeSecurityGroupIngress", actor="student", resource_type="SECURITY_GROUP", outcome="SUCCESS", severity="LOW", resource_name=group_name, metadata={"group_name": group_name, "port": port, "cidr": cidr})
        return {"status": "ok", "output": f"Authorized security group ingress for port {port} from {cidr}.", "data": {"Return": True}, "event": event}

    def _handle_cloudtrail_describe_trails(self, session_id, parsed):
        trails = self.provider.list_resources(session_id, "CLOUDTRAIL_TRAIL")
        payload = {"trailList": [{"Name": t["resource_name"], "IsMultiRegionTrail": t.get("configuration", {}).get("is_multi_region", True), "HomeRegion": t.get("region", "ap-south-1"), "S3BucketName": t.get("configuration", {}).get("s3_bucket_name", "cads-audit-logs")} for t in trails] or [{"Name": "cads-management-trail", "IsMultiRegionTrail": True, "HomeRegion": "ap-south-1"}]}
        self.provider.create_event(session_id, "CloudTrail", "DescribeTrails", actor="student", resource_type="CLOUDTRAIL_TRAIL", outcome="SUCCESS", severity="LOW", metadata={"count": len(payload["trailList"])})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "CloudTrail", "event_name": "DescribeTrails"}}

    def _handle_cloudtrail_get_trail_status(self, session_id, parsed):
        payload = {"IsLogging": True, "LatestDeliveryTime": "2026-09-24T10:21:33Z", "LatestNotificationTime": "2026-09-24T10:21:33Z"}
        self.provider.create_event(session_id, "CloudTrail", "GetTrailStatus", actor="student", resource_type="CLOUDTRAIL_TRAIL", outcome="SUCCESS", severity="LOW", metadata={"logging": True})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "CloudTrail", "event_name": "GetTrailStatus"}}

    def _handle_cloudtrail_lookup_events(self, session_id, parsed):
        username = self._extract_flag(parsed["parts"], "--username")
        event_name_filter = self._extract_flag(parsed["parts"], "--event-name")
        resource_type_filter = self._extract_flag(parsed["parts"], "--resource-type")
        max_results = int(self._extract_flag(parsed["parts"], "--max-results", 50))

        events = self.provider.list_events(session_id)
        filtered = []
        for e in events:
            if username and e.get("actor") != username:
                continue
            if event_name_filter and e.get("event_name") != event_name_filter:
                continue
            if resource_type_filter and e.get("resource_type") != resource_type_filter:
                continue
            filtered.append({
                "EventId": e.get("event_id"),
                "EventName": e.get("event_name"),
                "EventTime": e.get("timestamp"),
                "EventSource": f"{e.get('service', '').lower()}.amazonaws.com",
                "Username": e.get("actor"),
                "Resources": [{"ResourceType": e.get("resource_type"), "ResourceName": e.get("resource_name")}],
                "SourceIPAddress": e.get("source_ip", "10.10.10.10"),
                "ReadOnly": e.get("event_name", "").startswith(("Get", "List", "Describe")),
            })

        payload = {"Events": filtered[:max_results]}
        self.provider.create_event(session_id, "CloudTrail", "LookupEvents", actor="student", resource_type="CLOUDTRAIL_TRAIL", outcome="SUCCESS", severity="LOW", metadata={"matched_events": len(filtered), "filter_user": username, "filter_event": event_name_filter})
        return {"status": "ok", "output": self._build_output(payload), "data": payload, "event": {"service": "CloudTrail", "event_name": "LookupEvents"}}

    @staticmethod
    def _extract_bucket_name(parts):
        for idx, token in enumerate(parts):
            if token.startswith("--bucket"):
                if "=" in token:
                    return token.split("=", 1)[1]
                if idx + 1 < len(parts):
                    return parts[idx + 1]
        for token in parts:
            if token.startswith("s3://"):
                return token.replace("s3://", "")
        return "cads-public-data"


def parse_command(command: str):
    engine = CommandEngine()
    return engine.parse(command)
