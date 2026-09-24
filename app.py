"""CADS development entrypoint.

The application factory in ``app`` is the single authoritative runtime.
"""
from app import app


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False), use_reloader=False)
