import json

from flask import Blueprint, current_app, jsonify, render_template, request, session

from app.security.auth import csrf_protected, current_user, login_required
from app.services.lab_engine import LabEngine, get_lab_by_slug
from app.services.lab_engine import get_lab_session

labs_bp = Blueprint("labs", __name__)
_engine = LabEngine()


def _lab_engine():
    return current_app.extensions.get("lab_engine", _engine)


@labs_bp.route("/api/labs")
def list_labs():
    data = []
    for lab_id in ["LAB-001", "LAB-002", "LAB-003", "LAB-004"]:
        try:
            lab = _lab_engine().load_lab(lab_id)
        except ValueError:
            continue
        data.append({
            "id": lab.get("id"),
            "slug": lab.get("slug"),
            "title": lab.get("title"),
            "description": lab.get("scenario", ""),
            "difficulty": lab.get("difficulty", "beginner"),
            "xp": lab.get("xp", 100),
            "modes": ["cloud"],
            "category": lab.get("category", "Cloud Security"),
            "status": "IN PROGRESS" if session.get("lab_id") == lab.get("id") else "NOT STARTED",
        })
    return jsonify({"labs": data})


@labs_bp.route("/api/labs/<lab_id>/start", methods=["POST"])
@login_required
@csrf_protected
def start_lab(lab_id):
    engine = _lab_engine()
    lab = engine.load_lab(lab_id)
    session_id = engine.start_session(lab_id, current_user()["id"])
    session["lab_id"] = lab["id"]
    session["lab_session_id"] = session_id
    return jsonify({"status": "started", "session_id": session_id, "lab": engine.initialize_lab(lab_id)})


@labs_bp.route("/api/labs/<lab_id>/state")
@login_required
def get_lab_state(lab_id):
    session_id, error = _session_or_404(lab_id)
    if error:
        return error
    return jsonify(_lab_engine().get_lab_state(session_id))


@labs_bp.route("/api/labs/<lab_id>")
def get_lab_details(lab_id):
    try:
        return jsonify(_lab_engine().load_lab(lab_id))
    except ValueError:
        return jsonify({"error": "Lab not found"}), 404


@labs_bp.route("/api/labs/<lab_id>/resources")
@login_required
def get_lab_resources(lab_id):
    session_id, error = _session_or_404(lab_id)
    if error:
        return error
    return jsonify({"resources": _lab_engine().provider.list_resources(session_id)})


@labs_bp.route("/api/labs/<lab_id>/events")
@login_required
def get_lab_events(lab_id):
    session_id, error = _session_or_404(lab_id)
    if error:
        return error
    events = _lab_engine().provider.list_events(session_id)
    service = request.args.get("service")
    severity = request.args.get("severity")
    outcome = request.args.get("outcome")
    event_name = request.args.get("event")
    if service:
        events = [item for item in events if item.get("service") == service]
    if severity:
        events = [item for item in events if item.get("severity") == severity]
    if outcome:
        events = [item for item in events if item.get("outcome") == outcome]
    if event_name:
        events = [item for item in events if item.get("event_name") == event_name]
    return jsonify({"events": sorted(events, key=lambda item: item["timestamp"])})


@labs_bp.route("/api/labs/<lab_id>/progress")
@login_required
def get_lab_progress(lab_id):
    session_id, error = _session_or_404(lab_id)
    if error:
        return error
    engine = _lab_engine()
    objectives = engine.check_objectives(session_id)
    passed = sum(item["status"] == "PASS" for item in objectives.values())
    return jsonify({"passed": passed, "total": len(objectives), "percent": round((passed / len(objectives)) * 100) if objectives else 0, "objectives": objectives})


@labs_bp.route("/api/labs/<lab_id>/verify")
@login_required
def verify_lab(lab_id):
    session_id, error = _session_or_404(lab_id)
    if error:
        return error
    return jsonify({"objectives": _lab_engine().check_objectives(session_id), "completion": _lab_engine().complete_lab(session_id)})


@labs_bp.route("/api/labs/<lab_id>/reset", methods=["POST"])
@login_required
@csrf_protected
def reset_lab(lab_id):
    session_id, error = _session_or_404(lab_id)
    if error:
        return error
    return jsonify(_lab_engine().reset_lab(session_id))


def _session_or_404(lab_id):
    session_id = session.get("lab_session_id")
    user = current_user()
    record = get_lab_session(session_id, current_app.config.get("DATABASE_URL")) if session_id else None
    if not session_id or not user or session.get("lab_id") not in {lab_id, str(lab_id)} or not record or str(record.get("user_id")) != str(user["id"]):
        return None, (jsonify({"error": "No active lab session"}), 404)
    return session_id, None


@labs_bp.route("/api/labs/<lab_id>/findings")
@login_required
def list_findings(lab_id):
    session_id, error = _session_or_404(lab_id)
    if error:
        return error
    findings = current_app.extensions["lab_engine"].finding_engine.list_findings(session_id)
    return jsonify({"findings": findings})


@labs_bp.route("/api/labs/<lab_id>/findings/<finding_id>")
@login_required
def get_finding(lab_id, finding_id):
    session_id, error = _session_or_404(lab_id)
    if error:
        return error
    details = current_app.extensions["investigation_service"].get_details(session_id, finding_id)
    return jsonify(details) if details else (jsonify({"error": "Finding not found"}), 404)


@labs_bp.route("/api/labs/<lab_id>/findings/<finding_id>/evidence")
@login_required
def get_finding_evidence(lab_id, finding_id):
    session_id, error = _session_or_404(lab_id)
    if error:
        return error
    finding = current_app.extensions["investigation_service"].get_finding(session_id, finding_id)
    return jsonify({"evidence": finding["evidence"]}) if finding else (jsonify({"error": "Finding not found"}), 404)


@labs_bp.route("/api/labs/<lab_id>/findings/<finding_id>/investigate", methods=["POST"])
@login_required
@csrf_protected
def investigate_finding(lab_id, finding_id):
    session_id, error = _session_or_404(lab_id)
    if error:
        return error
    details = current_app.extensions["investigation_service"].investigate(session_id, finding_id)
    return jsonify(details) if details else (jsonify({"error": "Finding not found"}), 404)


@labs_bp.route("/api/labs/<lab_id>/findings/<finding_id>/remediate", methods=["POST"])
@login_required
@csrf_protected
def remediate_finding(lab_id, finding_id):
    session_id, error = _session_or_404(lab_id)
    if error:
        return error
    finding = current_app.extensions["investigation_service"].get_finding(session_id, finding_id)
    if not finding:
        return jsonify({"error": "Finding not found"}), 404
    defense = current_app.extensions["defense_engine"]
    rule_id = finding["rule_id"]
    if rule_id in {"S3-PUBLIC-ACCESS", "S3-SENSITIVE-OBJECT"}:
        event = defense.enable_s3_public_access_block(session_id, finding.get("resource_id") or "cads-public-data")
    elif rule_id in {"IAM-EXCESSIVE-PERMISSIONS", "IAM-PRIVILEGE-ESCALATION"}:
        event = defense.remediate_iam_policy(session_id, finding.get("resource_id") or "student-user")
    elif rule_id == "EC2-OPEN-SSH":
        event = defense.remediate_security_group(session_id, finding.get("resource_id") or "sg-cads-web")
    elif rule_id == "CLOUDTRAIL-SUSPICIOUS-ACTIVITY":
        event = defense.remediate_compromised_identity(session_id, finding.get("resource_id") or "compromised-user")
    else:
        return jsonify({"error": "No remediation is available for this finding"}), 400
    current_app.extensions["lab_engine"].event_processor.reevaluate(session_id)
    return jsonify({"status": "remediated", "event": event, "finding": current_app.extensions["investigation_service"].get_finding(session_id, finding_id)})


@labs_bp.route("/api/labs/<lab_id>/timeline")
@login_required
def get_timeline(lab_id):
    session_id, error = _session_or_404(lab_id)
    if error:
        return error
    return jsonify({"events": current_app.extensions["investigation_service"].get_timeline(session_id)})


@labs_bp.route("/labs")
def labs_page():
    return render_template("labs.html")


@labs_bp.route("/labs/<slug>")
def lab_detail(slug):
    lab = get_lab_by_slug(slug)
    if not lab:
        return jsonify({"error": "Lab not found"}), 404
    return render_template("lab_overview.html", lab=lab)


@labs_bp.route("/lab/<lab_id>")
def lab_workspace(lab_id):
    try:
        lab = _lab_engine().load_lab(lab_id)
    except ValueError:
        return jsonify({"error": "Lab not found"}), 404
    return render_template("lab_workspace.html", lab=lab)
