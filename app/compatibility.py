"""Compatibility routes for legacy templates and smoke scripts.

These adapters preserve old URLs while the application factory remains the only
Flask runtime. New product behavior belongs in the modular blueprints/services.
"""
from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

compat_bp = Blueprint("compatibility", __name__)


def get_local_chatbot_response(message, lab_name):
    return jsonify({"reply": "Use the simulator to investigate the lab. Start with `aws s3 ls`, then inspect the bucket policy and public access settings."})


def call_openai_api(message, lab_name):
    return None


def _legacy_commands(mode):
    if mode == "defense":
        return [{"name": "Block public access", "pattern": "aws s3api put-public-access-block", "description": "Restrict public bucket access.", "example": "aws s3api put-public-access-block --bucket cads-public-data", "level": "Beginner", "category": "Defense"}]
    return [{"name": "List S3 buckets", "pattern": "aws s3 ls", "description": "Enumerate S3 buckets.", "example": "aws s3 ls", "level": "Beginner", "category": "Reconnaissance"}]


@compat_bp.route("/lab/<lab_id>/start", methods=["GET", "POST"])
def legacy_lab_start(lab_id):
    session["legacy_lab_id"] = lab_id
    session["legacy_mode"] = request.form.get("mode", "attack")
    session["legacy_cheatsheet_views"] = session.get("legacy_cheatsheet_views", {})
    session["legacy_cheatsheet_views"][lab_id] = 0
    session["terminal_output"] = []
    return redirect(url_for("compatibility.legacy_terminal"))


@compat_bp.route("/terminal", methods=["GET", "POST"])
def legacy_terminal():
    output = session.setdefault("terminal_output", [])
    if request.method == "POST":
        command = " ".join(str(request.form.get("command", "")).split())
        output.append(f"$ {command}")
        output.append("CADS Simulator: use the modular cloud terminal API for active labs.")
        session.modified = True
    return render_template("terminal.html", output=output)


@compat_bp.route("/cheatsheet_api")
def legacy_cheatsheet_api():
    lab_id = session.get("legacy_lab_id", "s3")
    counters = session.setdefault("legacy_cheatsheet_views", {})
    views = int(counters.get(lab_id, 0))
    if views >= 3:
        return jsonify({"message": "Rate limit reached. Try again later.", "remaining_free_views": 0}), 429
    counters[lab_id] = views + 1
    session.modified = True
    mode = session.get("legacy_mode", "attack")
    return jsonify({"commands": _legacy_commands(mode), "mode": mode, "remaining_free_views": 2 - views, "lab": lab_id})


@compat_bp.route("/api/terminal_execute", methods=["POST"])
def legacy_terminal_execute():
    payload = request.get_json(silent=True) or {}
    command = str(payload.get("command", "")).strip()
    outputs = []
    if command.lower() == "aws s3 ls":
        outputs = ["2026-09-24 10:21:33 cads-public-data"]
    elif command.lower().startswith("nmap"):
        outputs = ["CADS Simulator: simulated network scan completed."]
    elif command.lower() == "whoami":
        outputs = ["student"]
    elif command.lower() == "help":
        outputs = ["Available simulated commands: aws s3 ls, nmap, whoami, help"]
    else:
        outputs = ["CADS Simulator: command handled by compatibility adapter."]
    session.setdefault("terminal_output", []).extend([f"$ {command}", *outputs])
    return jsonify({"new_lines": [f"$ {command}", *outputs], "ai_analysis": "", "lab_state": "recon", "score": 0, "mode": session.get("legacy_mode", "attack"), "outcome": "simulated"})


@compat_bp.route("/api/logs")
def legacy_logs():
    return jsonify({"events": [], "lab_state": session.get("legacy_lab_id")})


@compat_bp.route("/chatbot_api", methods=["POST"])
def chatbot_api():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not session.get("legacy_lab_id") and not session.get("lab_session_id"):
        return jsonify({"reply": "Please start a lab session first."})
    if any(term in message.lower() for term in ("ddos", "ransomware", "malware")):
        return jsonify({"reply": "I can help with defensive cloud-security investigation and simulator commands, but not harmful actions."})
    return get_local_chatbot_response(message, session.get("legacy_lab_id", "LAB-001"))
