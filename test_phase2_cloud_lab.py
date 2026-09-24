import json

from app.services.cloud_provider import SimulatorProvider
from app.services.command_engine import CommandEngine
from app.services.lab_engine import LabEngine, load_lab_definition
from app.services.verification_engine import verify_objectives


def test_simulator_session_isolation():
    provider = SimulatorProvider()
    session_a = "session-A"
    session_b = "session-B"

    provider.create_resource(session_a, "S3_BUCKET", "cads-public-data", configuration={"public_access": True})
    provider.create_resource(session_b, "S3_BUCKET", "private-data", configuration={"public_access": False})

    resources_a = provider.list_resources(session_a)
    resources_b = provider.list_resources(session_b)

    assert any(r["resource_name"] == "cads-public-data" for r in resources_a)
    assert all(r["resource_name"] != "cads-public-data" for r in resources_b)


def test_command_engine_handles_supported_and_unsupported_commands():
    provider = SimulatorProvider()
    engine = CommandEngine(provider)
    provider.create_resource("session-123", "S3_BUCKET", "cads-public-data", configuration={"public_access": True})

    response = engine.execute("session-123", "aws s3 ls")
    assert response["status"] == "ok"
    assert "cads-public-data" in response["output"]

    unsupported = engine.execute("session-123", "aws s3 cp s3://bucket/key /tmp/file")
    assert unsupported["status"] == "unsupported"
    assert "Command not supported in this lab environment" in unsupported["output"]


def test_lab_definition_and_objectives_load():
    lab = load_lab_definition("public-s3-bucket")
    assert lab["id"] == "LAB-001"
    assert lab["slug"] == "public-s3-bucket"
    assert len(lab["objectives"]) >= 4

    engine = LabEngine()
    session_id = engine.start_session("LAB-001", "student-demo")
    assert session_id
    state = engine.get_lab_state(session_id)
    assert state["lab_id"] == "LAB-001"
    assert state["resources"][0]["resource_name"] == "cads-public-data"


def test_lab_reset_restores_vulnerability():
    engine = LabEngine()
    session_id = engine.start_session("LAB-001", "student-demo")
    provider = engine.provider
    provider.update_resource(session_id, "cads-public-data", {"public_access": False})

    engine.reset_lab(session_id)
    bucket = provider.get_resource(session_id, "cads-public-data")
    assert bucket["configuration"]["public_access"] is True


def test_complete_lab_flow_verifies_objectives():
    engine = LabEngine()
    session_id = engine.start_session("LAB-001", "student-demo")
    provider = engine.provider

    provider.update_resource(session_id, "cads-public-data", {"public_access": True, "encryption": False, "logging": False})
    provider.create_event(session_id, "S3", "ListAllMyBuckets", "student", "S3_BUCKET", "SUCCESS", "LOW")
    provider.create_event(session_id, "S3", "GetBucketPolicy", "student", "S3_BUCKET", "SUCCESS", "MEDIUM")

    result = verify_objectives(session_id, provider)
    assert result["OBJ-001"]["status"] == "PASS"
    assert result["OBJ-002"]["status"] == "PASS"
    assert result["OBJ-004"]["status"] == "FAIL"

    provider.update_resource(session_id, "cads-public-data", {"public_access": False, "encryption": True, "logging": True})
    result = verify_objectives(session_id, provider)
    assert result["OBJ-004"]["status"] == "PASS"
    assert engine.complete_lab(session_id)["status"] in {"completed", "ready"}
