# syntax=docker/dockerfile:1.11
FROM python:3.12.13-slim-trixie@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH"

RUN python -m venv /opt/venv \
    && addgroup --system --gid 10001 prescripta \
    && adduser --system --uid 10001 --ingroup prescripta --home /nonexistent --no-create-home prescripta

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
