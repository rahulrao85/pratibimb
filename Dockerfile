# Pratibimb — one container: FastAPI serves the API under /api and the built React UI at /.
# Built for Cloud Run (listens on $PORT; Vertex AI auth comes from the attached service account).

# ---- 1. Build the UI ----
FROM node:20-slim AS ui
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY ui/ ./
RUN npm run build

# ---- 2. Python runtime ----
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY agents/ agents/
COPY app/ app/
COPY data/ data/
COPY --from=ui /ui/dist ui/dist
# Cached Gemini responses and embeddings, if present (an empty cache also works): the first page load costs nothing.
COPY .cache/ .cache/

ENV PATH="/app/.venv/bin:$PATH" \
    GOOGLE_GENAI_USE_VERTEXAI=true \
    GOOGLE_CLOUD_LOCATION=global \
    GEMINI_MODEL=gemini-3.8-flash \
    LLM_DAILY_CALL_CAP=300 \
    ALLOW_BACKTEST_RUN=false \
    PORT=8080

EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
