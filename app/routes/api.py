from flask import Blueprint, jsonify

api_bp = Blueprint("api", __name__)


@api_bp.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "CADS foundation", "version": "phase-1"})


@api_bp.route("/api/foundation")
def foundation_status():
    return jsonify({
        "status": "ready",
        "architecture": "modular-foundation",
        "database": "sqlite",
        "features": [
            "app-factory",
            "labs-model",
            "lab-session-model",
            "cloud-resource-model",
            "cloud-event-model",
            "command-allowlist"
        ],
    })
