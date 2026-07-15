"""Embedding-based semantic intent router for the chat assistant.

Routes a user query into a broad intent family using cosine similarity against
embedded example utterances (anchors). This scales by adding examples instead of
hand-written keyword rules. Falls back to keyword scoring when Azure embeddings
are not configured so the service still works in minimal/local setups.
"""

from __future__ import annotations

import logging
import math
import re
import threading

from openai import AzureOpenAI

from app.config import settings
from app.logging_utils import log_step
from app.services.prompt_registry import PromptNotFoundError, get_prompt_registry

logger = logging.getLogger(__name__)

# Broad, stable intent families. Add example utterances here instead of new
# branch rules in the router. New phrasing is handled by semantic similarity.
# Kept as an in-code default so the router remains usable when the prompt
# registry is unavailable; the registry (prompts/intent_anchors/vN.yaml) is
# consulted at construction time and overrides this baseline when present.
INTENT_ANCHORS: dict[str, list[str]] = {
    "product_search": [
        "show me running shoes",
        "I want to buy a denim jacket",
        "recommend a backpack under 100",
        "do you have leather bags",
        "looking for a blue shirt in size medium",
        "what perfumes do you sell",
        "find me something casual to wear",
        "cheapest sneakers you have",
    ],
    "product_details": [
        "what material is this jacket made of",
        "what sizes are available for this shirt",
        "does this bag come in black",
        "what are the specifications of this product",
        "is this true to size",
        "what colors does this come in",
    ],
    "policy_support": [
        "what is your refund policy",
        "how do returns work",
        "my item arrived damaged what do I do",
        "can I cancel my order",
        "what is your shipping policy",
        "is my payment information secure",
        "how long does delivery take",
        "what is your warranty policy",
        "the product is defective can I get a refund",
        "do you offer exchanges",
    ],
    "order_status": [
        "where is my order",
        "track my package",
        "what is the status of my delivery",
        "has my order shipped yet",
        "when will my order arrive",
    ],
    "account_help": [
        "I forgot my password",
        "how do I reset my password",
        "I cannot log into my account",
        "how do I update my profile",
        "where are my saved items",
    ],
    "greeting": [
        "hi",
        "hello",
        "hey there",
        "good morning",
        "thanks",
    ],
}


def _load_intent_anchors_from_registry() -> tuple[dict[str, list[str]], str]:
    """Load intent-anchor utterances from the prompt registry.

    Returns ``(anchors, label)`` where ``label`` identifies the version used
    (e.g. ``intent_anchors@v1``) or an empty string when the fallback constant
    was used.
    """
    try:
        tpl = get_prompt_registry().get("intent_anchors")
    except PromptNotFoundError as exc:
        logger.warning("prompt_registry intent_anchors miss: %s; using in-code default", exc)
        return INTENT_ANCHORS, ""

    payload = tpl.structured
    if not isinstance(payload, dict):
        logger.warning(
            "prompt_registry intent_anchors expected 'structured: {intent: [utterances]}' "
            "in %s; using in-code default",
            tpl.metadata.get("path"),
        )
        return INTENT_ANCHORS, ""

    parsed: dict[str, list[str]] = {}
    for intent, utterances in payload.items():
        if not isinstance(utterances, list) or not utterances:
            continue
        parsed[str(intent)] = [str(u) for u in utterances if isinstance(u, (str, int))]

    if not parsed:
        return INTENT_ANCHORS, ""
    return parsed, tpl.label

# Keyword fallback signals used only when embeddings are unavailable.
_FALLBACK_KEYWORDS: dict[str, set[str]] = {
    "policy_support": {
        "policy", "policies", "refund", "refundable", "return", "returns", "damaged",
        "defective", "wrong", "cancel", "cancellation", "shipping", "delivery", "warranty",
        "exchange", "payment", "security", "privacy", "support",
    },
    "order_status": {"order", "track", "tracking", "package", "shipped", "arrive", "status"},
    "account_help": {"password", "login", "log", "account", "profile", "reset"},
    "product_details": {"material", "size", "sizes", "color", "colors", "spec", "specs", "fit"},
    "product_search": {
        "buy", "price", "cheap", "budget", "under", "product", "products", "style",
        "shoe", "shoes", "bag", "bags", "jacket", "coat", "shirt", "perfume", "sneaker", "backpack",
    },
    "greeting": {"hi", "hello", "hey", "thanks", "morning", "afternoon", "evening"},
}


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticRouter:
    """Classify a query into an intent family via embedding similarity."""

    def __init__(self, min_confidence: float = 0.78) -> None:
        self._min_confidence = min_confidence
        # Anchor utterances come from the prompt registry so intent phrasings can
        # be versioned + A/B tested without a code deploy. Falls back to the
        # in-code INTENT_ANCHORS default when the registry is unavailable.
        self._anchors, self._anchors_label = _load_intent_anchors_from_registry()
        self._azure_ready = bool(
            settings.azure_openai_endpoint
            and settings.azure_openai_api_key
            and settings.azure_openai_embedding_deployment
        )
        self._client = (
            AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
            )
            if self._azure_ready
            else None
        )
        self._deployment = settings.azure_openai_embedding_deployment
        # anchor_vectors[intent] = list of embedding vectors for that intent
        self._anchor_vectors: dict[str, list[list[float]]] = {}
        self._loaded = False
        self._lock = threading.Lock()

    @property
    def anchors_label(self) -> str:
        """Prompt-registry label for the intent anchors currently in use."""
        return self._anchors_label

    @property
    def mode(self) -> str:
        return "semantic" if self._azure_ready else "keyword"

    @property
    def confidence_threshold(self) -> float:
        return self._min_confidence

    def _embed(self, texts: list[str]) -> list[list[float]]:
        from app.services.embedding_provider import embed_texts

        # Symmetric similarity (query vs anchor utterances): use the neutral text type.
        return embed_texts(texts, kind="text")

    def _ensure_loaded(self) -> None:
        if self._loaded or not self._azure_ready:
            return
        with self._lock:
            if self._loaded:
                return
            for intent, utterances in self._anchors.items():
                self._anchor_vectors[intent] = self._embed(utterances)
            self._loaded = True
            logger.info(
                "SemanticRouter anchors embedded for %d intents (prompt=%s)",
                len(self._anchor_vectors),
                self._anchors_label or "builtin",
            )

    def _keyword_classify(self, query: str) -> tuple[str, float]:
        normalized = re.sub(r"[^a-z0-9\s]", " ", query.lower())
        tokens = set(normalized.split())
        best_intent = "product_search"
        best_score = 0
        for intent, keywords in _FALLBACK_KEYWORDS.items():
            overlap = len(tokens & keywords)
            # Policy/support gets a slight priority to avoid product hijacking.
            weight = 1.2 if intent in {"policy_support", "order_status", "account_help"} else 1.0
            score = overlap * weight
            if score > best_score:
                best_score = score
                best_intent = intent
        confidence = min(1.0, 0.5 + 0.2 * best_score) if best_score else 0.0
        return best_intent, confidence

    def classify(self, query: str) -> tuple[str, float, str]:
        """Return (intent, confidence, mode).

        Confidence below ``min_confidence`` should be treated as ambiguous by the
        caller (e.g. ask a clarifying question or use a safe default).
        """
        text = query.strip()
        if not text:
            return "greeting", 1.0, self.mode

        if not self._azure_ready:
            intent, confidence = self._keyword_classify(text)
            return intent, confidence, "keyword"

        try:
            self._ensure_loaded()
            query_vec = self._embed([text])[0]
            best_intent = "product_search"
            best_score = -1.0
            for intent, vectors in self._anchor_vectors.items():
                # Use the max similarity to the closest example in the intent.
                intent_score = max((_cosine(query_vec, v) for v in vectors), default=0.0)
                if intent_score > best_score:
                    best_score = intent_score
                    best_intent = intent
            log_step(
                logger,
                "route_classify",
                enabled=settings.rag_step_logging,
                intent=best_intent,
                score=round(best_score, 4),
                mode="semantic",
            )
            return best_intent, round(best_score, 4), "semantic"
        except Exception as exc:  # noqa: BLE001 - degrade gracefully to keywords
            logger.warning("SemanticRouter falling back to keywords: %r", exc)
            intent, confidence = self._keyword_classify(text)
            return intent, confidence, "keyword-fallback"
