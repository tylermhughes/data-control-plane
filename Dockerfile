# One image for both the API server and the background worker.

# Step 1: build the web interface (Node is only needed here, not in the final image).
FROM node:24.21.0-alpine AS web
WORKDIR /repo/web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# Step 2: the Python app, with the built web interface served at /.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /srv

# Install libraries first so code changes don't trigger a full reinstall.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY --from=web /repo/web/dist /srv/web

RUN useradd --system --uid 10001 dcp
USER dcp

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
