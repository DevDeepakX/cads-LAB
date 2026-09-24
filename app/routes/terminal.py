from flask import Blueprint, current_app, jsonify, request, session

from app.security.auth import csrf_protected, login_required
from app.services.cloud_simulator import ALLOWED_COMMANDS, is_allowed_command
from app.services.command_engine import CommandEngine

terminal_bp = Blueprint("terminal", __name__)
_engine = CommandEngine()


@terminal_bp.route("/api/terminal/command", methods=["POST"])
@login_required
@csrf_protected
def execute_command():
    payload = request.get_json(silent=True) or {}
    command = str(payload.get("command", "")).strip()
    if not command:
        return jsonify({"error": "command is required"}), 400

    if not is_allowed_command(command):
        return jsonify({
            "status": "denied",
            "message": "Command is not allowed in this lab environment.",
            "allowed_commands": sorted(ALLOWED_COMMANDS),
        }), 403

    session_id = session.get("lab_session_id")
    result = current_app.extensions.get("command_engine", _engine).execute(session_id, command)
    current_app.extensions.get("lab_engine").record_activity(session_id)
    return jsonify({"status": result.get("status", "ok"), "command": command, "simulated": True, **result})
