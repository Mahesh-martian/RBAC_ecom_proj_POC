"""Local RAG service for support and policy questions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import re

from app.config import settings


@dataclass
class PolicyChunk:
    chunk_id: str
    title: str
    source: str
    content: str
    terms: set[str]
    audience: str = "common"


class SupportRAGService:
    """Simple retrieval over local policy markdown documents."""

    def __init__(self, policies_dir: Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        self._policies_dir = policies_dir or (base_dir / "policies")
        self._chunks: list[PolicyChunk] = []
        self._loaded = False

    def _tokenize(self, text: str) -> list[str]:
        cleaned = re.sub(r"[^a-z0-9\s]", " ", text.lower())
        words = [w for w in cleaned.split() if len(w) > 2]
        return words

    def _load(self) -> None:
        if self._loaded:
            return

        self._chunks = []
        if not self._policies_dir.exists():
            self._loaded = True
            return

        # Documents are organized into audience subfolders (customer/, vendor/,
        # common/). The immediate parent folder name is the audience tag; files at
        # the policies root default to "common" so they are visible to everyone.
        for file_path in sorted(self._policies_dir.rglob("*.md")):
            parent_name = file_path.parent.name.lower()
            audience = parent_name if file_path.parent != self._policies_dir else "common"
            text = file_path.read_text(encoding="utf-8")
            title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else file_path.stem

            sections = [s.strip() for s in text.split("\n\n") if s.strip()]
            for idx, section in enumerate(sections):
                terms = set(self._tokenize(section))
                self._chunks.append(
                    PolicyChunk(
                        chunk_id=f"{file_path.stem}-{idx}",
                        title=title,
                        source=file_path.name,
                        content=section,
                        terms=terms,
                        audience=audience,
                    )
                )

        self._loaded = True

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        audiences: Optional[set[str]] = None,
    ) -> list[tuple[int, PolicyChunk]]:
        self._load()
        if not self._chunks:
            return []

        q_terms = set(self._tokenize(query))
        if not q_terms:
            return []

        allowed = {a.lower() for a in audiences} if audiences else None
        scored: list[tuple[int, PolicyChunk]] = []
        for chunk in self._chunks:
            if allowed is not None and chunk.audience not in allowed:
                continue
            overlap = len(q_terms & chunk.terms)
            if overlap <= 0:
                continue

            boost = 0
            lower_content = chunk.content.lower()
            if "refund" in query.lower() and "refund" in lower_content:
                boost += 2
            if "return" in query.lower() and "return" in lower_content:
                boost += 2
            if "shipping" in query.lower() and "shipping" in lower_content:
                boost += 2
            if "delivery" in query.lower() and "delivery" in lower_content:
                boost += 2
            if "cancel" in query.lower() and "cancel" in lower_content:
                boost += 2
            if "payment" in query.lower() and "payment" in lower_content:
                boost += 2

            score = overlap + boost
            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[:top_k]

    def answer(
        self,
        query: str,
        top_k: int = 3,
        audiences: Optional[set[str]] = None,
    ) -> tuple[str, list[str], float]:
        scored_chunks = self.retrieve(query, top_k=top_k, audiences=audiences)
        if not scored_chunks:
            return (
                "I do not have enough policy context to answer that yet. Please contact support with your order number.",
                [],
                0.0,
            )

        top_score = scored_chunks[0][0]
        if top_score < settings.rag_min_local_score:
            return (
                "I do not have enough policy context to answer that yet. Please contact support with your order number.",
                [],
                float(top_score),
            )

        chunks = [chunk for _, chunk in scored_chunks]

        bullet_points = []
        cited_sources: list[str] = []
        seen_sources: set[str] = set()
        for chunk in chunks:
            snippet = chunk.content.replace("\n", " ").strip()
            if len(snippet) > 220:
                snippet = snippet[:217] + "..."
            bullet_points.append(f"- {snippet}")
            citation = f"{chunk.title} ({chunk.source})"
            if citation not in seen_sources:
                seen_sources.add(citation)
                cited_sources.append(citation)

        response = (
            "Based on our policy documents:\n"
            + "\n".join(bullet_points)
            + "\nIf you share your order number, I can guide you through the exact next step."
        )
        return response, cited_sources, float(top_score)
