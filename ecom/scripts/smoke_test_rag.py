"""Cheap pre-flight smoke test for the Azure RAG indexing pipeline.

Embedding is a *paid* service, so before kicking off a full (~2.6k chunk) indexing
run this script validates the whole path end-to-end using only ``limit`` chunks.
It exercises: admin auth -> ensure_index -> embed (paid, but tiny) -> upload, and
confirms the response reports the expected backend and chunk count.

Usage (PowerShell):

    python scripts/smoke_test_rag.py --limit 3
    python scripts/smoke_test_rag.py --base-url http://localhost:8000 --limit 3

Configuration (CLI flags override env vars):
    RAG_BASE_URL        default http://localhost:8000
    RAG_ADMIN_API_KEY   admin key for the /admin/rag endpoints (required)

Exit code 0 = pass, non-zero = fail. Nothing is purged: limited runs never
delete existing documents, so it is safe to run against a populated index.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _post(url: str, admin_key: str, timeout: int) -> tuple[int, dict]:
    req = urllib.request.Request(
        url,
        method="POST",
        headers={"X-Admin-Key": admin_key, "Content-Type": "application/json"},
        data=b"",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, {"raw": body}


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG indexing pre-flight smoke test")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("RAG_BASE_URL", "http://localhost:8000"),
    )
    parser.add_argument("--limit", type=int, default=3, help="chunks to embed (keep small; paid)")
    parser.add_argument("--timeout", type=int, default=120, help="request timeout in seconds")
    parser.add_argument(
        "--admin-key",
        default=os.environ.get("RAG_ADMIN_API_KEY", ""),
        help="admin key (defaults to RAG_ADMIN_API_KEY env var)",
    )
    args = parser.parse_args()

    if not args.admin_key:
        print("FAIL: no admin key. Set RAG_ADMIN_API_KEY or pass --admin-key.", file=sys.stderr)
        return 2
    if args.limit < 1:
        print("FAIL: --limit must be >= 1.", file=sys.stderr)
        return 2

    url = f"{args.base_url.rstrip('/')}/admin/rag/index-policies?limit={args.limit}"
    print(f"-> POST {url}")
    status, payload = _post(url, args.admin_key, args.timeout)
    print(f"<- {status} {json.dumps(payload)}")

    if status != 200:
        print(f"FAIL: expected HTTP 200, got {status}.", file=sys.stderr)
        return 1

    backend = payload.get("backend")
    indexed = payload.get("indexed_chunks")

    if backend == "azure" and indexed == args.limit:
        print(f"PASS: backend=azure, embedded and uploaded {indexed} chunk(s). "
              f"Pipeline healthy - safe to run the full indexing.")
        return 0

    if backend in {"none", "external"} and payload.get("status") == "skipped":
        print(f"WARN: indexing skipped (backend={backend}); Azure RAG not configured here.")
        return 0

    print(f"FAIL: unexpected result (backend={backend}, indexed_chunks={indexed}).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
