class DefenseEngine:
    def __init__(self, provider):
        self.provider = provider

    def enable_s3_public_access_block(self, session_id, bucket_name="cads-public-data", actor="student"):
        return self.provider.remediate_s3_bucket(session_id, bucket_name, actor)

    def remediate_iam_policy(self, session_id, user_name="student-user", policy_arn="arn:aws:iam::aws:policy/AdministratorAccess", actor="student"):
        user_res = self.provider.get_resource(session_id, user_name)
        if not user_res or user_res.get("resource_type") != "IAM_USER":
            users = self.provider.list_resources(session_id, "IAM_USER")
            user_res = users[0] if users else None
        target_name = user_res.get("resource_name", user_name) if user_res else user_name
        if user_res:
            attached = [p for p in user_res.get("configuration", {}).get("attached_policies", []) if p not in {"AdministratorAccess", "ExcessiveDeveloperPolicy"}]
            self.provider.update_resource(session_id, target_name, {"attached_policies": attached, "escalated": False, "compromised": False})
        return self.provider.create_event(
            session_id,
            service="IAM",
            event_name="DetachUserPolicy",
            actor=actor,
            resource_type="IAM_USER",
            outcome="SUCCESS",
            severity="LOW",
            resource_name=target_name,
            metadata={"user_name": target_name, "policy_arn": policy_arn, "remediation": "LeastPrivilegeEnforced"},
        )

    def remediate_security_group(self, session_id, group_name="sg-cads-web", port=22, restricted_cidr="10.0.0.0/16", actor="student"):
        group_res = self.provider.get_resource(session_id, group_name)
        if not group_res or group_res.get("resource_type") != "SECURITY_GROUP":
            sgs = self.provider.list_resources(session_id, "SECURITY_GROUP")
            group_res = sgs[0] if sgs else None
        target_name = group_res.get("resource_name", group_name) if group_res else group_name
        if group_res:
            rules = [r for r in group_res.get("configuration", {}).get("inbound_rules", []) if not (int(r.get("port", 0)) == port and (r.get("source") == "0.0.0.0/0" or r.get("cidr_ip") == "0.0.0.0/0"))]
            rules.append({"protocol": "tcp", "port": port, "from_port": port, "to_port": port, "source": restricted_cidr, "cidr_ip": restricted_cidr, "description": "Restricted Admin Access"})
            self.provider.update_resource(session_id, target_name, {"inbound_rules": rules})
        return self.provider.create_event(
            session_id,
            service="EC2",
            event_name="RevokeSecurityGroupIngress",
            actor=actor,
            resource_type="SECURITY_GROUP",
            outcome="SUCCESS",
            severity="LOW",
            resource_name=target_name,
            metadata={"group_name": target_name, "port": port, "cidr": "0.0.0.0/0", "restricted_to": restricted_cidr},
        )

    def remediate_compromised_identity(self, session_id, user_name="compromised-user", actor="student"):
        user_res = self.provider.get_resource(session_id, user_name)
        if not user_res or user_res.get("resource_type") != "IAM_USER":
            users = self.provider.list_resources(session_id, "IAM_USER")
            user_res = users[0] if users else None
        target_name = user_res.get("resource_name", user_name) if user_res else user_name
        if user_res:
            self.provider.update_resource(session_id, target_name, {"access_keys": [], "attached_policies": [], "compromised": False})
        self.provider.create_event(
            session_id,
            service="IAM",
            event_name="DeleteAccessKey",
            actor=actor,
            resource_type="IAM_USER",
            outcome="SUCCESS",
            severity="LOW",
            resource_name=target_name,
            metadata={"user_name": target_name, "access_key_id": "AKIAEXAMPLEROOTKEY", "action": "DeactivateAndRevoke"},
        )
        return self.provider.create_event(
            session_id,
            service="IAM",
            event_name="DetachUserPolicy",
            actor=actor,
            resource_type="IAM_USER",
            outcome="SUCCESS",
            severity="LOW",
            resource_name=target_name,
            metadata={"user_name": target_name, "policy_arn": "arn:aws:iam::aws:policy/AdministratorAccess", "action": "RevokeCompromisedAccess"},
        )