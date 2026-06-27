"""SMTP email helper (mirrors Node `emailSender` using Gmail app password)."""

from __future__ import annotations

import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, html: str, subject: str = "Reset Password Link") -> None:
    """Send an HTML email via Gmail SMTP. Logs and swallows errors (best-effort)."""
    if not settings.nodemailer_email or not settings.nodemailer_app_pass:
        logger.warning("email not configured; skipping send to %s", to)
        return

    message = EmailMessage()
    message["From"] = settings.nodemailer_email
    message["To"] = to
    message["Subject"] = subject
    message.add_alternative(html, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=settings.nodemailer_email,
            password=settings.nodemailer_app_pass,
        )
    except Exception as exc:
        logger.warning("email send failed to %s: %s", to, exc)
