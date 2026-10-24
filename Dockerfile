
FROM python:3.11-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY requirements.txt .

RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN uv pip install -r requirements.txt


FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="Predator – Face Auth Backend" \
      org.opencontainers.image.description="FastAPI + InsightFace passwordless authentication service" \
      org.opencontainers.image.version="2.0.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

RUN groupadd --gid 1001 appgroup \
 && useradd  --uid 1001 --gid appgroup --create-home appuser

# Tell InsightFace explicitly where to cache models
ENV INSIGHTFACE_ROOT=/home/appuser/.insightface

WORKDIR /app

COPY --chown=appuser:appgroup . .

# Pre-create the model cache directory with correct ownership.
# Docker named volumes inherit the image directory's ownership, so this
# ensures appuser can write the downloaded buffalo_l model at runtime.
RUN mkdir -p /home/appuser/.insightface/models \
 && chown -R appuser:appgroup /home/appuser/.insightface

USER appuser

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8090/auth/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090", "--workers", "1"]
