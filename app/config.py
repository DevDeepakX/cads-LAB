import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]


class BaseConfig:
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY") or "development-secret-change-me"
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'database.db'}")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    DATABASE_URL = os.getenv("TEST_DATABASE_URL", f"sqlite:///{BASE_DIR / 'test_cads.db'}")
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


def get_config(config_name: str | None = None):
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    config_map = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
        "default": DevelopmentConfig,
    }
    selected = config_map.get(config_name, DevelopmentConfig)
    if config_name == "testing":
        selected.DATABASE_URL = os.getenv("TEST_DATABASE_URL", selected.DATABASE_URL)
    return selected
