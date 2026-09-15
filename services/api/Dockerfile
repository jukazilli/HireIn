FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv==0.12.13

COPY pyproject.toml uv.lock ./
COPY services/api ./services/api

RUN uv sync --locked --all-packages --no-dev

WORKDIR /app/services/api

CMD ["sh", "-c", "uv run --package hirein-api alembic upgrade head && exec uv run --package hirein-api uvicorn hirein_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
