import json
import secrets
from functools import wraps
from typing import Any

from flask import abort, current_app, jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.services.database import get_db_connection


def csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def csrf_protected(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        supplied = request.headers.get("X-CSRFToken") or request.form.get("csrf_token") or (request.get_json(silent=True) or {}).get("csrf_token")
        if not supplied or not secrets.compare_digest(supplied, csrf_token()):
            return jsonify({"error": "CSRF validation failed"}), 400
        return view(*args, **kwargs)
    return wrapped


def csrf_valid():
    supplied = request.headers.get("X-CSRFToken") or request.form.get("csrf_token") or (request.get_json(silent=True) or {}).get("csrf_token")
    return bool(supplied) and secrets.compare_digest(supplied, csrf_token())


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    conn = get_db_connection(current_app.config.get("DATABASE_URL"))
    row = conn.execute("SELECT id, username, email, role, is_active, created_at, updated_at FROM users WHERE id = ? AND is_active = 1", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def login_user(user):
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["csrf_token"] = secrets.token_urlsafe(32)
    conn = get_db_connection(current_app.config.get("DATABASE_URL"))
    row = conn.execute("SELECT session_id, lab_id, metadata FROM lab_sessions WHERE user_id = ? ORDER BY last_activity_at DESC, started_at DESC LIMIT 1", (user["id"],)).fetchone()
    conn.close()
    if row:
        session["lab_session_id"] = row["session_id"]
        metadata = json.loads(row["metadata"] or "{}")
        session["lab_id"] = metadata.get("lab_id", row["lab_id"])


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            if request.accept_mimetypes.best == "application/json" or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def password_hash(password):
    return generate_password_hash(password)


def verify_password(password_hash_value, password):
    return check_password_hash(password_hash_value or "", password)


def validate_user_input(value: Any, max_length: int = 2000):
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) > max_length:
        raise ValueError("Input exceeds the allowed size.")
    return text


def require_lab_access(user_id: str | int | None, lab_id: str | int | None):
    if user_id is None or lab_id is None:
        abort(403)
    return True


def enforce_safe_command(command: str) -> str:
    cleaned = str(command or "").strip()
    if len(cleaned) > 1000:
        raise ValueError("Command exceeds the maximum safe length.")
    if "&&" in cleaned or "|" in cleaned or ";" in cleaned:
        raise ValueError("Unsafe shell chaining is not permitted.")
    return cleaned
