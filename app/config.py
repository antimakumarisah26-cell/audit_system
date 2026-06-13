"""
app/config.py
─────────────
Central configuration loaded from environment variables.
Never hardcode secrets — use .env locally, platform secrets in production.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///audit_system.db")

    # ── Auth ──────────────────────────────────────────────────────────────────
    DEFAULT_ADMIN_USERNAME: str = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

    # ── Email ─────────────────────────────────────────────────────────────────
    GMAIL_EMAIL: str = os.getenv("GMAIL_EMAIL", "")
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "")

    # ── App ───────────────────────────────────────────────────────────────────
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── ML ────────────────────────────────────────────────────────────────────
    RISK_HIGH_THRESHOLD: float = 66.0
    RISK_CRITICAL_THRESHOLD: float = 80.0
    MODEL_CONTAMINATION: float = 0.1

    @classmethod
    def is_production(cls) -> bool:
        return cls.APP_ENV == "production"


config = Config()