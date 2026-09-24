import json
import pytest
from app import create_app
from app.services.lab_engine import LabEngine, load_lab_definition
from app.services.cloud_provider import SimulatorProvider
from app.services.command_engine import CommandEngine
from app.services.detection_engine import DetectionEngine
from app.services.defense_engine import DefenseEngine
from app.services.investigation_service import InvestigationService


@pytest.fixture
def db_url(tmp_path, monkeypatch):
    value = f"sqlite:///{tmp_path / 'test_iam.db'}"
    monkeypatch.setenv("TEST_DATABASE_URL", value)
    return value


def csrf(client):
    with client.session_transaction() as state:
        return state["csrf_token"]


def register_user(client, username="iam-student", email="iam@example.com"):
    client.get("/register")
    return client.post("/register", json={"username": username, "email": email, "password": "correct-horse"}, headers={"X-CSRFToken": csrf(client)})


def login_user(client, identifier="iam-student"):
    client.get("/login")
    return client.post("/login", json={"identifier": identifier, "password": "correct-horse"}, headers={"X-CSRFToken": csrf(client)})


def test_lab002_definition_and_bootstrap():
    lab = load_lab_definition("LAB-002")
    assert lab is not None
    assert lab["id"] == "LAB-002"
    assert lab["slug"] == "excessive-iam-permissions"
    assert lab["category"] == "Identity & Access Management"
    assert len(lab["objectives"]) >= 8
    assert any(r["resource_type"] == "IAM_USER" and r["resource_name"] == "student-user" for r in lab["resources"])
    assert any(r["resource_type"] == "IAM_POLICY" and r["resource_name"] == "ExcessiveDeveloperPolicy" for r in lab["resources"])

    provider = SimulatorProvider()
    engine = LabEngine(provider)
    session_id = engine.start_session("LAB-002", "student-tester")
    state = engine.get_lab_state(session_id)
    assert len(state["resources"]) == 4
    user_res = next(r for r in state["resources"] if r["resource_name"] == "student-user")
    assert "ExcessiveDeveloperPolicy" in user_res["configuration"]["attached_policies"]


def test_lab002_iam_commands_and_events():
    provider = SimulatorProvider()
    engine = LabEngine(provider)
    cmd_engine = CommandEngine(provider)
    session_id = engine.start_session("LAB-002", "student-tester")

    # 1. get-user
    res = cmd_engine.execute(session_id, "aws iam get-user")
    assert res["status"] == "ok"
    assert res["data"]["User"]["UserName"] == "student-user"

    # 2. list-attached-user-policies
    res = cmd_engine.execute(session_id, "aws iam list-attached-user-policies --user-name student-user")
    assert res["status"] == "ok"
    assert len(res["data"]["AttachedPolicies"]) >= 1

    # 3. get-policy
    res = cmd_engine.execute(session_id, "aws iam get-policy --policy-arn arn:aws:iam::CADS-000001:policy/ExcessiveDeveloperPolicy")
    assert res["status"] == "ok"
    assert res["data"]["Policy"]["PolicyName"] == "ExcessiveDeveloperPolicy"

    # 4. get-policy-version
    res = cmd_engine.execute(session_id, "aws iam get-policy-version --policy-arn arn:aws:iam::CADS-000001:policy/ExcessiveDeveloperPolicy --version-id v1")
    assert res["status"] == "ok"
    assert "iam:AttachUserPolicy" in res["data"]["PolicyVersion"]["Document"]["Statement"][0]["Action"]

    # 5. attach-user-policy (privilege escalation simulation)
    res = cmd_engine.execute(session_id, "aws iam attach-user-policy --user-name student-user --policy-arn arn:aws:iam::aws:policy/AdministratorAccess")
    assert res["status"] == "ok"

    events = provider.list_events(session_id)
    event_names = [e["event_name"] for e in events]
    assert "GetUser" in event_names
    assert "ListAttachedUserPolicies" in event_names
    assert "GetPolicyVersion" in event_names
    assert "AttachUserPolicy" in event_names


def test_lab002_detection_investigation_and_remediation_lifecycle(db_url):
    app = create_app("testing")
    client = app.test_client()
    register_user(client, "iam-tester", "iam-tester@example.com")

    # Start lab
    start = client.post("/api/labs/LAB-002/start", headers={"X-CSRFToken": csrf(client)})
    assert start.status_code == 200

    # Execute enumeration & attack commands
    client.post("/api/terminal/command", json={"command": "aws iam get-user"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws iam list-attached-user-policies --user-name student-user"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws iam get-policy-version --policy-arn arn:aws:iam::CADS-000001:policy/ExcessiveDeveloperPolicy"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws iam attach-user-policy --user-name student-user --policy-arn arn:aws:iam::aws:policy/AdministratorAccess"}, headers={"X-CSRFToken": csrf(client)})

    # Findings should be generated
    findings_resp = client.get("/api/labs/LAB-002/findings")
    assert findings_resp.status_code == 200
    findings = findings_resp.get_json()["findings"]
    assert len(findings) >= 1
    finding = findings[0]
    assert finding["status"] == "OPEN"
    finding_id = finding["finding_id"]

    # Investigate finding
    inv_resp = client.post(f"/api/labs/LAB-002/findings/{finding_id}/investigate", headers={"X-CSRFToken": csrf(client)})
    assert inv_resp.status_code == 200
    assert inv_resp.get_json()["finding"]["status"] == "INVESTIGATING"

    # Remediate finding
    rem_resp = client.post(f"/api/labs/LAB-002/findings/{finding_id}/remediate", headers={"X-CSRFToken": csrf(client)})
    assert rem_resp.status_code == 200
    assert rem_resp.get_json()["status"] == "remediated"

    # Verify objectives
    verify_resp = client.get("/api/labs/LAB-002/verify")
    assert verify_resp.status_code == 200
    result = verify_resp.get_json()
    assert all(obj["status"] == "PASS" for obj in result["objectives"].values())
    assert result["completion"]["status"] == "completed"


def test_lab002_persistence_and_reset(db_url):
    first_client = create_app("testing").test_client()
    register_user(first_client, "persist-iam", "persist-iam@example.com")
    first_client.post("/api/labs/LAB-002/start", headers={"X-CSRFToken": csrf(first_client)})
    first_client.post("/api/terminal/command", json={"command": "aws iam get-user"}, headers={"X-CSRFToken": csrf(first_client)})
    first_client.post("/api/terminal/command", json={"command": "aws iam attach-user-policy --user-name student-user --policy-arn arn:aws:iam::aws:policy/AdministratorAccess"}, headers={"X-CSRFToken": csrf(first_client)})

    # Restart app and resume
    second_client = create_app("testing").test_client()
    login_user(second_client, "persist-iam")
    resources = second_client.get("/api/labs/LAB-002/resources").get_json()["resources"]
    user_res = next(r for r in resources if r["resource_name"] == "student-user")
    assert user_res["configuration"]["escalated"] is True
    assert "AdministratorAccess" in user_res["configuration"]["attached_policies"]

    # Reset lab
    reset_resp = second_client.post("/api/labs/LAB-002/reset", headers={"X-CSRFToken": csrf(second_client)})
    assert reset_resp.status_code == 200
    assert reset_resp.get_json()["status"] == "reset"

    # Check reset state
    reset_resources = second_client.get("/api/labs/LAB-002/resources").get_json()["resources"]
    reset_user = next(r for r in reset_resources if r["resource_name"] == "student-user")
    assert reset_user["configuration"]["escalated"] is False
    assert "AdministratorAccess" not in reset_user["configuration"]["attached_policies"]
    assert "ExcessiveDeveloperPolicy" in reset_user["configuration"]["attached_policies"]
