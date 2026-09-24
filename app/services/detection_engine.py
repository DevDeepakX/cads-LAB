from dataclasses import dataclass


@dataclass(frozen=True)
class DetectionRule:
    rule_id: str
    name: str
    description: str
    severity: str
    service: str
    finding_type: str
    recommendation: str


RULES = (
    DetectionRule("S3-PUBLIC-ACCESS", "Publicly Accessible S3 Bucket", "An S3 bucket permits public access.", "HIGH", "S3", "PUBLIC_S3_EXPOSURE", "Restrict public access and verify the bucket configuration."),
    DetectionRule("S3-SENSITIVE-OBJECT", "Sensitive Object Access", "A sensitive object was accessed from a publicly accessible bucket.", "HIGH", "S3", "SENSITIVE_OBJECT_ACCESS", "Restrict public access and review the access event."),
    DetectionRule("IAM-EXCESSIVE-PERMISSIONS", "Excessive IAM Permission", "An identity has permissions broader than required.", "HIGH", "IAM", "EXCESSIVE_IAM_PERMISSION", "Reduce permissions to the minimum required scope."),
    DetectionRule("IAM-PRIVILEGE-ESCALATION", "IAM Privilege Escalation", "A low-privileged identity performed unauthorized privilege escalation.", "HIGH", "IAM", "IAM_PRIVILEGE_ESCALATION", "Detach administrative policy and restrict iam:AttachUserPolicy permission."),
    DetectionRule("EC2-OPEN-SSH", "Open SSH Security Group", "A security group permits SSH from the public internet.", "HIGH", "EC2", "OPEN_SSH_SECURITY_GROUP", "Restrict TCP/22 to trusted source networks."),
    DetectionRule("CLOUDTRAIL-SUSPICIOUS-ACTIVITY", "Suspicious Activity Sequence", "Suspicious multi-step attack sequence detected in CloudTrail audit logs.", "HIGH", "CloudTrail", "SUSPICIOUS_CLOUDTRAIL_ACTIVITY", "Isolate compromised IAM user, detach administrative policy, and delete access keys."),
)


class DetectionEngine:
    def __init__(self, rules=RULES):
        self.rules = tuple(rules)

    def evaluate(self, event, provider):
        detections = []
        resource_name = event.get("resource_name") or event.get("resource_id")
        resource = provider.get_resource(event["session_id"], resource_name) if resource_name else None
        config = (resource or {}).get("configuration", {})

        for rule in self.rules:
            detection = self._evaluate_rule(rule, event, resource, config, provider)
            if detection:
                detections.append(detection)
        return detections

    @staticmethod
    def _base(rule, event, resource, reason):
        return {
            "rule_id": rule.rule_id,
            "title": rule.name,
            "description": reason,
            "severity": rule.severity,
            "service": rule.service,
            "resource_id": (resource or {}).get("resource_name") or event.get("resource_name") or event.get("resource_id"),
            "recommendation": rule.recommendation,
            "evidence": [{
                "event_id": event["event_id"],
                "event_name": event["event_name"],
                "actor": event["actor"],
                "timestamp": event["timestamp"],
            }, {"resource": (resource or {}).get("resource_name"), "configuration": (resource or {}).get("configuration", {})}],
        }

    def _evaluate_rule(self, rule, event, resource, config, provider=None):
        if rule.rule_id == "S3-PUBLIC-ACCESS" and event["service"] == "S3" and resource and resource["resource_type"] == "S3_BUCKET" and config.get("public_access") is True:
            return self._base(rule, event, resource, "Public access is enabled on the bucket.")
        if rule.rule_id == "S3-SENSITIVE-OBJECT" and event["event_name"] == "GetObject" and event["service"] == "S3" and event.get("metadata", {}).get("classification") == "SENSITIVE" and config.get("public_access") is True:
            return self._base(rule, event, resource, "A sensitive object was accessed while the bucket was publicly accessible.")
        if rule.rule_id == "IAM-EXCESSIVE-PERMISSIONS":
            if event["service"] == "IAM" and event["event_name"] in {"GetRole", "ListAttachedRolePolicies"}:
                return self._base(rule, event, resource, "The identity exposes permissions broader than the lab requires.")
            if event["service"] == "IAM" and event["event_name"] in {"GetUser", "GetPolicy", "GetPolicyVersion", "ListAttachedUserPolicies"}:
                user_res = provider.get_resource(event["session_id"], "student-user") if provider else None
                user_cfg = (user_res or {}).get("configuration", {})
                if "ExcessiveDeveloperPolicy" in user_cfg.get("attached_policies", []) or "iam:AttachUserPolicy" in str(user_cfg.get("dangerous_permissions", [])):
                    return self._base(rule, event, resource or user_res, "The user has excessive permissions allowing iam:AttachUserPolicy privilege escalation.")
        if rule.rule_id == "IAM-PRIVILEGE-ESCALATION":
            if event["service"] == "IAM" and event["event_name"] == "AttachUserPolicy":
                return self._base(rule, event, resource, "Privilege escalation detected: AdministratorAccess policy was attached.")
            if resource and resource.get("resource_type") == "IAM_USER" and config.get("escalated") is True:
                return self._base(rule, event, resource, "The identity has active escalated administrator privileges.")
        if rule.rule_id == "EC2-OPEN-SSH":
            target = resource
            if not target and provider:
                target = provider.get_resource(event["session_id"], "sg-cads-web")
            target_config = (target or {}).get("configuration", {})
            if (target and target.get("resource_type") == "SECURITY_GROUP") or event["service"] == "EC2":
                if any(str(item.get("port")) == "22" and item.get("source") == "0.0.0.0/0" for item in target_config.get("inbound_rules", [])):
                    return self._base(rule, event, target, "TCP/22 is open to 0.0.0.0/0 on security group.")
        if rule.rule_id == "CLOUDTRAIL-SUSPICIOUS-ACTIVITY":
            if event["service"] == "CloudTrail" and event["event_name"] in {"LookupEvents", "DescribeTrails", "GetTrailStatus"}:
                user_res = provider.get_resource(event["session_id"], "compromised-user") if provider else None
                user_cfg = (user_res or {}).get("configuration", {})
                if user_cfg.get("compromised", False) or user_cfg.get("access_keys"):
                    return self._base(rule, event, user_res or resource, "Suspicious sequence: ConsoleLogin -> Reconnaissance -> Privilege Escalation -> Access Key Generation.")
            if event["actor"] == "compromised-user" and event["event_name"] in {"AttachUserPolicy", "CreateAccessKey"}:
                return self._base(rule, event, resource, "Suspicious administrative action performed by compromised identity.")
        return None