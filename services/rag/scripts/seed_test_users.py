"""Seed test users and (optionally) smoke-test the RAG chat endpoint.

POC helper for populating the database with many test accounts and validating
the shopping-assistant RAG flow.

Run INSIDE the api container (so DATABASE_URL points at the postgres service):

    docker exec -it ecommerce-api python scripts/seed_test_users.py --count 100
    docker exec -it ecommerce-api python scripts/seed_test_users.py --count 100 --rag-test

Options:
    --count N        Number of test users to create (default: 100).
    --password PWD   Shared password for all test users (default: TestUser1234).
    --rag-test       After seeding, fire sample queries at the chat endpoint.
    --api-url URL    Base API URL for --rag-test (default: http://localhost:8000).
    --rag-samples N  Number of sample queries to send when --rag-test (default: 6).

All test users share the same password and use deterministic emails:
    testuser001@example.com ... testuserNNN@example.com
Existing emails are skipped, so the script is safe to re-run (idempotent).
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import select

from app.db import DatabaseManager
from app.models import User
from app.services.auth import AuthService

EMAIL_TEMPLATE = "testuser{n:03d}@example.com"
DEFAULT_PASSWORD = "TestUser1234"  # >=12 chars, 1 uppercase, 1 digit (passes validation)

# A small spread of intents to exercise the semantic router / RAG flow.
SAMPLE_QUERIES = [
    "what is your refund policy",
    "my item arrived damaged what do I do",
    "where is my order",
    "I forgot my password",
    "show me running shoes",
    "what material is this jacket made of",
    "how long does delivery take",
    "do you offer exchanges",
]


async def seed_users(count: int, password: str) -> tuple[int, int]:
    """Create ``count`` test users. Returns (created, skipped)."""
    password_hash = AuthService.hash_password(password)
    emails = [EMAIL_TEMPLATE.format(n=i) for i in range(1, count + 1)]

    factory = DatabaseManager.get_session_factory()
    async with factory() as session:
        existing_result = await session.execute(
            select(User.email).where(User.email.in_(emails))
        )
        existing = {row[0] for row in existing_result.all()}

        created = 0
        for i, email in enumerate(emails, start=1):
            if email in existing:
                continue
            session.add(
                User(
                    email=email,
                    password_hash=password_hash,
                    name=f"Test User {i:03d}",
                    phone=None,
                    email_verified=True,
                )
            )
            created += 1

        await session.commit()

    return created, len(existing)


def rag_smoke_test(api_url: str, sample_count: int) -> None:
    """Send a handful of queries to the chat endpoint and print the routing."""
    try:
        import httpx
    except ImportError:
        print("  httpx not installed; skipping --rag-test.", file=sys.stderr)
        return

    url = api_url.rstrip("/") + "/chat/query"
    queries = SAMPLE_QUERIES[: max(1, sample_count)]
    print(f"\nRAG smoke test against {url}")
    with httpx.Client(timeout=30.0) as client:
        for q in queries:
            try:
                resp = client.post(url, json={"query": q, "session_id": "seed-smoke"})
                resp.raise_for_status()
                data = resp.json()
                print(
                    f"  [{data.get('response_type', '?'):>14}] "
                    f"provider={data.get('provider', '?'):<16} "
                    f"q={q!r}"
                )
            except Exception as exc:  # noqa: BLE001 - smoke test is best-effort
                print(f"  [ERROR] q={q!r} -> {type(exc).__name__}: {exc}")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Seed test users and smoke-test RAG.")
    parser.add_argument("--count", type=int, default=100, help="Number of test users.")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Shared password.")
    parser.add_argument("--rag-test", action="store_true", help="Run RAG smoke test.")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL.")
    parser.add_argument("--rag-samples", type=int, default=6, help="Sample query count.")
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be >= 1")

    DatabaseManager.initialize()
    try:
        created, skipped = await seed_users(args.count, args.password)
    finally:
        await DatabaseManager.close()

    print(
        f"Seeded test users: {created} created, {skipped} already existed "
        f"(total requested {args.count})."
    )
    print(
        f"Login with any of: {EMAIL_TEMPLATE.format(n=1)} .. "
        f"{EMAIL_TEMPLATE.format(n=args.count)}  /  password: {args.password!r}"
    )

    if args.rag_test:
        rag_smoke_test(args.api_url, args.rag_samples)

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
