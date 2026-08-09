# syntax=docker/dockerfile:1.11
FROM python:3.12.13-alpine3.23@sha256:601d3d3797e90e2534782e69c85fafb7971b43f24c7b1b079b7e48dd435e458d AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH"

RUN python -m venv /opt/venv \
    && addgroup -S -g 10001 prescripta \
    && adduser -S -D -H -u 10001 -G prescripta prescripta

WORKDIR /app/backend

COPY backend/requirements-lock.txt ./requirements-lock.txt
RUN python -m pip install --no-cache-dir --requirement requirements-lock.txt \
    && python -m pip check

COPY --chown=prescripta:prescripta VERSION /app/VERSION
COPY --chown=prescripta:prescripta backend/app ./app
COPY --chown=prescripta:prescripta backend/migrations ./migrations
COPY --chown=prescripta:prescripta backend/alembic.ini ./alembic.ini

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=5 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()"]

ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app"]
CMD ["--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=127.0.0.1"]
