from flask import Blueprint, current_app, jsonify, render_template, session

from app.services.lab_engine import load_lab_definition
from app.security.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


def _catalog():
    labs = []
    for lab_id in ["LAB-001", "LAB-002", "LAB-003", "LAB-004"]:
        lab = load_lab_definition(lab_id)
        if lab:
            labs.append(lab)
    return labs


def _dashboard_payload():
    engine = current_app.extensions["lab_engine"]
    session_id = session.get("lab_session_id")
    active_lab_id = session.get("lab_id")
    active = None
    if session_id and active_lab_id:
        try:
            state = engine.get_lab_state(session_id)
            objectives = engine.check_objectives(session_id)
            lab = engine.load_lab(active_lab_id)
            passed = sum(item["status"] == "PASS" for item in objectives.values())
            active = {
                "lab_id": lab["id"],
                "slug": lab["slug"],
                "title": lab["title"],
                "progress": round((passed / len(objectives)) * 100) if objectives else 0,
                "objectives_passed": passed,
                "objectives_total": len(objectives),
                "events": state["event_count"],
                "open_findings": sum(item["status"] != "RESOLVED" for item in state["findings"]),
                "completed": all(item["status"] == "PASS" for item in objectives.values()),
                "xp": lab.get("xp", 100) if all(item["status"] == "PASS" for item in objectives.values()) else 0,
                "recent_activity": state["events"][-6:][::-1],
            }
        except (KeyError, ValueError):
            active = None

    labs = _catalog()
    completed = 1 if active and active["completed"] else 0
    return {
        "progress": {"percent": active["progress"] if active else 0, "completed": completed, "total": len(labs)},
        "xp": active["xp"] if active else 0,
        "current_lab": active,
        "open_findings": active["open_findings"] if active else 0,
        "events": active["events"] if active else 0,
        "recent_activity": active["recent_activity"] if active else [],
        "labs": [{"id": item["id"], "slug": item["slug"], "title": item["title"], "category": item.get("category", "Cloud Security"), "xp": item.get("xp", 100)} for item in labs],
    }


@dashboard_bp.route("/api/dashboard")
@login_required
def dashboard_api():
    return jsonify(_dashboard_payload())


@dashboard_bp.route("/progress")
@login_required
def progress():
    return render_template("progress.html")


@dashboard_bp.route("/api/progress")
@login_required
def progress_api():
    payload = _dashboard_payload()
    categories = {}
    for lab in payload["labs"]:
        cat = lab["category"]
        if "Storage" in cat:
            category = "Storage Security"
        elif "Identity" in cat or "IAM" in cat:
            category = "IAM Security"
        elif "Network" in cat:
            category = "Network Security"
        elif "Logging" in cat or "Detection" in cat:
            category = "Logging & Detection"
        else:
            category = cat
        categories.setdefault(category, {"completed": 0, "total": 0})["total"] += 1
    if payload["current_lab"] and payload["current_lab"]["completed"]:
        current_id = payload["current_lab"]["lab_id"]
        current_lab_item = next((l for l in payload["labs"] if l["id"] == current_id), None)
        cat = current_lab_item["category"] if current_lab_item else "Storage Security"
        if "Storage" in cat:
            category = "Storage Security"
        elif "Identity" in cat or "IAM" in cat:
            category = "IAM Security"
        elif "Network" in cat:
            category = "Network Security"
        elif "Logging" in cat or "Detection" in cat:
            category = "Logging & Detection"
        else:
            category = cat
        if category in categories:
            categories[category]["completed"] += 1
    return jsonify({"overall": payload["progress"], "categories": categories, "labs": payload["labs"]})
