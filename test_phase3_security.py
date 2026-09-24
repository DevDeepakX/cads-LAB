import uuid

from app.services.cloud_provider import SimulatorProvider
from app.services.command_engine import CommandEngine
from app.services.defense_engine import DefenseEngine
from app.services.investigation_service import InvestigationService
from app.services.lab_engine import LabEngine
from app import create_app


def test_normalized_events_and_public_bucket_detection():
    provider = SimulatorProvider()
    lab = LabEngine(provider)
    session_id = lab.start_session("LAB-001")
    engine = CommandEngine(provider)

    engine.execute(session_id, "aws s3 ls")
    engine.execute(session_id, "aws s3api get-bucket-policy --bucket cads-public-data")

    event = provider.list_events(session_id)[-1]
    assert {"event_id", "source_ip", "region", "resource_id"}.issubset(event)
    findings = lab.finding_engine.list_findings(session_id)
    assert any(item["rule_id"] == "S3-PUBLIC-ACCESS" and item["severity"] == "HIGH" for item in findings)
    assert findings[0]["evidence"]


def test_sensitive_object_access_and_safe_simulation():
    provider = SimulatorProvider()
    lab = LabEngine(provider)
    session_id = lab.start_session("LAB-001")
    result = CommandEngine(provider).execute(session_id, "aws s3 cp s3://cads-public-data/employee-data.csv .")

    assert result["status"] == "ok"
    assert "No real filesystem access occurred" in result["output"]
    assert any(item["rule_id"] == "S3-SENSITIVE-OBJECT" for item in lab.finding_engine.list_findings(session_id))


def test_investigation_timeline_is_scoped_and_chronological():
    provider = SimulatorProvider()
    lab = LabEngine(provider)
    session_id = lab.start_session("LAB-001")
    CommandEngine(provider).execute(session_id, "aws s3 ls")
    finding = lab.finding_engine.list_findings(session_id)[0]
    details = InvestigationService(provider, lab.finding_engine).investigate(session_id, finding["finding_id"])

    assert details["finding"]["status"] == "INVESTIGATING"
    assert details["resource"]["resource_name"] == "cads-public-data"
    assert details["timeline"] == sorted(details["timeline"], key=lambda event: event["timestamp"])
    assert all(event["session_id"] == session_id for event in details["events"])


def test_defense_generates_event_and_resolves_finding():
    provider = SimulatorProvider()
    lab = LabEngine(provider)
    session_id = lab.start_session("LAB-001")
    CommandEngine(provider).execute(session_id, "aws s3 ls")
    finding = lab.finding_engine.list_findings(session_id)[0]

    event = DefenseEngine(provider).enable_s3_public_access_block(session_id)
    provider._event_processor.reevaluate(session_id)

    assert event["event_name"] == "PutPublicAccessBlock"
    assert provider.get_resource(session_id, "cads-public-data")["configuration"]["public_access"] is False
    assert lab.finding_engine.get_finding(session_id, finding["finding_id"])["status"] == "RESOLVED"


def test_findings_are_isolated_between_sessions():
    provider = SimulatorProvider()
    lab = LabEngine(provider)
    session_a = lab.start_session("LAB-001", "student-a")
    session_b = lab.start_session("LAB-001", "student-b")
    CommandEngine(provider).execute(session_a, "aws s3 ls")

    assert lab.finding_engine.list_findings(session_a)
    assert lab.finding_engine.list_findings(session_b) == []
    assert lab.finding_engine.get_finding(session_b, lab.finding_engine.list_findings(session_a)[0]["finding_id"]) is None


def test_phase3_api_flow_uses_server_side_session_scope():
    app = create_app("testing")
    client = app.test_client()
    client.get("/register")
    with client.session_transaction() as state:
        csrf = state["csrf_token"]
    suffix = uuid.uuid4().hex[:8]
    assert client.post("/register", json={"username": f"phase3-api-{suffix}", "email": f"phase3-api-{suffix}@example.com", "password": "correct-horse"}, headers={"X-CSRFToken": csrf}).status_code == 200
    with client.session_transaction() as state:
        csrf = state["csrf_token"]
    started = client.post("/api/labs/LAB-001/start", headers={"X-CSRFToken": csrf})
    assert started.status_code == 200

    command = client.post("/api/terminal/command", json={"command": "aws s3 ls"}, headers={"X-CSRFToken": csrf})
    assert command.status_code == 200
    findings = client.get("/api/labs/LAB-001/findings").get_json()["findings"]
    assert findings
    finding_id = findings[0]["finding_id"]

    investigated = client.post(f"/api/labs/LAB-001/findings/{finding_id}/investigate", headers={"X-CSRFToken": csrf})
    assert investigated.status_code == 200
    remediated = client.post(f"/api/labs/LAB-001/findings/{finding_id}/remediate", headers={"X-CSRFToken": csrf})
    assert remediated.status_code == 200
    assert remediated.get_json()["finding"]["status"] == "RESOLVED"


def test_generic_iam_and_open_ssh_rules_evaluate():
    provider = SimulatorProvider()
    lab = LabEngine(provider)
    session_id = lab.start_session("LAB-001")
    provider.create_event(session_id, "IAM", "GetRole", resource_type="IAM_ROLE", resource_name="cads-s3-readonly")
    provider.create_event(session_id, "EC2", "DescribeSecurityGroups", resource_type="SECURITY_GROUP", resource_name="default-sg")

    rule_ids = {finding["rule_id"] for finding in lab.finding_engine.list_findings(session_id)}
    assert "IAM-EXCESSIVE-PERMISSIONS" in rule_ids
    assert "EC2-OPEN-SSH" in rule_ids


def test_unsupported_and_shell_chaining_commands_remain_blocked():
    provider = SimulatorProvider()
    lab = LabEngine(provider)
    session_id = lab.start_session("LAB-001")
    engine = CommandEngine(provider)

    assert engine.execute(session_id, "aws s3 rm s3://cads-public-data/file")["status"] == "unsupported"
    try:
        engine.execute(session_id, "aws s3 ls; whoami")
    except ValueError:
        pass
    else:
        raise AssertionError("shell chaining must be rejected")
