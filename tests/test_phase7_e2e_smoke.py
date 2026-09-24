import pytest
from app import create_app


@pytest.fixture
def db_url(tmp_path, monkeypatch):
    value = f"sqlite:///{tmp_path / 'phase7_e2e.db'}"
    monkeypatch.setenv("TEST_DATABASE_URL", value)
    return value


def csrf(client):
    with client.session_transaction() as state:
        return state["csrf_token"]


def register(client, username="p7student", email="p7student@example.com"):
    client.get("/register")
    return client.post(
        "/register",
        json={"username": username, "email": email, "password": "secure-password-123"},
        headers={"X-CSRFToken": csrf(client)},
    )


def login(client, identifier="p7student"):
    client.get("/login")
    return client.post(
        "/login",
        json={"identifier": identifier, "password": "secure-password-123"},
        headers={"X-CSRFToken": csrf(client)},
    )


def test_phase7_full_platform_e2e_all_labs(db_url):
    app = create_app("testing")
    client = app.test_client()

    # 1. Register & Check Dashboard
    res = register(client)
    assert res.status_code == 200

    dash_res = client.get("/api/dashboard").get_json()
    assert len(dash_res["labs"]) == 4
    lab_ids = [l["id"] for l in dash_res["labs"]]
    assert set(lab_ids) == {"LAB-001", "LAB-002", "LAB-003", "LAB-004"}
    assert dash_res["progress"]["completed"] == 0

    # -------------------------------------------------------------
    # 2. LAB-001: Public S3 Bucket Discovery & Hardening
    # -------------------------------------------------------------
    client.post("/api/labs/LAB-001/start", headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws s3 ls"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws s3api get-public-access-block --bucket cads-confidential-assets-prod"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws s3 cp s3://cads-confidential-assets-prod/customer_pii_export.csv local.csv"}, headers={"X-CSRFToken": csrf(client)})

    findings_001 = client.get("/api/labs/LAB-001/findings").get_json()["findings"]
    assert any(f["rule_id"] == "S3-PUBLIC-ACCESS" for f in findings_001)

    # Remediate S3
    f001_id = findings_001[0].get("finding_id") or findings_001[0].get("id")
    rem_001 = client.post(f"/api/labs/LAB-001/findings/{f001_id}/remediate", headers={"X-CSRFToken": csrf(client)})
    assert rem_001.status_code == 200

    # Verify S3
    ver_001 = client.get("/api/labs/LAB-001/verify").get_json()
    assert ver_001["completion"]["status"] == "completed"

    # -------------------------------------------------------------
    # 3. LAB-002: Excessive IAM Permissions & Privilege Escalation
    # -------------------------------------------------------------
    client.post("/api/labs/LAB-002/start", headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws iam list-users"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws iam list-attached-user-policies --user-name dev-contractor-01"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws iam get-policy --policy-arn arn:aws:iam::123456789012:policy/ContractorPrivilegeEscalationPolicy"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws iam attach-user-policy --user-name dev-contractor-01 --policy-arn arn:aws:iam::aws:policy/AdministratorAccess"}, headers={"X-CSRFToken": csrf(client)})

    findings_002 = client.get("/api/labs/LAB-002/findings").get_json()["findings"]
    assert any(f["rule_id"] == "IAM-PRIVILEGE-ESCALATION" for f in findings_002)

    # Remediate IAM
    f002_id = findings_002[0].get("finding_id") or findings_002[0].get("id")
    rem_002 = client.post(f"/api/labs/LAB-002/findings/{f002_id}/remediate", headers={"X-CSRFToken": csrf(client)})
    assert rem_002.status_code == 200

    # Verify IAM
    ver_002 = client.get("/api/labs/LAB-002/verify").get_json()
    assert ver_002["completion"]["status"] == "completed"

    # -------------------------------------------------------------
    # 4. LAB-003: Insecure Security Group Remediation
    # -------------------------------------------------------------
    client.post("/api/labs/LAB-003/start", headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws ec2 describe-security-groups"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws ec2 describe-instances"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws ec2 describe-security-group-rules"}, headers={"X-CSRFToken": csrf(client)})

    findings_003 = client.get("/api/labs/LAB-003/findings").get_json()["findings"]
    assert any(f["rule_id"] == "EC2-OPEN-SSH" for f in findings_003)

    # Remediate SG
    f003_id = findings_003[0].get("finding_id") or findings_003[0].get("id")
    rem_003 = client.post(f"/api/labs/LAB-003/findings/{f003_id}/remediate", headers={"X-CSRFToken": csrf(client)})
    assert rem_003.status_code == 200

    # Verify SG
    ver_003 = client.get("/api/labs/LAB-003/verify").get_json()
    assert ver_003["completion"]["status"] == "completed"

    # -------------------------------------------------------------
    # 5. LAB-004: CloudTrail Threat Investigation & Response
    # -------------------------------------------------------------
    client.post("/api/labs/LAB-004/start", headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws cloudtrail describe-trails"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws cloudtrail lookup-events"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws cloudtrail lookup-events --username compromised-user"}, headers={"X-CSRFToken": csrf(client)})
    client.post("/api/terminal/command", json={"command": "aws cloudtrail lookup-events --event-name AttachUserPolicy"}, headers={"X-CSRFToken": csrf(client)})

    findings_004 = client.get("/api/labs/LAB-004/findings").get_json()["findings"]
    f004 = next(f for f in findings_004 if f["rule_id"] == "CLOUDTRAIL-SUSPICIOUS-ACTIVITY")
    f004_id = f004.get("finding_id") or f004.get("id")

    # Investigate & Remediate CloudTrail incident
    client.post(f"/api/labs/LAB-004/findings/{f004_id}/investigate", headers={"X-CSRFToken": csrf(client)})
    rem_004 = client.post(f"/api/labs/LAB-004/findings/{f004_id}/remediate", headers={"X-CSRFToken": csrf(client)})
    assert rem_004.status_code == 200

    # Verify CloudTrail
    ver_004 = client.get("/api/labs/LAB-004/verify").get_json()
    assert ver_004["completion"]["status"] == "completed"

    # -------------------------------------------------------------
    # 6. Check Active Lab Progress
    # -------------------------------------------------------------
    dash_final = client.get("/api/dashboard").get_json()
    assert dash_final["current_lab"]["completed"] is True
    assert dash_final["current_lab"]["progress"] == 100

    # -------------------------------------------------------------
    # 7. Dynamic Reset Verification (Reset LAB-003)
    # -------------------------------------------------------------
    client.post("/api/labs/LAB-003/start", headers={"X-CSRFToken": csrf(client)})
    reset_res = client.post("/api/labs/LAB-003/reset", headers={"X-CSRFToken": csrf(client)})
    assert reset_res.status_code == 200

    dash_after_reset = client.get("/api/dashboard").get_json()
    assert dash_after_reset["current_lab"]["completed"] is False

    # LAB-003 should have open SSH ingress again
    sg_res = client.get("/api/labs/LAB-003/resources").get_json()["resources"]
    sg = next(r for r in sg_res if r["resource_name"] == "sg-cads-web")
    assert any(rule.get("source") == "0.0.0.0/0" and rule.get("port") == 22 for rule in sg["configuration"].get("inbound_rules", []))

    # -------------------------------------------------------------
    # 8. Cross-User Isolation Verification
    # -------------------------------------------------------------
    client2 = app.test_client()
    register(client2, username="p7other", email="p7other@example.com")
    dash_user2 = client2.get("/api/dashboard").get_json()
    assert dash_user2["progress"]["completed"] == 0
    assert dash_user2["current_lab"] is None
