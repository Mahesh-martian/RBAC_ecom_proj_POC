"""Chat API endpoints for product guidance and recommendations."""

import asyncio
import json
import re
import logging
import time
from typing import AsyncGenerator, Optional

import jwt
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, or_

from app.dependencies import DBSessionDep
from app.models import Product, Category
from app.schemas import (
    ChatComparisonResponse,
    ChatProviderComparison,
    ChatQueryRequest,
    ChatQueryResponse,
    ChatRecommendation,
    ChatUsage,
)
from app.config import settings
from app.services.langchain_support_rag import LangChainSupportRAGService
from app.services.semantic_router import SemanticRouter
from app.services.support_rag import SupportRAGService
from app.services import shopease_products

router = APIRouter(prefix="/chat", tags=["chat"])
support_rag = SupportRAGService()
langchain_support_rag = LangChainSupportRAGService()
semantic_router = SemanticRouter()
logger = logging.getLogger(__name__)


# RBAC: map the caller's role to the set of policy-document audiences they may see.
# Customers see customer + shared docs; vendors see seller + shared docs; admins
# (and super admins) see everything.
ROLE_AUDIENCES: dict[str, set[str]] = {
    "customer": {"customer", "common"},
    "vendor": {"vendor", "common"},
    "admin": {"customer", "vendor", "common"},
}

# Role-specific persona prepended to the support system prompt so the assistant
# frames answers for the right audience.
ROLE_PERSONA: dict[str, str] = {
    "customer": (
        "You are ShopEase's shopping and customer-support assistant helping a shopper."
    ),
    "vendor": (
        "You are ShopEase's seller-support assistant helping a marketplace vendor with "
        "seller policies, product listings, fees, payouts, shipping, returns, and account health."
    ),
    "admin": (
        "You are ShopEase's administrator assistant with full access to both customer "
        "and seller policies."
    ),
}


def _normalize_role(role: Optional[str]) -> str:
    """Map an arbitrary role string to one of the supported RBAC roles."""
    normalized = (role or "").strip().lower().replace("-", "_")
    if normalized in {"super_admin", "superadmin"}:
        return "admin"
    if normalized in ROLE_AUDIENCES:
        return normalized
    return "customer"


def _resolve_role_and_name(request_context: Request, request: ChatQueryRequest) -> tuple[str, Optional[str]]:
    """Determine the caller's authoritative role and display name.

    Security: when a shared ShopEase JWT secret is configured, the role is taken
    ONLY from a valid, signature-verified bearer token — the client-supplied
    ``user_role`` body field is never trusted. Callers without a valid token are
    treated as anonymous customers. When no shared secret is configured (local dev
    convenience), we fall back to the body-supplied role so RBAC can be exercised
    without minting tokens.
    """
    name = request.user_name
    secret = settings.shopease_jwt_secret

    auth_header = request_context.headers.get("authorization")
    if secret:
        if auth_header:
            token = auth_header
            if token.lower().startswith("bearer "):
                token = token[7:]
            token = token.strip().strip('"').strip("'").strip()
            try:
                payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
                token_name = payload.get("name")
                if token_name and not name:
                    name = token_name
                return _normalize_role(payload.get("role")), name
            except jwt.InvalidTokenError:
                logger.warning("chat_rbac invalid shopease token; defaulting to customer")
        # No/invalid token while a secret is configured: anonymous customer.
        return "customer", name

    # Dev fallback (no shared secret): trust the body-provided role.
    return _normalize_role(request.user_role), name


def _role_help_text(role: str) -> str:
    """Guidance text shown for greetings/ambiguous queries, tailored per role."""
    if role == "vendor":
        return (
            "I can help with seller topics like listings, fees, payouts, shipping, "
            "returns, and account health \u2014 and you can still look up products. "
            "Try 'how are payouts calculated?' or 'show me backpacks'."
        )
    if role == "admin":
        return (
            "I can help with customer and seller policies and look up products. "
            "Try 'what is the return policy?', 'how do seller payouts work?', or "
            "'show me running shoes'."
        )
    return (
        "I can help you find products or answer questions about orders, "
        "returns, shipping, and your account. Try 'running shoes under 100' "
        "or 'what is your return policy?'."
    )



def _build_product_response(
    recommendations: list[ChatRecommendation],
    lowered_query: str,
    conversation_id: Optional[str],
    provider: str,
) -> ChatQueryResponse:
    """Format product recommendations into the chat response contract."""
    if recommendations:
        # Keep the text minimal: the storefront renders the product cards (image,
        # name, price) from the structured ``recommendations`` payload, so avoid
        # duplicating names/prices (and the USD figures) in the answer text.
        answer = "Here are some items that match your request:"
    else:
        answer = (
            "I could not find matching products right now. Please try another keyword "
            "or browse the catalog for more options."
        )

    # Intent-aware hinting for common e-commerce intents.
    if "return" in lowered_query or "refund" in lowered_query:
        answer += "\nFor returns/refunds, you can also check your Orders page after login."
    if "track" in lowered_query or "shipping" in lowered_query:
        answer += "\nFor shipping updates, open your order details from the Orders page."

    citations = [f"SKU:{rec.sku}" for rec in recommendations if rec.sku]

    return ChatQueryResponse(
        answer=answer,
        recommendations=recommendations,
        citations=citations,
        conversation_id=conversation_id,
        response_type="product",
        provider=provider,
        confidence=1.0 if recommendations else 0.0,
    )



@router.post("/query/compare", response_model=ChatComparisonResponse, summary="Compare current and LangChain policy providers")
async def compare_chat_query(request_context: Request, request: ChatQueryRequest) -> ChatComparisonResponse:
    """Benchmark current local policy retrieval against a LangChain-backed equivalent."""
    query_text = request.query.strip()

    current_started = time.perf_counter()
    current_answer, current_citations, current_confidence = support_rag.answer(query_text, top_k=settings.rag_top_k)
    current_latency_ms = round((time.perf_counter() - current_started) * 1000, 1)

    langchain_result = await langchain_support_rag.answer(query_text, top_k=settings.rag_top_k)

    logger.info(
        "chat_compare query=%s current_latency_ms=%s langchain_latency_ms=%s",
        query_text,
        current_latency_ms,
        langchain_result.latency_ms,
    )

    return ChatComparisonResponse(
        query=query_text,
        current=ChatProviderComparison(
            answer=current_answer,
            citations=current_citations,
            provider="local",
            confidence=current_confidence,
            latency_ms=current_latency_ms,
        ),
        langchain=ChatProviderComparison(
            answer=langchain_result.answer,
            citations=langchain_result.citations,
            provider="langchain-local",
            confidence=langchain_result.confidence,
            latency_ms=langchain_result.latency_ms,
        ),
    )


@router.post("/query", response_model=ChatQueryResponse, summary="Query shopping assistant")
async def chat_query(request_context: Request, request: ChatQueryRequest, session: DBSessionDep) -> ChatQueryResponse:
    """Return a shopping-assistant answer with product recommendations."""
    query_text = request.query.strip()
    lowered_query = query_text.lower()
    normalized_query = re.sub(r"[^a-z0-9\s]", " ", lowered_query)

    # Parse an optional price ceiling so budget phrasing ("running shoes under 100",
    # "below \u20b950", "less than 200") actually constrains the recommendations.
    max_price: Optional[float] = None
    budget_match = re.search(
        r"(?:under|below|less than|upto|up to|within|at most|no more than|max)\s*"
        r"(?:rs\.?|inr|usd|\$|\u20b9)?\s*(\d+(?:\.\d+)?)",
        lowered_query,
    )
    if budget_match:
        try:
            max_price = float(budget_match.group(1))
        except ValueError:
            max_price = None

    # Resolve the caller's authoritative role (token-verified when a shared secret
    # is configured) and personalize replies with their name.
    role, resolved_name = _resolve_role_and_name(request_context, request)
    audiences = ROLE_AUDIENCES.get(role, {"customer", "common"})
    persona = ROLE_PERSONA.get(role)
    first_name = (resolved_name or "").strip().split(" ")[0] if resolved_name else ""
    greeting_prefix = f"Hi {first_name}! " if first_name else "Hi! "

    # Handle greetings without forcing product recommendations.
    greeting_terms = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
    if normalized_query.strip() in greeting_terms:
        return ChatQueryResponse(
            answer=greeting_prefix + _role_help_text(role),
            recommendations=[],
            citations=[],
            conversation_id=request.conversation_id,
            response_type="general",
            provider="local",
            confidence=1.0,
        )

    # Basic category understanding from natural-language terms.
    category_synonyms = {
        "footwear": {"shoe", "shoes", "sneaker", "sneakers", "running", "boot", "boots"},
        "accessories": {"bag", "bags", "backpack", "backpacks", "belt", "wallet"},
        "apparel": {"shirt", "tshirt", "tee", "jacket", "coat", "hoodie", "dress", "denim"},
        "perfume": {"perfume", "fragrance", "scent", "cologne"},
    }

    stop_words = {
        "a", "an", "and", "are", "for", "from", "get", "i", "in", "is", "it", "me", "my",
        "need", "please", "recommend", "show", "something", "the", "to", "want", "with", "you",
        # Budget/price phrasing is handled by the price parser above, not as search keywords.
        "under", "below", "less", "than", "up", "upto", "within", "max", "most", "more",
        "no", "or", "cheap", "cheaper", "budget", "price", "priced", "cost", "around", "about",
        "rs", "inr", "usd",
    }
    raw_tokens = [
        t
        for t in normalized_query.split()
        if len(t) >= 2 and t not in stop_words and not t.isdigit()
    ]
    tokens: list[str] = []
    for token in raw_tokens:
        tokens.append(token)
        # Naive singularization helps match plural queries like "backpacks" -> "backpack".
        if token.endswith("s") and len(token) > 3:
            tokens.append(token[:-1])
    # Preserve token order while removing duplicates.
    tokens = list(dict.fromkeys(tokens))

    matched_category_names: set[str] = set()
    for category_name, synonyms in category_synonyms.items():
        if any(token in synonyms for token in tokens):
            matched_category_names.add(category_name)

    # Classify the query into a broad intent family using the semantic router.
    # New phrasings are handled by similarity to example utterances instead of
    # one-off keyword rules, so future shopping/support scenarios scale by adding
    # examples rather than branches.
    intent, intent_confidence, router_mode = await asyncio.to_thread(
        semantic_router.classify, query_text
    )
    logger.info(
        "chat_route query=%s intent=%s confidence=%s mode=%s",
        query_text,
        intent,
        intent_confidence,
        router_mode,
    )

    support_intents = {"policy_support", "order_status", "account_help"}
    # Honor explicit structured product context regardless of the predicted intent.
    forced_product = bool(request.product_id or request.category)

    # Support-family intents are grounded in policy docs via the RAG service.
    if intent in support_intents and not forced_product:
        # Single RAG path: Azure AI Search retrieval + Azure OpenAI generation,
        # scoped to the caller's audiences for RBAC. No local fallback.
        langchain_result = await langchain_support_rag.answer(
            query_text,
            top_k=settings.rag_top_k,
            user_name=first_name or None,
            history=[(m.role, m.text) for m in request.history],
            audiences=audiences,
            persona=persona,
        )
        answer = langchain_result.answer
        citations = langchain_result.citations
        confidence = langchain_result.confidence
        provider = "langchain-azure"
        logger.info(
            "chat_support query=%s intent=%s provider=%s role=%s confidence=%s citations=%s",
            query_text,
            intent,
            provider,
            role,
            confidence,
            len(citations),
        )
        logger.info(
            "chat_usage query=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s "
            "retrieval_count=%s search_latency_ms=%s llm_latency_ms=%s",
            query_text,
            langchain_result.prompt_tokens,
            langchain_result.completion_tokens,
            langchain_result.total_tokens,
            langchain_result.retrieval_count,
            langchain_result.search_latency_ms,
            langchain_result.llm_latency_ms,
        )
        return ChatQueryResponse(
            answer=answer,
            recommendations=[],
            citations=citations,
            conversation_id=request.conversation_id,
            response_type="policy_support",
            provider=provider,
            confidence=confidence,
            usage=ChatUsage(
                prompt_tokens=langchain_result.prompt_tokens,
                completion_tokens=langchain_result.completion_tokens,
                total_tokens=langchain_result.total_tokens,
                retrieval_count=langchain_result.retrieval_count,
                search_latency_ms=langchain_result.search_latency_ms,
                llm_latency_ms=langchain_result.llm_latency_ms,
            ),
        )

    # Greeting (or ambiguous non-shopping query): guide instead of dumping products.
    is_ambiguous = (
        router_mode.startswith("semantic")
        and intent_confidence < semantic_router.confidence_threshold
        and not tokens
        and not matched_category_names
    )
    if (intent == "greeting" or is_ambiguous) and not forced_product:
        return ChatQueryResponse(
            answer=greeting_prefix + _role_help_text(role),
            recommendations=[],
            citations=[],
            conversation_id=request.conversation_id,
            response_type="general",
            provider="local",
            confidence=1.0,
        )

    base_stmt = (
        select(Product)
        .where(Product.is_active.is_(True), Product.stock_qty > 0)
        .order_by(Product.rating.desc(), Product.created_at.desc())
    )
    if max_price is not None:
        base_stmt = base_stmt.where(Product.price <= max_price)

    category_names: set[str] = set(matched_category_names)
    if request.category:
        category_names.add(request.category.lower())

    # ShopEase storefront: source recommendations from the external catalog API
    # instead of the local database. Falls back to an empty list (handled below)
    # when ShopEase is unreachable.
    if settings.shopease_products_enabled:
        # Use the cleaned, singularized tokens (stop words removed) so conversational
        # phrasing like "I need a backpack" still finds the "Canvas Backpack". Fall back
        # to the raw query when tokenization yields nothing.
        shopease_recs = await shopease_products.search_products(
            search_terms=tokens or [query_text],
            category=request.category,
            limit=settings.rag_top_k,
            max_price=max_price,
        )
        logger.info(
            "chat_product source=shopease query=%s results=%s",
            query_text,
            len(shopease_recs),
        )
        return _build_product_response(
            shopease_recs, lowered_query, request.conversation_id, provider="shopease"
        )

    category_ids: list[int] = []
    if category_names:
        category_filters = [Category.name.ilike(f"%{name}%") for name in category_names]
        category_stmt = select(Category.id).where(or_(*category_filters))
        category_result = await session.execute(category_stmt)
        category_ids = [row[0] for row in category_result.all()]
        if category_ids:
            base_stmt = base_stmt.where(Product.category_id.in_(category_ids))

    # Token-based matching improves relevance for natural language queries.
    if tokens:
        token_filters = []
        for token in tokens:
            like = f"%{token}%"
            token_filters.extend([
                Product.name.ilike(like),
                Product.description.ilike(like),
                Product.sku.ilike(like),
            ])
        base_stmt = base_stmt.where(or_(*token_filters))

    if request.product_id:
        base_stmt = base_stmt.where(Product.id == request.product_id)

    result = await session.execute(base_stmt.limit(25))
    products = list(result.scalars().all())

    def score_product(product: Product) -> int:
        searchable = " ".join([
            (product.name or "").lower(),
            (product.description or "").lower(),
            (product.sku or "").lower(),
        ])
        score = 0
        for token in tokens:
            if token in searchable:
                score += 2
            if token in (product.name or "").lower():
                score += 2
        if query_text.lower() and query_text.lower() in searchable:
            score += 3
        return score

    if products:
        products.sort(key=lambda p: (score_product(p), p.rating, p.created_at), reverse=True)
        products = products[:3]

    # Fallback to featured products if no direct match.
    if not products:
        fallback_stmt = (
            select(Product)
            .where(Product.is_active.is_(True), Product.stock_qty > 0)
            .order_by(Product.rating.desc(), Product.created_at.desc())
            .limit(3)
        )
        if max_price is not None:
            fallback_stmt = fallback_stmt.where(Product.price <= max_price)
        if category_ids:
            fallback_stmt = fallback_stmt.where(Product.category_id.in_(category_ids))
        fallback_result = await session.execute(fallback_stmt)
        products = list(fallback_result.scalars().all())

    recommendations: list[ChatRecommendation] = []
    for product in products:
        image_url = None
        if isinstance(product.images, list) and product.images:
            first_image = product.images[0]
            if isinstance(first_image, dict):
                image_url = first_image.get("url")

        recommendations.append(
            ChatRecommendation(
                id=str(product.id),
                name=product.name,
                sku=product.sku,
                price=product.price,
                currency=product.currency,
                image_url=image_url,
            )
        )

    return _build_product_response(
        recommendations, lowered_query, request.conversation_id, provider="local"
    )


@router.post("/query/stream", summary="Stream a shopping-assistant answer over SSE")
async def chat_query_stream(
    request_context: Request, request: ChatQueryRequest, session: DBSessionDep
) -> StreamingResponse:
    """Server-Sent Events (SSE) variant of ``/chat/query``.

    Reuses the full routing/recommendation logic, then streams the answer as
    incremental ``token`` events for a live typing effect, followed by a single
    ``done`` event carrying recommendations, citations, and metadata. The client
    should consume ``text/event-stream`` and stop on the ``done`` event.
    """
    response = await chat_query(request_context, request, session)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            words = response.answer.split(" ")
            for index, word in enumerate(words):
                # Re-append the spaces removed by split so the client can concatenate verbatim.
                chunk = word if index == len(words) - 1 else f"{word} "
                payload = {"type": "token", "content": chunk}
                yield f"data: {json.dumps(payload)}\n\n"
                await asyncio.sleep(0.02)  # pacing for a natural typing cadence

            done = {
                "type": "done",
                "response_type": response.response_type,
                "provider": response.provider,
                "confidence": response.confidence,
                "conversation_id": response.conversation_id,
                "citations": response.citations,
                "recommendations": [rec.model_dump() for rec in response.recommendations],
            }
            yield f"data: {json.dumps(done)}\n\n"
        except Exception as exc:  # never leave the stream hanging on error
            logger.error("chat_query_stream error: %s", exc)
            yield f"data: {json.dumps({'type': 'error', 'message': 'stream interrupted'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable proxy buffering (nginx/ACA) for true streaming
        },
    )
