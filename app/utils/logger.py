"""
app/utils/logger.py
───────────────────
Structured logging via loguru.
All modules import `logger` from here instead of using `print()`.
"""

import sys
import os
from loguru import logger

os.makedirs("logs", exist_ok=True)

# Remove default handler
logger.remove()

# Console handler (human-readable)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# File handler (JSON-style for production monitoring)
logger.add(
    "logs/audit_system_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG",
    format="{time} | {level} | {name}:{line} | {message}",
)

__all__ = ["logger"]