"""Chatbot routes — /api/v1/chat-bot.

Mirrors the Node Gemini-based shopping assistant. Unlike the original (which
kept a single shared, mutable conversation history), this implementation is
stateless per request to avoid cross-user leakage.
"""

from __future__ import annotations

import asyncio
import logging

import httpx
from fastapi import APIRouter

from app.config import settings
from app.core.errors import ApiError
from app.core.response import send_response
from app.schemas import ChatbotRequest

router = APIRouter(prefix="/chat-bot", tags=["chat-bot"])
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful shopping assistant. Your job is to assist users with their "
    "shopping-related questions, such as product recommendations, price comparisons, "
    "and store locations. Be friendly, informative, and concise."
)


async def _rag_reply(message: str) -> str | None:
    """Ask the RAG service for a product-aware answer. Returns None on failure.

    The RAG service queries the live product catalog and needs no external API
    key, so this is the default engine for the shopping assistant.
    """
    url = f"{settings.rag_service_url.rstrip('/')}/chat/query"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json={"query": message})
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # network error, RAG down, bad status
        logger.warning("RAG service unavailable (%s): %s", url, exc)
        return None

    answer = (data.get("answer") or "").strip()
    return answer or None


def _gemini_reply(message: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(message)
    return response.text


@router.post("")
async def chat(payload: ChatbotRequest):
    message = (payload.message or "").strip()
    if not message:
        raise ApiError(400, "User prompt is required.")

    # 1) Primary engine: key-free RAG service over the product catalog.
    reply = await _rag_reply(message)
    if reply:
        return send_response(status_code=201, message="Chat saved successfully.", data=reply)

    # 2) Optional enhancement: Google Gemini, if a key is configured.
    if settings.gemini_api_key:
        try:
            reply = await asyncio.to_thread(_gemini_reply, message)
            return send_response(status_code=201, message="Chat saved successfully.", data=reply)
        except Exception as exc:
            logger.error("chatbot gemini error: %s", exc)

    # 3) Graceful fallback when no engine is available.
    return send_response(
        status_code=201,
        message="Chat saved successfully.",
        data=(
            "I'm having trouble reaching the shopping assistant right now. "
            "You can still browse products, search the catalog, and check out normally."
        ),
    )
