from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for

from app.security.auth import csrf_protected, csrf_valid, current_user, login_user, password_hash, verify_password
from app.services.database import get_db_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/health")
def auth_health():
    return jsonify({"status": "ok", "module": "auth-foundation"})


@auth_bp.route("/")
def index():
    if current_user():
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if current_user():
            return redirect(url_for("dashboard.dashboard"))
        return render_template("auth.html", mode="register")
    if not csrf_valid():
        return jsonify({"error": "CSRF validation failed"}), 400
    payload = request.get_json(silent=True) or request.form
    username = str(payload.get("username", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    if len(username) < 3 or len(password) < 8 or "@" not in email:
        return jsonify({"error": "Enter a valid username, email, and password of at least 8 characters."}), 400
    conn = get_db_connection(current_app.config.get("DATABASE_URL"))
    try:
        now = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute("INSERT INTO users (username, email, password_hash, role, created_at, updated_at, is_active) VALUES (?, ?, ?, 'STUDENT', ?, ?, 1)", (username, email, password_hash(password), now, now))
        conn.commit()
        user = {"id": cursor.lastrowid, "username": username, "email": email}
    except Exception:
        conn.rollback()
        conn.close()
        return jsonify({"error": "Unable to create account. Username or email may already be in use."}), 409
    conn.close()
    login_user(user)
    return jsonify({"status": "registered", "user": user}) if request.is_json else redirect(url_for("dashboard.dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if current_user():
            return redirect(url_for("dashboard.dashboard"))
        return render_template("auth.html", mode="login")
    if not csrf_valid():
        return jsonify({"error": "CSRF validation failed"}), 400
    payload = request.get_json(silent=True) or request.form
    identifier = str(payload.get("identifier", payload.get("email", ""))).strip().lower()
    password = str(payload.get("password", ""))
    conn = get_db_connection(current_app.config.get("DATABASE_URL"))
    row = conn.execute("SELECT * FROM users WHERE lower(email) = ? OR lower(username) = ?", (identifier, identifier)).fetchone()
    conn.close()
    if not row or not row["is_active"] or not verify_password(row["password_hash"], password):
        return jsonify({"error": "Invalid credentials."}), 401
    login_user(dict(row))
    return jsonify({"status": "authenticated", "user": {"id": row["id"], "username": row["username"], "role": row["role"]}}) if request.is_json else redirect(url_for("dashboard.dashboard"))


@auth_bp.route("/logout", methods=["POST", "GET"])
@csrf_protected
def logout():
    session.clear()
    return jsonify({"status": "logged_out"}) if request.is_json else redirect(url_for("auth.login"))


@auth_bp.route("/api/me")
def me():
    user = current_user()
    return jsonify({"user": user}) if user else (jsonify({"error": "Authentication required"}), 401)
