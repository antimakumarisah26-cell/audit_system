"""
app/models/schema.py
SQLAlchemy ORM models. Works with SQLite (dev) and PostgreSQL (production).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import config

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(30), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class AuditRecord(Base):
    __tablename__ = "audit_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_name = Column(String(100), nullable=False, index=True)
    account_type = Column(String(50), nullable=False)
    transaction_volume = Column(Float, nullable=False)
    compliance_score = Column(Float, nullable=False)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="unknown")
    flagged = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String(30), nullable=False)
    action = Column(String(100), nullable=False)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_engine():
    db_url = config.DATABASE_URL
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, connect_args=connect_args, echo=False)


def get_session_factory():
    engine = get_engine()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


SessionLocal = get_session_factory()