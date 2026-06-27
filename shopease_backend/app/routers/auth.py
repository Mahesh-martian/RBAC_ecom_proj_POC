"""Auth routes — /api/v1/auth."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from app.core.errors import ApiError
from app.core.email_helper import send_email
from app.core.response import model_to_dict, send_response
from app.core.security import (
    generate_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.serializers import serialize_user

router = APIRouter(prefix="/auth", tags=["auth"])


async def _find_user_by_email(db: AsyncSession, email: str) -> models.User:
    result = await db.execute(
        select(models.User)
        .where(models.User.email == email)
        .options(selectinload(models.User.vendor), selectinload(models.User.customer))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise ApiError(404, "User Not Found")
    return user


def _check_account_status(user: models.User) -> None:
    if user.role == "VENDOR" and user.vendor and (user.vendor.isDeleted or user.vendor.isSuspended):
        raise ApiError(403, "Vendor account is suspended or deleted.")
    if user.role == "CUSTOMER" and user.customer and (user.customer.isDeleted or user.customer.isSuspended):
        raise ApiError(403, "Customer account is suspended or deleted.")


@router.post("/register")
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(models.User).where(models.User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise ApiError(400, "User with this email already exists")

    user = models.User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    await db.flush()

    if payload.role == "VENDOR":
        db.add(models.Vendor(name=payload.name, email=user.email))
    elif payload.role == "CUSTOMER":
        db.add(models.Customer(name=payload.name, email=user.email))
    elif payload.role == "ADMIN":
        db.add(models.Admin(name=payload.name, email=user.email))

    await db.commit()
    await db.refresh(user)

    return send_response(
        status_code=201,
        message="User Created Successfully.",
        data=model_to_dict(user, exclude=("password",)),
    )


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await _find_user_by_email(db, payload.email)
    _check_account_status(user)

    if not verify_password(payload.password, user.password):
        raise ApiError(401, "Invalid Credentials.")

    user_without_password = serialize_user(user)
    access_token = generate_token(user_without_password, settings.jwt_secret, settings.jwt_expires_in)
    refresh_token = generate_token(
        user_without_password, settings.jwt_refresh_token_secret, settings.jwt_refresh_token_expires_in
    )

    return send_response(
        status_code=200,
        message="User logged in successfully.",
        data={
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "userWithoutPassword": user_without_password,
        },
    )


@router.patch("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    user_data = await _find_user_by_email(db, user["email"])
    if not verify_password(payload.oldPassword, user_data.password):
        raise ApiError(401, "Invalid Credentials.")
    user_data.password = hash_password(payload.newPassword)
    await db.commit()
    return send_response(status_code=200, message="Password changed successfully.", data="")


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    user = await _find_user_by_email(db, payload.email)
    _check_account_status(user)

    reset_token = generate_token(
        {"email": user.email, "role": user.role},
        settings.jwt_reset_pass_token,
        settings.jwt_reset_pass_token_expires_in,
    )
    reset_link = f"{settings.reset_pass_link}?userId={user.id}&token={reset_token}"
    await send_email(
        user.email,
        f"""
    <div>
    <p>Dear {user.name}</p>
    <p> Your password reset link
    <a href={reset_link}>
    <button>Reset Password</button>
    </a>
    </p>
    </div>
    """,
    )
    return send_response(status_code=200, message="Check your email", data=None)


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
):
    if not authorization:
        raise ApiError(401, "You are not authorized")

    result = await db.execute(
        select(models.User)
        .where(models.User.id == payload.id)
        .options(selectinload(models.User.vendor), selectinload(models.User.customer))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise ApiError(404, "User Not Found")
    _check_account_status(user)

    try:
        verify_token(authorization, settings.jwt_reset_pass_token)
    except Exception:
        raise ApiError(403, "Forbidden")

    user.password = hash_password(payload.password)
    await db.commit()
    return send_response(status_code=200, message="Password reset successfully", data=None)


@router.post("/logout")
async def logout():
    response = send_response(status_code=200, message="User logged out successfully.", data=None)
    response.delete_cookie("accessToken")
    response.delete_cookie("refreshToken")
    return response
