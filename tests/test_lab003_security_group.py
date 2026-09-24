import json
import pytest
from app import create_app
from app.services.lab_engine import LabEngine, load_lab_definition
from app.services.cloud_provider import SimulatorProvider
from app.services.command_engine import CommandEngine


@pytest.fixture
def db_url(tmp_path, monkeypatch):
    value = f"sqlite:///{tmp_path / 'test_sg.db'}"
    monkeypatch.setenv("TEST_DATABASE_URL", value)
    return value


def csrf(client):
    with client.session_transaction() as state:
        return state["csrf_token"]


def register_user(client, username="sg-student", email="sg@example.com"):
    client.get("/register")
    return client.post("/register", json={"username": username, "email": email, "password": "correct-horse"}, headers={"X-CSRFToken": csrf(client)})


def login_user(client, identifier="sg-student"):
    client.get("/login")
    return client.post("/login", json={"identifier": identifier, "password": "correct-horse"}, headers={"X-CSRFToken": csrf(client)})


def test_lab003_definition_and_bootstrap():
    lab = load_lab_definition("LAB-003")
    assert lab is not None
    assert lab["id"] == "LAB-003"
    assert lab["slug"] == "insecure-security-group"
    assert lab["category"] == "Network Security"
    assert len(lab["objectives"]) >= 8
    assert any(r["resource_type"] == "SECURITY_GROUP" and r["resource_name"] == "sg-cads-web" for r in lab["resources"])
    assert any(r["resource_type"] == "EC2_INSTANCE" and r["resource_name"] == "cads-web-server" for r in lab["resources"])

    provider = SimulatorProvider()
    engine = LabEngine(provider)
    session_id = engine.start_session("LAB-003", "student-tester")
    state = engine.get_lab_state(session_id)
    assert len(state["resources"]) == 2
    sg_res = next(r for r in state["resources"] if r["resource_name"] == "sg-cads-web")
    assert any(r["port"] == 22 and r["source"] == "0.0.0.0/0" for r in sg_res["configuration"]["inbound_rules"])


def test_lab003_commands_and_events():
    provider = SimulatorProvider()
    engine = LabEngine(provider)
    cmd_engine = CommandEngine(provider)
    session_id = engine.start_session("LAB-003", "student-tester")

    # 1. describe-security-groups
    res = cmd_engine.execute(session_id, "aws ec2 describe-security-groups")
    assert res["status"] == "ok"
    assert len(res["data"]["SecurityGroups"]) >= 1

    # 2. describe-instances
    res = cmd_engine.execute(session_id, "aws ec2 describe-instances")
    assert res["status"] == "ok"
    assert len(res["data"]["Reservations"][0]["Instances"]) >= 1

    # 3. describe-security-group-rules
    res = cmd_engine.execute(session_id, "aws ec2 describe-security-group-rules")
    assert res["status"] == "ok"
    assert any(r["FromPort"] == 22 and r["CidrIpv4"] == "0.0.0.0/0" for r in res["data"]["SecurityGroupRules"])

    # 4. revoke-security-group-ingress
    res = cmd_engine.execute(session_id, "aws ec2 revoke-security-group-ingress --group-name sg-cads-web --port 22 --cidr 0.0.0.0/0")
    assert res["status"] == "ok"

    events = provider.list_events(session_id)
    event_names = [e["event_name"] for e in events]
    assert "DescribeSecurityGroups" in event_names
    assert "DescribeInstances" in event_names
    assert "DescribeSecurityGroupRules" in event_names
    assert "RevokeSecurityGroupIngress" in event_names


def test_lab003_detection_investigation_and_remediation_lifecycle(db_url):
    app = create_app("testing")
    client = app.test_client()
    register_user(client, "sg-tester", "sg-tester@example.com")

    # Start lab
    start = client.post("/api/labs/LAB-003/start", headers={"X-CSRFToken": csrf(client)})
    assert start.status_code == 200

    # Run inspection commands
    client.post("/api/terminal/command", json={"command": "aws ec2 describe-security-groups"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws ec2 describe-instances"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws ec2 describe-security-group-rules"}, headers={"X-CSRFToken": csrf(client)})

    # Findings should be generated
    findings_resp = client.get("/api/labs/LAB-003/findings")
    assert findings_resp.status_code == 200
    findings = findings_resp.get_json()["findings"]
    assert len(findings) >= 1
    finding = next(f for f in findings if f["rule_id"] == "EC2-OPEN-SSH")
    assert finding["status"] == "OPEN"
    finding_id = finding["finding_id"]

    # Investigate finding
    inv_resp = client.post(f"/api/labs/LAB-003/findings/{finding_id}/investigate", headers={"X-CSRFToken": csrf(client)})
    assert inv_resp.status_code == 200
    assert inv_resp.get_json()["finding"]["status"] == "INVESTIGATING"

    # Remediate finding
    rem_resp = client.post(f"/api/labs/LAB-003/findings/{finding_id}/remediate", headers={"X-CSRFToken": csrf(client)})
    assert rem_resp.status_code == 200

    # Verify objectives
    verify_resp = client.get("/api/labs/LAB-003/verify")
    assert verify_resp.status_code == 200
    result = verify_resp.get_json()
    assert all(obj["status"] == "PASS" for obj in result["objectives"].values())
    assert result["completion"]["status"] == "completed"


def test_lab003_persistence_and_reset(db_url):
    first_client = create_app("testing").test_client()
    register_user(first_client, "persist-sg", "persist-sg@example.com")
    first_client.post("/api/labs/LAB-003/start", headers={"X-CSRFToken": csrf(first_client)})
    first_client.post("/api/terminal/command", json={"command": "aws ec2 describe-security-groups"}, headers={"X-CSRFToken": csrf(first_client)})
    first_client.post("/api/terminal/command", json={"command": "aws ec2 revoke-security-group-ingress --group-name sg-cads-web --port 22 --cidr 0.0.0.0/0"}, headers={"X-CSRFToken": csrf(first_client)})

    # Restart app and resume
    second_client = create_app("testing").test_client()
    login_user(second_client, "persist-sg")
    resources = second_client.get("/api/labs/LAB-003/resources").get_json()["resources"]
    sg_res = next(r for r in resources if r["resource_name"] == "sg-cads-web")
    assert not any(r["port"] == 22 and r["source"] == "0.0.0.0/0" for r in sg_res["configuration"]["inbound_rules"])

    # Reset lab
    reset_resp = second_client.post("/api/labs/LAB-003/reset", headers={"X-CSRFToken": csrf(second_client)})
    assert reset_resp.status_code == 200

    # Check reset state
    reset_resources = second_client.get("/api/labs/LAB-003/resources").get_json()["resources"]
    reset_sg = next(r for r in reset_resources if r["resource_name"] == "sg-cads-web")
    assert any(r["port"] == 22 and r["source"] == "0.0.0.0/0" for r in reset_sg["configuration"]["inbound_rules"])
