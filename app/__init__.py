from flask import Flask
from flask import jsonify, request

from .config import get_config
from .routes.api import api_bp
from .routes.auth import auth_bp
from .routes.dashboard import dashboard_bp
from .routes.labs import labs_bp
from .routes.terminal import terminal_bp
from .compatibility import compat_bp
from .services.database import initialize_database
from .services.cloud_provider import SimulatorProvider
from .services.lab_engine import LabEngine
from .services.command_engine import CommandEngine
from .services.defense_engine import DefenseEngine
from .services.investigation_service import InvestigationService
from .security.auth import csrf_token, current_user


def create_app(config_name: str | None = None):
    """Create and configure the Flask application using the app factory pattern."""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    config = get_config(config_name)
    app.config.from_object(config)

    # Keep the app secret key in configuration and environment variables only.
    app.secret_key = app.config.get("SECRET_KEY") or "development-secret-change-me"
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("SESSION_COOKIE_SECURE", False)

    initialize_database(app.config.get("DATABASE_URL"))

    provider = SimulatorProvider(app.config.get("DATABASE_URL"))
    app.extensions["cloud_provider"] = provider
    app.extensions["lab_engine"] = LabEngine(provider)
    app.extensions["command_engine"] = CommandEngine(provider)
    app.extensions["defense_engine"] = DefenseEngine(provider)
    app.extensions["investigation_service"] = InvestigationService(provider, app.extensions["lab_engine"].finding_engine)

    @app.context_processor
    def inject_auth_context():
        return {"csrf_token": csrf_token, "current_user": current_user}

    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(compat_bp)
    app.register_blueprint(labs_bp)
    app.register_blueprint(terminal_bp)

    @app.route("/health")
    def health():
        return {"status": "ok", "app": "CADS", "mode": app.config.get("ENV", "development")}

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Authentication required"}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": "Forbidden"}), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        return "Not found", 404

    @app.errorhandler(409)
    def conflict(error):
        return jsonify({"error": "Conflict"}), 409

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        if request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json":
            return jsonify({"error": str(error)}), 400
        return str(error), 400

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception("Unhandled application error")
        if request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json":
            return jsonify({"error": "Internal server error"}), 500
        return "Internal server error", 500

    return app


app = create_app()
