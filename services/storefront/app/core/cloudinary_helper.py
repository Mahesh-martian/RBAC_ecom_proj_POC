"""Cloudinary upload helper (mirrors Node `fileUploader`)."""

from __future__ import annotations

import logging
from typing import Optional

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

from app.config import settings

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=settings.cloudinary_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_secret,
    secure=True,
)


async def upload_to_cloudinary(file: UploadFile) -> Optional[str]:
    """Upload a single file, returning its secure URL (or None on failure)."""
    if file is None:
        return None
    contents = await file.read()
    try:
        result = cloudinary.uploader.upload(contents, resource_type="auto")
        return result.get("secure_url")
    except Exception as exc:  # cloudinary raises various error types
        logger.warning("cloudinary upload failed: %s", exc)
        return None


async def upload_multiple_to_cloudinary(files: list[UploadFile]) -> list[str]:
    """Upload multiple files, returning the list of secure URLs."""
    urls: list[str] = []
    for file in files:
        url = await upload_to_cloudinary(file)
        if url:
            urls.append(url)
    return urls
