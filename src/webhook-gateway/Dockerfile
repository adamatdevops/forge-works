# --- Build stage ---
FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# --- Runtime stage ---
FROM python:3.11-slim

LABEL maintainer="ForgeWorks Team <team@forgeworks.dev>" \
      org.opencontainers.image.source="https://github.com/adamatdevops/forge-works"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --system --no-create-home --uid 10001 appuser

COPY --from=builder /install /usr/local
COPY app/ ./app/

USER 10001
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
