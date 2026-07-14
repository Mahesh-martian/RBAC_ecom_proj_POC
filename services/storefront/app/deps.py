"""Auth dependencies mirroring the Node `auth(...roles)` middleware.

The original middleware reads the raw `Authorization` header (no "Bearer "
prefix), verifies the JWT with `JWT_SECRET`, attaches the decoded payload as
`req.user`, and enforces role membership. The decoded payload embeds the user
plus nested `vendor` / `customer` objects.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

import jwt
from fastapi import Header

from app.config import settings
from app.core.errors import ApiError
from app.core.security import verify_token


def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict[str, Any]:
    """Decode and return the JWT payload, or raise 401 when missing/invalid."""
    if not authorization:
        raise ApiError(401, "You are not authorized")
    try:
        return verify_token(authorization, settings.jwt_secret)
    except jwt.PyJWTError:
        raise ApiError(401, "You are not authorized")


def require_roles(*roles: str) -> Callable[..., dict[str, Any]]:
    """Dependency factory enforcing that the user has one of ``roles``."""

    def _dependency(authorization: Optional[str] = Header(default=None)) -> dict[str, Any]:
        user = get_current_user(authorization)
        if roles and user.get("role") not in roles:
            raise ApiError(403, "Forbidden")
        return user

    return _dependency


def vendor_id_of(user: dict[str, Any]) -> str:
    vendor = user.get("vendor")
    if not vendor or not vendor.get("id"):
        raise ApiError(403, "Vendor profile not found")
    return vendor["id"]


def customer_id_of(user: dict[str, Any]) -> str:
    customer = user.get("customer")
    if not customer or not customer.get("id"):
        raise ApiError(403, "Customer profile not found")
    return customer["id"]
