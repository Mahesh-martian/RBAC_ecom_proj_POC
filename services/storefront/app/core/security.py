"""Password hashing (bcrypt) and JWT helpers mirroring the Node implementation."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt


def hash_password(password: str) -> str:
    """bcrypt hash with cost factor 10 (matches Node `bcrypt.hash(pwd, 10)`)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


_DURATION_RE = re.compile(r"^\s*(\d+)\s*([smhd])\s*$", re.IGNORECASE)
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _expires_in_seconds(expires_in: str) -> int:
    """Convert a Node-style duration string ("7d", "15m", "3600") to seconds."""
    if expires_in is None:
        return 7 * 86400
    text = str(expires_in).strip()
    if text.isdigit():
        return int(text)
    match = _DURATION_RE.match(text)
    if not match:
        return 7 * 86400
    return int(match.group(1)) * _UNIT_SECONDS[match.group(2).lower()]


def generate_token(payload: dict[str, Any], secret: str, expires_in: str) -> str:
    """Sign an HS256 JWT with an `exp` derived from a Node-style duration string."""
    to_encode = dict(payload)
    expire = datetime.now(timezone.utc) + timedelta(seconds=_expires_in_seconds(expires_in))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, secret, algorithm="HS256")


def verify_token(token: str, secret: str) -> dict[str, Any]:
    """Decode an HS256 JWT, stripping surrounding quotes like the Node helper."""
    cleaned = token.strip().strip('"')
    return jwt.decode(cleaned, secret, algorithms=["HS256"])
