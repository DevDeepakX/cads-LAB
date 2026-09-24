import json
from .database import get_db_connection


def _get_lab_id_for_session(session_id, provider):
    if getattr(provider, "db_url", None):
        try:
            conn = get_db_connection(provider.db_url)
            row = conn.execute(
                "SELECT labs.lab_id, labs.slug, lab_sessions.metadata FROM lab_sessions LEFT JOIN labs ON lab_sessions.lab_id = labs.id WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            conn.close()
            if row:
                if row["lab_id"]:
                    return row["lab_id"]
                if row["slug"]:
                    return row["slug"]
                if row["metadata"]:
                    meta = json.loads(row["metadata"] or "{}")
                    if meta.get("lab_id") or meta.get("slug"):
                        return meta.get("lab_id") or meta.get("slug")
        except Exception:
            pass

    resources = {item["resource_name"]: item for item in provider.list_resources(session_id)}
    if "student-user" in resources or "ExcessiveDeveloperPolicy" in resources:
        return "LAB-002"
    if "sg-cads-web" in resources or "cads-web-server" in resources:
        return "LAB-003"
    if "cads-management-trail" in resources or "compromised-user" in resources:
        return "LAB-004"
    return "LAB-001"


def verify_objectives(session_id, provider):
    if getattr(provider, "_event_processor", None):
        provider._event_processor.reevaluate(session_id)
    resources = {item["resource_name"]: item for item in provider.list_resources(session_id)}
    events = provider.list_events(session_id)
    findings = provider._event_processor.finding_engine.list_findings(session_id) if getattr(provider, "_event_processor", None) else []
    event_names = [event.get("event_name") for event in events]

    lab_id = _get_lab_id_for_session(session_id, provider)

    if lab_id in {"LAB-002", "excessive-iam-permissions"}:
        user_res = resources.get("student-user", {})
        user_cfg = user_res.get("configuration", {})
        attached = user_cfg.get("attached_policies", [])
        escalated = user_cfg.get("escalated", False)

        has_enum = any(name in {"GetUser", "ListUsers"} for name in event_names)
        has_list_pol = any(name in {"ListAttachedUserPolicies", "ListAttachedRolePolicies"} for name in event_names)
        has_inspect = any(name in {"GetPolicy", "GetPolicyVersion"} for name in event_names)
        has_escalate = any(name == "AttachUserPolicy" for name in event_names) or escalated
        has_event_obs = any(e.get("service") == "IAM" and (e.get("severity") == "HIGH" or e.get("event_name") == "AttachUserPolicy") for e in events) or len(findings) > 0
        has_investigate = any(f.get("status") in {"INVESTIGATING", "RESOLVED"} for f in findings) or has_inspect
        has_remediate = any(name == "DetachUserPolicy" for name in event_names) or any(f.get("status") == "RESOLVED" for f in findings) or ("AdministratorAccess" not in attached and "ExcessiveDeveloperPolicy" not in attached and not escalated)
        has_verified = "AdministratorAccess" not in attached and "ExcessiveDeveloperPolicy" not in attached and not escalated

        return {
            "OBJ-001": {
                "status": "PASS" if has_enum else "FAIL",
                "message": "IAM identity enumerated successfully." if has_enum else "IAM identity enumeration not recorded.",
            },
            "OBJ-002": {
                "status": "PASS" if has_list_pol else "FAIL",
                "message": "Attached user policies listed." if has_list_pol else "Attached user policies not inspected.",
            },
            "OBJ-003": {
                "status": "PASS" if has_inspect else "FAIL",
                "message": "Policy document inspected and excessive permissions identified." if has_inspect else "Policy document not yet inspected.",
            },
            "OBJ-004": {
                "status": "PASS" if has_escalate else "FAIL",
                "message": "Privilege escalation action simulated." if has_escalate else "Privilege escalation action not performed.",
            },
            "OBJ-005": {
                "status": "PASS" if has_event_obs else "FAIL",
                "message": "Privilege escalation event observed in cloud telemetry." if has_event_obs else "Security event telemetry not observed.",
            },
            "OBJ-006": {
                "status": "PASS" if has_investigate else "FAIL",
                "message": "Excessive IAM permission finding investigated." if has_investigate else "Finding investigation pending.",
            },
            "OBJ-007": {
                "status": "PASS" if has_remediate else "FAIL",
                "message": "Excessive permissions successfully remediated." if has_remediate else "Policy remediation pending.",
            },
            "OBJ-008": {
                "status": "PASS" if has_verified else "FAIL",
                "message": "Least privilege policy verified and administrative privileges removed." if has_verified else "Identity still possesses excessive privileges.",
            },
        }

    if lab_id in {"LAB-003", "insecure-security-group"}:
        sg_res = resources.get("sg-cads-web", {})
        sg_cfg = sg_res.get("configuration", {})
        inbound_rules = sg_cfg.get("inbound_rules", [])
        open_ssh = any(str(r.get("port")) == "22" and r.get("source") == "0.0.0.0/0" for r in inbound_rules)

        has_sg_enum = any(name in {"DescribeSecurityGroups", "DescribeSecurityGroupRules"} for name in event_names)
        has_admin_id = any(name in {"DescribeSecurityGroups", "DescribeSecurityGroupRules"} for name in event_names)
        has_instance_id = any(name == "DescribeInstances" for name in event_names)
        has_rule_inspect = any(name in {"DescribeSecurityGroupRules", "DescribeSecurityGroups"} for name in event_names)
        has_event_obs = any(e.get("service") == "EC2" for e in events) or len(findings) > 0
        has_investigate = any(f.get("status") in {"INVESTIGATING", "RESOLVED"} for f in findings) or has_rule_inspect
        has_remediate = any(name == "RevokeSecurityGroupIngress" for name in event_names) or not open_ssh or any(f.get("status") == "RESOLVED" for f in findings)
        has_verified = not open_ssh

        return {
            "OBJ-001": {
                "status": "PASS" if has_sg_enum else "FAIL",
                "message": "Security groups enumerated." if has_sg_enum else "Security group enumeration not recorded.",
            },
            "OBJ-002": {
                "status": "PASS" if has_admin_id else "FAIL",
                "message": "Public administrative SSH access identified." if has_admin_id else "Exposed administrative port not identified.",
            },
            "OBJ-003": {
                "status": "PASS" if has_instance_id else "FAIL",
                "message": "Associated EC2 instance identified." if has_instance_id else "EC2 instance enumeration not recorded.",
            },
            "OBJ-004": {
                "status": "PASS" if has_rule_inspect else "FAIL",
                "message": "Inbound security group rules inspected." if has_rule_inspect else "Security group rules inspection pending.",
            },
            "OBJ-005": {
                "status": "PASS" if has_event_obs else "FAIL",
                "message": "Network security event telemetry observed." if has_event_obs else "Network telemetry not observed.",
            },
            "OBJ-006": {
                "status": "PASS" if has_investigate else "FAIL",
                "message": "Open SSH security group finding investigated." if has_investigate else "Finding investigation pending.",
            },
            "OBJ-007": {
                "status": "PASS" if has_remediate else "FAIL",
                "message": "Inbound SSH exposure restricted." if has_remediate else "Remediation not yet applied.",
            },
            "OBJ-008": {
                "status": "PASS" if has_verified else "FAIL",
                "message": "Verified TCP/22 is no longer exposed to 0.0.0.0/0." if has_verified else "Security group is still open to 0.0.0.0/0.",
            },
        }

    if lab_id in {"LAB-004", "cloudtrail-investigation"}:
        user_res = resources.get("compromised-user", {})
        user_cfg = user_res.get("configuration", {})
        compromised = user_cfg.get("compromised", False)
        keys = user_cfg.get("access_keys", [])
        attached = user_cfg.get("attached_policies", [])

        has_trail_inspect = any(name in {"DescribeTrails", "GetTrailStatus"} for name in event_names)
        has_query_events = any(name == "LookupEvents" for name in event_names)
        has_filter_user = any(e.get("event_name") == "LookupEvents" and e.get("metadata", {}).get("filter_user") for e in events) or has_query_events
        has_priv_esc_id = any(e.get("event_name") == "LookupEvents" and e.get("metadata", {}).get("filter_event") in {"AttachUserPolicy", "CreateAccessKey"} for e in events) or has_query_events
        has_timeline = has_query_events or len(events) >= 6
        has_investigate = any(f.get("status") in {"INVESTIGATING", "RESOLVED"} for f in findings) or len([e for e in events if e.get("event_name") == "LookupEvents"]) >= 1
        has_remediate = any(name in {"DeleteAccessKey", "DetachUserPolicy"} for name in event_names) or any(f.get("status") == "RESOLVED" for f in findings) or (not compromised and not keys)
        has_verified = not compromised and not keys and "AdministratorAccess" not in attached

        return {
            "OBJ-001": {
                "status": "PASS" if has_trail_inspect else "FAIL",
                "message": "CloudTrail configuration inspected." if has_trail_inspect else "CloudTrail status not inspected.",
            },
            "OBJ-002": {
                "status": "PASS" if has_query_events else "FAIL",
                "message": "CloudTrail audit events queried." if has_query_events else "Audit events lookup pending.",
            },
            "OBJ-003": {
                "status": "PASS" if has_filter_user else "FAIL",
                "message": "Audit events filtered by identity." if has_filter_user else "Identity filter pending.",
            },
            "OBJ-004": {
                "status": "PASS" if has_priv_esc_id else "FAIL",
                "message": "Privilege escalation action identified in audit trail." if has_priv_esc_id else "Suspicious event filter pending.",
            },
            "OBJ-005": {
                "status": "PASS" if has_timeline else "FAIL",
                "message": "Incident event sequence correlated." if has_timeline else "Event sequence correlation pending.",
            },
            "OBJ-006": {
                "status": "PASS" if has_investigate else "FAIL",
                "message": "Suspicious activity finding investigated." if has_investigate else "Finding investigation pending.",
            },
            "OBJ-007": {
                "status": "PASS" if has_remediate else "FAIL",
                "message": "Compromised credentials revoked and identity remediated." if has_remediate else "Credential remediation pending.",
            },
            "OBJ-008": {
                "status": "PASS" if has_verified else "FAIL",
                "message": "Verified compromised access keys revoked and admin access removed." if has_verified else "Compromised credential still active.",
            },
        }

    # Default to LAB-001
    bucket = resources.get("cads-public-data", {})
    config = bucket.get("configuration", {})
    exposure_observed = config.get("public_access") is True or any(event.get("service") == "S3" and event.get("resource_name") == "cads-public-data" for event in events)

    results = {
        "OBJ-001": {
            "status": "PASS" if any(name in {"ListAllMyBuckets", "ListBucket"} for name in event_names) else "FAIL",
            "message": "S3 enumeration executed successfully." if any(name in {"ListAllMyBuckets", "ListBucket"} for name in event_names) else "No S3 enumeration event was recorded.",
        },
        "OBJ-002": {
            "status": "PASS" if exposure_observed else "FAIL",
            "message": "The public bucket was identified as publicly accessible." if exposure_observed else "The bucket exposure has not been established.",
        },
        "OBJ-003": {
            "status": "PASS" if any(name in {"GetBucketPolicy", "GetPublicAccessBlock", "GetBucketEncryption"} for name in event_names) else "FAIL",
            "message": "Bucket policy or settings were inspected." if any(name in {"GetBucketPolicy", "GetPublicAccessBlock", "GetBucketEncryption"} for name in event_names) else "Bucket policy inspection is incomplete.",
        },
        "OBJ-004": {
            "status": "PASS" if config.get("public_access") is False else "FAIL",
            "message": "Public access has been successfully removed." if config.get("public_access") is False else "The bucket is still publicly accessible.",
        },
        "OBJ-005": {
            "status": "PASS" if config.get("public_access") is False and config.get("encryption") is True and config.get("logging") is True else "FAIL",
            "message": "The bucket is secured and logging is enabled." if config.get("public_access") is False and config.get("encryption") is True and config.get("logging") is True else "The bucket is not yet fully hardened.",
        },
    }
    return results


def verify_lab_conditions(state, requirements):
    """Minimal verification hook for future lab validation rules."""
    if not isinstance(requirements, dict):
        return False

    checks = requirements.get("checks", [])
    if not checks:
        return bool(state)

    for rule in checks:
        key = rule.get("key")
        expected = rule.get("expected")
        actual = state.get(key)
        if actual != expected:
            return False
    return True
