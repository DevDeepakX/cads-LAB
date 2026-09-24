import pytest

from app import create_app


@pytest.fixture
def database_url(tmp_path, monkeypatch):
    value = f"sqlite:///{tmp_path / 'persistent.db'}"
    monkeypatch.setenv("TEST_DATABASE_URL", value)
    return value


def token(client):
    with client.session_transaction() as state:
        return state["csrf_token"]


def register(client):
    client.get("/register")
    return client.post("/register", json={"username": "persistent-student", "email": "persist@example.com", "password": "correct-horse"}, headers={"X-CSRFToken": token(client)})


def test_lab_state_events_findings_and_progress_survive_restart(database_url):
    first = create_app("testing").test_client()
    assert register(first).status_code == 200
    start = first.post("/api/labs/LAB-001/start", headers={"X-CSRFToken": token(first)})
    assert start.status_code == 200
    first.post("/api/terminal/command", json={"command": "aws s3 ls"}, headers={"X-CSRFToken": token(first)})
    first.post("/api/terminal/command", json={"command": "aws s3api get-bucket-policy --bucket cads-public-data"}, headers={"X-CSRFToken": token(first)})
    before = first.get("/api/labs/LAB-001/findings").get_json()["findings"]
    assert before and before[0]["status"] == "OPEN"

    second = create_app("testing").test_client()
    second.get("/login")
    login = second.post("/login", json={"identifier": "persistent-student", "password": "correct-horse"}, headers={"X-CSRFToken": token(second)})
    assert login.status_code == 200
    resources = second.get("/api/labs/LAB-001/resources").get_json()["resources"]
    events = second.get("/api/labs/LAB-001/events").get_json()["events"]
    findings = second.get("/api/labs/LAB-001/findings").get_json()["findings"]
    assert resources[0]["resource_name"] == "cads-public-data"
    assert any(event["event_name"] == "ListAllMyBuckets" for event in events)
    assert findings[0]["finding_id"] == before[0]["finding_id"]

    finding_id = findings[0]["finding_id"]
    remediation = second.post(f"/api/labs/LAB-001/findings/{finding_id}/remediate", headers={"X-CSRFToken": token(second)})
    assert remediation.status_code == 200
    assert second.get("/api/labs/LAB-001/findings").get_json()["findings"][0]["status"] == "RESOLVED"
    assert second.get("/api/labs/LAB-001/verify").get_json()["completion"]["status"] == "completed"

    third = create_app("testing").test_client()
    third.get("/login")
    assert third.post("/login", json={"identifier": "persistent-student", "password": "correct-horse"}, headers={"X-CSRFToken": token(third)}).status_code == 200
    dashboard = third.get("/api/dashboard").get_json()
    assert dashboard["xp"] == 100
    assert dashboard["progress"]["completed"] == 1


def test_reset_persists_vulnerable_state_and_clears_security_records(database_url):
    client = create_app("testing").test_client()
    register(client)
    client.post("/api/labs/LAB-001/start", headers={"X-CSRFToken": token(client)})
    client.post("/api/terminal/command", json={"command": "aws s3 ls"}, headers={"X-CSRFToken": token(client)})
    assert client.get("/api/labs/LAB-001/findings").get_json()["findings"]
    reset = client.post("/api/labs/LAB-001/reset", headers={"X-CSRFToken": token(client)})
    assert reset.status_code == 200
    resource = client.get("/api/labs/LAB-001/resources").get_json()["resources"][0]
    assert resource["configuration"]["public_access"] is True
    assert client.get("/api/labs/LAB-001/findings").get_json()["findings"] == []


def test_user_ownership_rejects_cross_user_access(database_url):
    first = create_app("testing").test_client()
    register(first)
    first.post("/api/labs/LAB-001/start", headers={"X-CSRFToken": token(first)})
    first.post("/api/terminal/command", json={"command": "aws s3 ls"}, headers={"X-CSRFToken": token(first)})

    second = create_app("testing").test_client()
    second.get("/register")
    second.post("/register", json={"username": "other-student", "email": "other@example.com", "password": "correct-horse"}, headers={"X-CSRFToken": token(second)})
    assert second.get("/api/labs/LAB-001/resources").status_code == 404
    assert second.get("/api/labs/LAB-001/events").status_code == 404
    assert second.get("/api/labs/LAB-001/findings").status_code == 404
