import re

import pytest

from app import create_app


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("TEST_DATABASE_URL", f"sqlite:///{tmp_path / 'cads.db'}")
    return create_app("testing").test_client()


def csrf(client):
    with client.session_transaction() as state:
        return state["csrf_token"]


def register(client, username, email):
    client.get("/register")
    token = csrf(client)
    return client.post("/register", json={"username": username, "email": email, "password": "correct-horse"}, headers={"X-CSRFToken": token})


def login(client, identifier, password="correct-horse"):
    client.get("/login")
    return client.post("/login", json={"identifier": identifier, "password": password}, headers={"X-CSRFToken": csrf(client)})


def test_registration_hashes_password_and_login_logout(client):
    response = register(client, "auth-student", "auth@example.com")
    assert response.status_code == 200
    assert client.get("/api/me").get_json()["user"]["username"] == "auth-student"

    client.post("/logout", headers={"X-CSRFToken": csrf(client)})
    assert client.get("/dashboard").status_code == 302
    assert login(client, "auth-student").status_code == 200


def test_invalid_login_and_duplicate_account_are_generic(client):
    assert register(client, "duplicate-student", "duplicate@example.com").status_code == 200
    client.post("/logout", headers={"X-CSRFToken": csrf(client)})
    assert login(client, "duplicate-student", "wrong-password").status_code == 401
    assert register(client, "duplicate-student", "duplicate@example.com").status_code == 409


def test_unauthenticated_lab_and_dashboard_access_is_rejected(client):
    assert client.get("/dashboard").status_code == 302
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/labs/LAB-001/resources").status_code == 401


def test_state_changing_requests_require_csrf(client):
    register(client, "csrf-student", "csrf@example.com")
    assert client.post("/api/labs/LAB-001/start").status_code == 400
