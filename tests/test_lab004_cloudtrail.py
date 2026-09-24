import json
import pytest
from app import create_app
from app.services.lab_engine import LabEngine, load_lab_definition
from app.services.cloud_provider import SimulatorProvider
from app.services.command_engine import CommandEngine


@pytest.fixture
def db_url(tmp_path, monkeypatch):
    value = f"sqlite:///{tmp_path / 'test_ct.db'}"
    monkeypatch.setenv("TEST_DATABASE_URL", value)
    return value


def csrf(client):
    with client.session_transaction() as state:
        return state["csrf_token"]


def register_user(client, username="ct-student", email="ct@example.com"):
    client.get("/register")
    return client.post("/register", json={"username": username, "email": email, "password": "correct-horse"}, headers={"X-CSRFToken": csrf(client)})


def login_user(client, identifier="ct-student"):
    client.get("/login")
    return client.post("/login", json={"identifier": identifier, "password": "correct-horse"}, headers={"X-CSRFToken": csrf(client)})


def test_lab004_definition_and_bootstrap():
    lab = load_lab_definition("LAB-004")
    assert lab is not None
    assert lab["id"] == "LAB-004"
    assert lab["slug"] == "cloudtrail-investigation"
    assert lab["category"] == "Logging & Detection"
    assert len(lab["objectives"]) >= 8
    assert any(r["resource_type"] == "CLOUDTRAIL_TRAIL" and r["resource_name"] == "cads-management-trail" for r in lab["resources"])
    assert any(r["resource_type"] == "IAM_USER" and r["resource_name"] == "compromised-user" for r in lab["resources"])

    provider = SimulatorProvider()
    engine = LabEngine(provider)
    session_id = engine.start_session("LAB-004", "student-tester")
    state = engine.get_lab_state(session_id)
    assert len(state["resources"]) == 3
    # Initial seeded events should be present
    events = state["events"]
    assert len(events) >= 6
    assert any(e["event_name"] == "ConsoleLogin" for e in events)
    assert any(e["event_name"] == "AttachUserPolicy" for e in events)
    assert any(e["event_name"] == "CreateAccessKey" for e in events)


def test_lab004_commands_and_filtering():
    provider = SimulatorProvider()
    engine = LabEngine(provider)
    cmd_engine = CommandEngine(provider)
    session_id = engine.start_session("LAB-004", "student-tester")

    # 1. describe-trails
    res = cmd_engine.execute(session_id, "aws cloudtrail describe-trails")
    assert res["status"] == "ok"
    assert len(res["data"]["trailList"]) >= 1

    # 2. get-trail-status
    res = cmd_engine.execute(session_id, "aws cloudtrail get-trail-status")
    assert res["status"] == "ok"
    assert res["data"]["IsLogging"] is True

    # 3. lookup-events
    res = cmd_engine.execute(session_id, "aws cloudtrail lookup-events")
    assert res["status"] == "ok"
    assert len(res["data"]["Events"]) >= 6

    # 4. lookup-events with username filter
    res = cmd_engine.execute(session_id, "aws cloudtrail lookup-events --username compromised-user")
    assert res["status"] == "ok"
    assert all(e["Username"] == "compromised-user" for e in res["data"]["Events"])

    # 5. lookup-events with event-name filter
    res = cmd_engine.execute(session_id, "aws cloudtrail lookup-events --event-name AttachUserPolicy")
    assert res["status"] == "ok"
    assert any(e["EventName"] == "AttachUserPolicy" for e in res["data"]["Events"])


def test_lab004_detection_investigation_and_remediation_lifecycle(db_url):
    app = create_app("testing")
    client = app.test_client()
    register_user(client, "ct-tester", "ct-tester@example.com")

    # Start lab
    start = client.post("/api/labs/LAB-004/start", headers={"X-CSRFToken": csrf(client)})
    assert start.status_code == 200

    # Run investigation commands
    client.post("/api/terminal/command", json={"command": "aws cloudtrail describe-trails"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws cloudtrail lookup-events"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws cloudtrail lookup-events --username compromised-user"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws cloudtrail lookup-events --event-name AttachUserPolicy"}, headers={"X-CSRFToken": csrf(client)})

    # Findings should be generated
    findings_resp = client.get("/api/labs/LAB-004/findings")
    assert findings_resp.status_code == 200
    findings = findings_resp.get_json()["findings"]
    assert len(findings) >= 1
    finding = next(f for f in findings if f["rule_id"] == "CLOUDTRAIL-SUSPICIOUS-ACTIVITY")
    assert finding["status"] == "OPEN"
    finding_id = finding["finding_id"]

    # Investigate finding
    inv_resp = client.post(f"/api/labs/LAB-004/findings/{finding_id}/investigate", headers={"X-CSRFToken": csrf(client)})
    assert inv_resp.status_code == 200
    assert inv_resp.get_json()["finding"]["status"] == "INVESTIGATING"

    # Remediate finding
    rem_resp = client.post(f"/api/labs/LAB-004/findings/{finding_id}/remediate", headers={"X-CSRFToken": csrf(client)})
    assert rem_resp.status_code == 200

    # Verify objectives
    verify_resp = client.get("/api/labs/LAB-004/verify")
    assert verify_resp.status_code == 200
    result = verify_resp.get_json()
    assert all(obj["status"] == "PASS" for obj in result["objectives"].values())
    assert result["completion"]["status"] == "completed"


def test_lab004_persistence_and_reset(db_url):
    first_client = create_app("testing").test_client()
    register_user(first_client, "persist-ct", "persist-ct@example.com")
    first_client.post("/api/labs/LAB-004/start", headers={"X-CSRFToken": csrf(first_client)})
    first_client.post("/api/terminal/command", json={"command": "aws cloudtrail lookup-events"}, headers={"X-CSRFToken": csrf(first_client)})

    # Restart app and resume
    second_client = create_app("testing").test_client()
    login_user(second_client, "persist-ct")
    events = second_client.get("/api/labs/LAB-004/events").get_json()["events"]
    assert len(events) >= 6

    # Reset lab
    reset_resp = second_client.post("/api/labs/LAB-004/reset", headers={"X-CSRFToken": csrf(second_client)})
    assert reset_resp.status_code == 200

    # Verify reset restored initial events
    reset_events = second_client.get("/api/labs/LAB-004/events").get_json()["events"]
    assert any(e["event_name"] == "ConsoleLogin" for e in reset_events)
    assert any(e["event_name"] == "AttachUserPolicy" for e in reset_events)
