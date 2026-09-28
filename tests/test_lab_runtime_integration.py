import pytest
from app import create_app


@pytest.fixture
def db_url(tmp_path, monkeypatch):
    value = f"sqlite:///{tmp_path / 'lab_runtime_integration.db'}"
    monkeypatch.setenv("TEST_DATABASE_URL", value)
    return value


def csrf(client):
    with client.session_transaction() as state:
        return state.get("csrf_token")


def register_user(client, username="student1", email="student1@example.com", password="password123"):
    client.get("/register")
    return client.post(
        "/register",
        json={"username": username, "email": email, "password": password},
        headers={"X-CSRFToken": csrf(client)},
    )


def test_lab_overview_public_s3_bucket_renders_objectives(db_url):
    """1. GET /labs/public-s3-bucket returns HTTP 200 and renders objectives."""
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    response = client.get("/labs/public-s3-bucket")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Public S3 Bucket" in html
    assert "0 objectives" not in html
    assert "5 objectives" in html
    assert "Enumerate S3 resources" in html
    assert "data-start-lab=\"LAB-001\"" in html


def test_lab001_metadata_api(db_url):
    """2. LAB-001 metadata API: HTTP 200, JSON, valid lab ID, non-empty objectives."""
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    response = client.get("/api/labs/LAB-001")
    assert response.status_code == 200
    assert response.content_type.startswith("application/json")
    data = response.get_json()
    assert data["id"] == "LAB-001"
    assert data["slug"] == "public-s3-bucket"
    assert len(data.get("objectives", [])) == 5


def test_lab002_metadata_api(db_url):
    """3. LAB-002 metadata API: HTTP 200, JSON, valid lab ID, non-empty objectives."""
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    response = client.get("/api/labs/LAB-002")
    assert response.status_code == 200
    assert response.content_type.startswith("application/json")
    data = response.get_json()
    assert data["id"] == "LAB-002"
    assert data["slug"] == "excessive-iam-permissions"
    assert len(data.get("objectives", [])) >= 8


def test_lab003_metadata_api(db_url):
    """4. LAB-003 metadata API: HTTP 200, JSON, valid lab ID, non-empty objectives."""
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    response = client.get("/api/labs/LAB-003")
    assert response.status_code == 200
    assert response.content_type.startswith("application/json")
    data = response.get_json()
    assert data["id"] == "LAB-003"
    assert data["slug"] == "insecure-security-group"
    assert len(data.get("objectives", [])) >= 8


def test_lab004_metadata_api(db_url):
    """5. LAB-004 metadata API: HTTP 200, JSON, valid lab ID, non-empty objectives."""
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    response = client.get("/api/labs/LAB-004")
    assert response.status_code == 200
    assert response.content_type.startswith("application/json")
    data = response.get_json()
    assert data["id"] == "LAB-004"
    assert data["slug"] == "cloudtrail-investigation"
    assert len(data.get("objectives", [])) >= 8


def test_start_lab001_and_workspace(db_url):
    """6. Start LAB-001 -> valid session and workspace response."""
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    start_res = client.post("/api/labs/LAB-001/start", headers={"X-CSRFToken": csrf(client)})
    assert start_res.status_code == 200
    assert start_res.content_type.startswith("application/json")
    start_data = start_res.get_json()
    assert start_data["status"] == "started"
    assert start_data["lab"]["lab_id"] == "LAB-001"
    assert len(start_data["lab"]["objectives"]) == 5

    ws_res = client.get("/lab/LAB-001")
    assert ws_res.status_code == 200
    assert b"Public S3 Bucket" in ws_res.data
    assert b"\"LAB-001\"" in ws_res.data

    state_res = client.get("/api/labs/LAB-001/state")
    assert state_res.status_code == 200
    assert state_res.content_type.startswith("application/json")
    assert state_res.get_json()["lab_id"] == "LAB-001"


def test_start_lab002_and_workspace(db_url):
    """7. Start LAB-002 -> valid session and workspace response."""
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    start_res = client.post("/api/labs/LAB-002/start", headers={"X-CSRFToken": csrf(client)})
    assert start_res.status_code == 200
    assert start_res.content_type.startswith("application/json")
    start_data = start_res.get_json()
    assert start_data["status"] == "started"
    assert start_data["lab"]["lab_id"] == "LAB-002"

    ws_res = client.get("/lab/LAB-002")
    assert ws_res.status_code == 200
    assert b"Excessive IAM Permissions" in ws_res.data

    state_res = client.get("/api/labs/LAB-002/state")
    assert state_res.status_code == 200
    assert state_res.content_type.startswith("application/json")
    assert state_res.get_json()["lab_id"] == "LAB-002"


def test_start_lab003_and_workspace(db_url):
    """8. Start LAB-003 -> valid session and workspace response."""
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    start_res = client.post("/api/labs/LAB-003/start", headers={"X-CSRFToken": csrf(client)})
    assert start_res.status_code == 200
    assert start_res.content_type.startswith("application/json")
    start_data = start_res.get_json()
    assert start_data["status"] == "started"
    assert start_data["lab"]["lab_id"] == "LAB-003"

    ws_res = client.get("/lab/LAB-003")
    assert ws_res.status_code == 200
    assert b"Insecure Security Group" in ws_res.data

    state_res = client.get("/api/labs/LAB-003/state")
    assert state_res.status_code == 200
    assert state_res.content_type.startswith("application/json")
    assert state_res.get_json()["lab_id"] == "LAB-003"


def test_start_lab004_and_workspace(db_url):
    """9. Start LAB-004 -> valid session and workspace response."""
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    start_res = client.post("/api/labs/LAB-004/start", headers={"X-CSRFToken": csrf(client)})
    assert start_res.status_code == 200
    assert start_res.content_type.startswith("application/json")
    start_data = start_res.get_json()
    assert start_data["status"] == "started"
    assert start_data["lab"]["lab_id"] == "LAB-004"

    ws_res = client.get("/lab/LAB-004")
    assert ws_res.status_code == 200
    assert b"CloudTrail Investigation" in ws_res.data

    state_res = client.get("/api/labs/LAB-004/state")
    assert state_res.status_code == 200
    assert state_res.content_type.startswith("application/json")
    assert state_res.get_json()["lab_id"] == "LAB-004"


def test_unauthenticated_api_request_returns_json_401(db_url):
    """10. Unauthenticated API requests return JSON 401, not HTML."""
    app = create_app("testing")
    client = app.test_client()

    response = client.get("/api/labs/LAB-001/state")
    assert response.status_code == 401
    assert response.content_type.startswith("application/json")
    data = response.get_json()
    assert data["error"] == "Authentication required"


def test_invalid_lab_id_returns_json_404(db_url):
    """11. Invalid lab ID returns JSON 404, not HTML."""
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    # Invalid lab metadata
    response = client.get("/api/labs/NON_EXISTENT_LAB")
    assert response.status_code == 404
    assert response.content_type.startswith("application/json")
    data = response.get_json()
    assert "error" in data

    # Invalid lab start
    start_resp = client.post("/api/labs/NON_EXISTENT_LAB/start", headers={"X-CSRFToken": csrf(client)})
    assert start_resp.status_code == 404
    assert start_resp.content_type.startswith("application/json")
    assert "error" in start_resp.get_json()


def test_cross_user_lab_access_isolation(db_url):
    """12. Cross-user lab access: User A session cannot be accessed by User B."""
    app = create_app("testing")
    client_a = app.test_client()
    client_b = app.test_client()

    # User A registers and starts LAB-001
    register_user(client_a, username="student_a", email="student_a@example.com")
    start_a = client_a.post("/api/labs/LAB-001/start", headers={"X-CSRFToken": csrf(client_a)})
    assert start_a.status_code == 200
    session_a_id = start_a.get_json()["session_id"]

    # User B registers
    register_user(client_b, username="student_b", email="student_b@example.com")

    # User B tries to hijack User A's session by injecting session_id into cookies
    with client_b.session_transaction() as sess:
        sess["lab_session_id"] = session_a_id
        sess["lab_id"] = "LAB-001"

    # User B attempts to fetch resources from User A's session
    resp_b = client_b.get("/api/labs/LAB-001/resources")
    assert resp_b.status_code in {403, 404}
    assert resp_b.content_type.startswith("application/json")
    assert "error" in resp_b.get_json()


def test_learn_before_you_practice_theory_rendered_all_labs(db_url):
    """13. Verify 'Learn Before You Practice' theory section renders on all lab overview pages."""
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    lab_slugs = [
        ("public-s3-bucket", "LAB-001", "Amazon Simple Storage Service"),
        ("excessive-iam-permissions", "LAB-002", "AWS Identity and Access Management"),
        ("insecure-security-group", "LAB-003", "Amazon EC2 Security Groups"),
        ("cloudtrail-investigation", "LAB-004", "AWS CloudTrail is an auditing and governance service"),
    ]


    for slug, lab_id, concept_keyword in lab_slugs:
        resp = client.get(f"/labs/{slug}")
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "Learn Before You Practice" in html
        assert "Architectural Concept" in html
        assert "Threat Model &amp; Risk" in html
        assert "Investigation Strategy" in html
        assert "Command Reference Guide" in html
        assert "Defense &amp; Remediation" in html
        assert "Core Learning Objectives" in html
        assert concept_keyword in html


def test_learning_commands_are_all_valid_and_executable_in_simulator(db_url):
    """14. Verify all commands in learning section are allowed by command engine and have valid structure."""
    from app.services.command_engine import is_allowed_command

    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    lab_ids = ["LAB-001", "LAB-002", "LAB-003", "LAB-004"]
    for lab_id in lab_ids:
        resp = client.get(f"/api/labs/{lab_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "learning" in data
        learning = data["learning"]

        # Validate required schema sections
        assert "concept" in learning
        assert "security_risk" in learning
        assert "what_you_will_investigate" in learning
        assert "commands" in learning
        assert "defense" in learning
        assert "key_takeaways" in learning

        # Validate commands
        assert len(learning["commands"]) >= 4
        for cmd_info in learning["commands"]:
            cmd_str = cmd_info["command"]
            example_str = cmd_info.get("example") or cmd_str
            assert "purpose" in cmd_info and len(cmd_info["purpose"]) > 10
            why_text = cmd_info.get("why_used") or cmd_info.get("explanation") or cmd_info.get("why")
            assert why_text and len(why_text) > 10
            # Executable example command must be allowed by the simulator engine
            assert is_allowed_command(example_str), f"Command example '{example_str}' in {lab_id} is not recognized by is_allowed_command"



