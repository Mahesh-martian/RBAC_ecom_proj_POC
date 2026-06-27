"""Seed a default admin account on startup (mirrors Node `seedAdmin`)."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app import models
from app.config import settings
from app.core.security import hash_password
from app.database import SessionLocal

logger = logging.getLogger(__name__)


async def seed_admin_account() -> None:
    async with SessionLocal() as db:
        result = await db.execute(select(models.User).where(models.User.email == settings.admin_email))
        if result.scalar_one_or_none() is not None:
            logger.info("Admin account already exists. Skipping creation.")
            return

        db.add(
            models.User(
                email=settings.admin_email,
                password=hash_password(settings.admin_password),
                role="ADMIN",
                name="Super Admin",
            )
        )
        await db.commit()
        logger.info("Admin account created with email: %s", settings.admin_email)
