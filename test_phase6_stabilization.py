from pathlib import Path

import pytest

from app import create_app
from app.services.database import get_db_connection


@pytest.fixture
def db_url(tmp_path, monkeypatch):
    value = f"sqlite:///{tmp_path / 'phase6.db'}"
    monkeypatch.setenv("TEST_DATABASE_URL", value)
    return value


def csrf(client):
    with client.session_transaction() as state:
        return state["csrf_token"]


def register(client, username="phase6-student", email="phase6@example.com"):
    client.get("/register")
    return client.post("/register", json={"username": username, "email": email, "password": "correct-horse"}, headers={"X-CSRFToken": csrf(client)})


def login(client, identifier="phase6-student"):
    client.get("/login")
    return client.post("/login", json={"identifier": identifier, "password": "correct-horse"}, headers={"X-CSRFToken": csrf(client)})


def test_fresh_database_startup_register_login_and_lab(db_url):
    client = create_app("testing").test_client()
    assert register(client).status_code == 200
    assert client.get("/api/me").get_json()["user"]["username"] == "phase6-student"
    assert client.post("/api/labs/LAB-001/start", headers={"X-CSRFToken": csrf(client)}).status_code == 200
    assert client.get("/api/labs/LAB-001/resources").get_json()["resources"]

    conn = get_db_connection(db_url)
    versions = [row[0] for row in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
    conn.close()
    assert versions == ["000_baseline_unversioned", "001_phase5_persistence", "002_phase6_runtime_stability"]


def test_existing_database_survives_second_factory_start(db_url):
    first = create_app("testing").test_client()
    assert register(first, "survivor", "survivor@example.com").status_code == 200
    assert first.post("/api/labs/LAB-001/start", headers={"X-CSRFToken": csrf(first)}).status_code == 200
    assert first.post("/api/terminal/command", json={"command": "aws s3 ls"}, headers={"X-CSRFToken": csrf(first)}).status_code == 200

    second = create_app("testing").test_client()
    assert login(second, "survivor").status_code == 200
    assert second.get("/api/labs/LAB-001/resources").get_json()["resources"]
    assert second.get("/api/labs/LAB-001/events").get_json()["events"]
    assert second.get("/api/labs/LAB-001/findings").get_json()["findings"]


def test_canonical_smoke_flow_and_restart(db_url):
    client = create_app("testing").test_client()
    register(client, "smoke-student", "smoke@example.com")
    assert client.get("/dashboard").status_code == 200
    client.post("/api/labs/LAB-001/start", headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws s3 ls"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws s3api get-bucket-policy --bucket cads-public-data"}, headers={"X-CSRFToken": csrf(client)})
    finding = client.get("/api/labs/LAB-001/findings").get_json()["findings"][0]
    assert client.post(f"/api/labs/LAB-001/findings/{finding['finding_id']}/investigate", headers={"X-CSRFToken": csrf(client)}).status_code == 200
    assert client.post(f"/api/labs/LAB-001/findings/{finding['finding_id']}/remediate", headers={"X-CSRFToken": csrf(client)}).status_code == 200
    assert client.get("/api/labs/LAB-001/verify").get_json()["completion"]["status"] == "completed"
    client.post("/logout", headers={"X-CSRFToken": csrf(client)})

    restarted = create_app("testing").test_client()
    assert login(restarted, "smoke-student").status_code == 200
    dashboard = restarted.get("/api/dashboard").get_json()
    assert dashboard["xp"] == 100
    assert dashboard["progress"]["completed"] == 1


def test_app_py_is_only_a_launcher():
    source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
    assert "@app.route" not in source
    assert "create_app" not in source or "from app import app" in source
