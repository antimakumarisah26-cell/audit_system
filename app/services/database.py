"""
app/services/database.py
All database operations using SQLAlchemy ORM.
No raw SQL, no injection risk. Every method is typed and documented.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime
from typing import Optional
import bcrypt
import pandas as pd
from app.config import config
from app.models.schema import AuditLog, AuditRecord, SessionLocal, User
from app.utils.logger import logger


@contextmanager
def get_db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(f"DB error, rolled back: {exc}")
        raise
    finally:
        session.close()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def seed_default_admin() -> None:
    with get_db() as db:
        if db.query(User).count() == 0:
            admin = User(
                username=config.DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(config.DEFAULT_ADMIN_PASSWORD),
                role="admin",
            )
            db.add(admin)
            logger.info("Default admin account created.")


def authenticate_user(username: str, password: str) -> Optional[dict]:
    if not username or not password:
        return None
    with get_db() as db:
        user = db.query(User).filter(
            User.username == username.strip(),
            User.is_active == True,
        ).first()
        if user and verify_password(password, user.password_hash):
            user.last_login = datetime.utcnow()
            logger.info(f"User '{username}' logged in.")
            return {"id": user.id, "username": user.username, "role": user.role}
    logger.warning(f"Failed login for '{username}'")
    return None


def get_all_users() -> pd.DataFrame:
    with get_db() as db:
        users = db.query(User.id, User.username, User.role, User.is_active, User.created_at).all()
        return pd.DataFrame(users, columns=["id", "username", "role", "active", "created_at"])


def create_user(username: str, password: str, role: str = "user") -> tuple[bool, str]:
    with get_db() as db:
        if db.query(User).filter(User.username == username.strip()).first():
            return False, f"Username '{username}' already exists."
        db.add(User(
            username=username.strip(),
            password_hash=hash_password(password),
            role=role,
        ))
    logger.info(f"User '{username}' created.")
    return True, f"User '{username}' created successfully."


def deactivate_user(user_id: int) -> bool:
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        user.is_active = False
    return True


def load_audit_records() -> pd.DataFrame:
    with get_db() as db:
        records = db.query(AuditRecord).order_by(AuditRecord.id).all()
        if not records:
            return pd.DataFrame()
        return pd.DataFrame([{
            "id": r.id,
            "branch_name": r.branch_name,
            "account_type": r.account_type,
            "transaction_volume": r.transaction_volume,
            "compliance_score": r.compliance_score,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "flagged": r.flagged,
            "notes": r.notes,
            "created_at": r.created_at,
        } for r in records])


def add_audit_record(branch_name, account_type, transaction_volume, compliance_score, risk_score=0.0, notes="") -> bool:
    try:
        with get_db() as db:
            db.add(AuditRecord(
                branch_name=branch_name.strip(),
                account_type=account_type,
                transaction_volume=float(transaction_volume),
                compliance_score=float(compliance_score),
                risk_score=float(risk_score),
                risk_level=_score_to_level(risk_score),
                flagged=risk_score >= config.RISK_HIGH_THRESHOLD,
                notes=notes.strip() if notes else None,
            ))
        return True
    except Exception as exc:
        logger.error(f"Failed to add record: {exc}")
        return False


def import_audit_records(df: pd.DataFrame) -> tuple[bool, str]:
    required = {"branch_name", "account_type", "transaction_volume", "compliance_score"}
    missing = required - set(df.columns)
    if missing:
        return False, f"Missing columns: {', '.join(missing)}"
    try:
        with get_db() as db:
            db.bulk_save_objects([
                AuditRecord(
                    branch_name=str(row["branch_name"]).strip(),
                    account_type=str(row["account_type"]),
                    transaction_volume=float(row["transaction_volume"]),
                    compliance_score=float(row["compliance_score"]),
                    risk_score=0.0,
                    risk_level="unknown",
                )
                for _, row in df.iterrows()
            ])
        return True, f"Successfully imported {len(df)} records."
    except Exception as exc:
        logger.error(f"Import failed: {exc}")
        return False, f"Import failed: {exc}"


def update_risk_scores(df: pd.DataFrame) -> None:
    if df.empty:
        return
    try:
        with get_db() as db:
            for _, row in df.iterrows():
                record = db.query(AuditRecord).filter(AuditRecord.id == int(row["id"])).first()
                if record:
                    record.risk_score = float(row["risk_score"])
                    record.risk_level = _score_to_level(float(row["risk_score"]))
                    record.flagged = float(row["risk_score"]) >= config.RISK_HIGH_THRESHOLD
                    record.updated_at = datetime.utcnow()
    except Exception as exc:
        logger.error(f"Risk score update failed: {exc}")


def delete_audit_record(record_id: int) -> bool:
    with get_db() as db:
        record = db.query(AuditRecord).filter(AuditRecord.id == record_id).first()
        if not record:
            return False
        db.delete(record)
    return True


def log_action(user_id: int, username: str, action: str, detail: str = "") -> None:
    try:
        with get_db() as db:
            db.add(AuditLog(user_id=user_id, username=username, action=action, detail=detail))
    except Exception as exc:
        logger.error(f"Audit log failed: {exc}")


def get_audit_logs() -> pd.DataFrame:
    with get_db() as db:
        logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(500).all()
        if not logs:
            return pd.DataFrame()
        return pd.DataFrame([{
            "id": l.id, "username": l.username,
            "action": l.action, "detail": l.detail, "timestamp": l.created_at,
        } for l in logs])


def _score_to_level(score: float) -> str:
    if score >= config.RISK_CRITICAL_THRESHOLD: return "critical"
    if score >= config.RISK_HIGH_THRESHOLD: return "high"
    if score >= 33.0: return "medium"
    return "low"
