from .detection_engine import DetectionEngine
from .finding_engine import FindingEngine


class EventProcessor:
    def __init__(self, provider, detection_engine=None, finding_engine=None):
        self.provider = provider
        self.detection_engine = detection_engine or DetectionEngine()
        self.finding_engine = finding_engine or FindingEngine(getattr(provider, "db_url", None))

    def process(self, event):
        findings = []
        for detection in self.detection_engine.evaluate(event, self.provider):
            findings.append(self.finding_engine.create_or_update(event["session_id"], detection))
        return findings

    def reevaluate(self, session_id):
        for event in self.provider.list_events(session_id):
            self.process(event)
        for finding in self.finding_engine.list_findings(session_id):
            resource = self.provider.get_resource(session_id, finding.get("resource_id"))
            rule_id = finding["rule_id"]
            if rule_id in {"S3-PUBLIC-ACCESS", "S3-SENSITIVE-OBJECT"} and resource and resource.get("configuration", {}).get("public_access") is False:
                self.finding_engine.resolve_matching(session_id, rule_id, finding.get("resource_id"))
            elif rule_id in {"IAM-EXCESSIVE-PERMISSIONS", "IAM-PRIVILEGE-ESCALATION"}:
                user_res = self.provider.get_resource(session_id, "student-user") or resource
                config = (user_res or {}).get("configuration", {})
                attached = config.get("attached_policies", [])
                if "AdministratorAccess" not in attached and "ExcessiveDeveloperPolicy" not in attached and not config.get("escalated"):
                    self.finding_engine.resolve_matching(session_id, rule_id, finding.get("resource_id"))
            elif rule_id == "EC2-OPEN-SSH":
                sg_res = self.provider.get_resource(session_id, "sg-cads-web") or resource
                config = (sg_res or {}).get("configuration", {})
                rules = config.get("inbound_rules", [])
                if not any(str(r.get("port")) == "22" and r.get("source") == "0.0.0.0/0" for r in rules):
                    self.finding_engine.resolve_matching(session_id, rule_id, finding.get("resource_id"))
            elif rule_id == "CLOUDTRAIL-SUSPICIOUS-ACTIVITY":
                user_res = self.provider.get_resource(session_id, "compromised-user") or resource
                config = (user_res or {}).get("configuration", {})
                if not config.get("compromised") and not config.get("access_keys"):
                    self.finding_engine.resolve_matching(session_id, rule_id, finding.get("resource_id"))
        return self.finding_engine.list_findings(session_id)

    def reset_session(self, session_id):
        self.finding_engine.clear_session(session_id)