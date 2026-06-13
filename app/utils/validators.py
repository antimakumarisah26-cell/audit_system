"""
app/utils/validators.py
───────────────────────
Input validation functions used across the app.
Centralising validation prevents duplicated logic and makes testing easier.
"""

import re
from typing import Tuple


def validate_username(username: str) -> Tuple[bool, str]:
    """Username must be 3–30 alphanumeric chars or underscores."""
    username = username.strip()
    if not username:
        return False, "Username is required."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(username) > 30:
        return False, "Username must be at most 30 characters."
    if not re.match(r"^\w+$", username):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Password must be at least 8 chars with one digit."""
    if not password:
        return False, "Password is required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    return True, ""


def validate_branch_name(name: str) -> Tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "Branch name is required."
    if len(name) > 100:
        return False, "Branch name must be at most 100 characters."
    return True, ""


def validate_transaction_volume(volume: float) -> Tuple[bool, str]:
    if volume < 0:
        return False, "Transaction volume cannot be negative."
    if volume > 1_000_000_000:
        return False, "Transaction volume exceeds maximum allowed value."
    return True, ""


def validate_compliance_score(score: float) -> Tuple[bool, str]:
    if not (0.0 <= score <= 100.0):
        return False, "Compliance score must be between 0 and 100."
    return True, ""


def validate_csv_columns(df_columns: list) -> Tuple[bool, str]:
    required = {"branch_name", "account_type", "transaction_volume", "compliance_score"}
    missing = required - set(df_columns)
    if missing:
        return False, f"CSV is missing required columns: {', '.join(missing)}"
    return True, ""