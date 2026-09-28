import pytest
from app import create_app


@pytest.fixture
def db_url(tmp_path, monkeypatch):
    value = f"sqlite:///{tmp_path / 'entry_flow.db'}"
    monkeypatch.setenv("TEST_DATABASE_URL", value)
    return value


def csrf(client):
    with client.session_transaction() as state:
        return state.get("csrf_token")


def register_user(client, username="entry-student", email="entry@example.com", password="password123"):
    client.get("/register")
    return client.post(
        "/register",
        json={"username": username, "email": email, "password": password},
        headers={"X-CSRFToken": csrf(client)},
    )


def login_user(client, identifier="entry-student", password="password123"):
    client.get("/login")
    return client.post(
        "/login",
        json={"identifier": identifier, "password": password},
        headers={"X-CSRFToken": csrf(client)},
    )


def test_root_unauthenticated_redirects_to_login(db_url):
    """1. GET / without authentication -> HTTP redirect to /login"""
    app = create_app("testing")
    client = app.test_client()

    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_get_login_returns_200(db_url):
    """3. GET /login -> HTTP 200"""
    app = create_app("testing")
    client = app.test_client()

    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in" in response.data or b"CADS" in response.data


def test_successful_login_and_root_authenticated_redirect(db_url):
    """2. GET / with authenticated session -> HTTP redirect to dashboard
    4. Successful login -> redirect to dashboard/lab catalog
    """
    app = create_app("testing")
    client = app.test_client()

    # Register first
    reg = register_user(client)
    assert reg.status_code == 200

    # User is logged in after registration; verify GET / redirects to /dashboard
    root_resp = client.get("/")
    assert root_resp.status_code == 302
    assert root_resp.headers["Location"].endswith("/dashboard")

    # Logout and log back in
    client.post("/logout", headers={"X-CSRFToken": csrf(client)})

    # Form-based login redirects to /dashboard
    client.get("/login")
    login_resp = client.post(
        "/login",
        data={"identifier": "entry-student", "password": "password123", "csrf_token": csrf(client)},
    )
    assert login_resp.status_code == 302
    assert login_resp.headers["Location"].endswith("/dashboard")

    # While authenticated, GET / redirects to /dashboard
    auth_root = client.get("/")
    assert auth_root.status_code == 302
    assert auth_root.headers["Location"].endswith("/dashboard")

    # While authenticated, GET /login redirects to /dashboard
    auth_login = client.get("/login")
    assert auth_login.status_code == 302
    assert auth_login.headers["Location"].endswith("/dashboard")


def test_dashboard_and_lab_catalog_available(db_url):
    """5. Dashboard/lab catalog -> HTTP 200
    6. Lab catalog contains LAB-001, LAB-002, LAB-003, LAB-004
    """
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    dash_page = client.get("/dashboard")
    assert dash_page.status_code == 200
    assert b"Dashboard" in dash_page.data or b"CADS" in dash_page.data

    labs_page = client.get("/labs")
    assert labs_page.status_code == 200
    assert b"Cloud security labs" in labs_page.data or b"Training catalog" in labs_page.data

    labs_api = client.get("/api/labs")
    assert labs_api.status_code == 200
    labs_data = labs_api.get_json()["labs"]
    lab_ids = [lab["id"] for lab in labs_data]
    assert "LAB-001" in lab_ids
    assert "LAB-002" in lab_ids
    assert "LAB-003" in lab_ids
    assert "LAB-004" in lab_ids


def test_lab_selection_and_workspace_navigation(db_url):
    """7. Selecting a lab opens the correct existing lab overview/workspace."""
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    # Check overview and workspace for each lab
    labs_to_check = [
        ("LAB-001", "public-s3-bucket", b"Public S3 Bucket"),
        ("LAB-002", "excessive-iam-permissions", b"Excessive IAM Permissions"),
        ("LAB-003", "insecure-security-group", b"Insecure Security Group"),
        ("LAB-004", "cloudtrail-investigation", b"CloudTrail Investigation"),
    ]

    for lab_id, slug, expected_title in labs_to_check:
        # Overview by slug
        overview_resp = client.get(f"/labs/{slug}")
        assert overview_resp.status_code == 200
        assert expected_title in overview_resp.data

        # Workspace by lab_id
        workspace_resp = client.get(f"/lab/{lab_id}")
        assert workspace_resp.status_code == 200
        assert expected_title in workspace_resp.data
        assert lab_id.encode() in workspace_resp.data


def test_logout_flow_and_post_logout_root_redirect(db_url):
    """8. Logout works.
    9. After logout: GET / -> /login
    """
    app = create_app("testing")
    client = app.test_client()
    register_user(client)

    # Verify currently authenticated
    assert client.get("/api/me").status_code == 200

    # Form Logout redirects to /login
    logout_resp = client.post("/logout", headers={"X-CSRFToken": csrf(client)})
    assert logout_resp.status_code == 302
    assert logout_resp.headers["Location"].endswith("/login")

    # api/me is now unauthorized
    assert client.get("/api/me").status_code == 401

    # Protected pages redirect to login
    assert client.get("/dashboard").status_code == 302
    assert client.get("/labs").status_code == 302

    # GET / redirects to /login
    post_logout_root = client.get("/")
    assert post_logout_root.status_code == 302
    assert post_logout_root.headers["Location"].endswith("/login")
