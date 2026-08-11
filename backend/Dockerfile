# syntax=docker/dockerfile:1.11
FROM python:3.12.13-slim-trixie@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36 AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH"

RUN python -m venv /opt/venv

WORKDIR /app/backend

COPY backend/requirements-lock.txt ./requirements-lock.txt
RUN python -m pip install --no-cache-dir --requirement requirements-lock.txt \
    && python -m pip check

FROM gcr.io/distroless/cc-debian13:nonroot@sha256:d97bc0a941b8d4be647dc0ee75b264ddbb772f1ac5ba690a4309c00723b23775 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app/backend

COPY --from=build /usr/local /usr/local
COPY --from=build /opt/venv /opt/venv
COPY --from=build /usr/lib/x86_64-linux-gnu/libffi.so.8* /usr/lib/x86_64-linux-gnu/
COPY --from=build /usr/lib/x86_64-linux-gnu/libsqlite3.so.0* /usr/lib/x86_64-linux-gnu/
COPY --chown=65532:65532 VERSION /app/VERSION
COPY --chown=65532:65532 backend/app ./app
COPY --chown=65532:65532 backend/migrations ./migrations
COPY --chown=65532:65532 backend/alembic.ini ./alembic.ini

USER 65532:65532
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=5 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()"]

ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app"]
CMD ["--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=127.0.0.1"]
