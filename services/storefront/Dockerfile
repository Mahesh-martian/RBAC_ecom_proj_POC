# syntax=docker/dockerfile:1.7
# Multi-stage build for the ShopEase FastAPI backend (shopease-api microservice).
FROM python:3.12-slim AS base

# Security: drop root, create an unprivileged user.
RUN groupadd --gid 1001 appgroup && \
    useradd  --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Runtime tools (curl for the container HEALTHCHECK).
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# ── Dependencies layer (cached unless requirements change) ────────────────────
FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Application layer ─────────────────────────────────────────────────────────
FROM deps AS final

COPY --chown=appuser:appgroup app/ ./app/

USER appuser

EXPOSE 5002

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

# Multiple workers for throughput; override CMD for local --reload dev.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "5002", \
     "--workers", "4", \
     "--loop", "uvloop"]
