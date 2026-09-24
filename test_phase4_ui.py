from app import create_app
import uuid


def authenticated_client(app):
    client = app.test_client()
    client.get("/register")
    with client.session_transaction() as state:
        csrf = state["csrf_token"]
    suffix = uuid.uuid4().hex[:8]
    assert client.post("/register", json={"username": f"phase4-{suffix}", "email": f"phase4-{suffix}@example.com", "password": "correct-horse"}, headers={"X-CSRFToken": csrf}).status_code == 200
    return client


def csrf(client):
    with client.session_transaction() as state:
        return state["csrf_token"]


def test_phase4_pages_render_with_product_shell():
    app = create_app("testing")
    client = authenticated_client(app)

    for path in ("/dashboard", "/labs", "/labs/public-s3-bucket", "/progress", "/lab/LAB-001"):
        response = client.get(path)
        assert response.status_code == 200
        assert b"CADS" in response.data
        assert b"phase4.css" in response.data


def test_phase4_ui_apis_are_real_and_session_scoped():
    app = create_app("testing")
    client = authenticated_client(app)

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.get_json()["progress"]["total"] == 4

    labs = client.get("/api/labs")
    assert labs.status_code == 200
    assert [lab["id"] for lab in labs.get_json()["labs"]] == ["LAB-001", "LAB-002", "LAB-003", "LAB-004"]

    assert client.post("/api/labs/LAB-001/start", headers={"X-CSRFToken": csrf(client)}).status_code == 200
    assert client.get("/api/labs/LAB-001/resources").get_json()["resources"]
    assert client.get("/api/labs/LAB-001/events").status_code == 200
    assert client.get("/api/labs/LAB-001/progress").get_json()["total"] == 5
    assert client.get("/api/labs/LAB-001/events?service=NoSuchService").get_json()["events"] == []

    second_client = authenticated_client(app)
    assert second_client.get("/api/labs/LAB-001/resources").status_code == 404
    assert second_client.get("/api/labs/LAB-001/findings").status_code == 404


def test_dashboard_updates_from_active_simulator_session():
    app = create_app("testing")
    client = authenticated_client(app)
    client.post("/api/labs/LAB-001/start", headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws s3 ls"}, headers={"X-CSRFToken": csrf(client)})

    payload = client.get("/api/dashboard").get_json()
    assert payload["current_lab"]["lab_id"] == "LAB-001"
    assert payload["events"] >= 2
    assert payload["open_findings"] >= 1
    assert payload["current_lab"]["progress"] >= 20
