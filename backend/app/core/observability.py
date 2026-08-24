from __future__ import annotations

import json
import logging
import re
from collections import Counter
from contextvars import ContextVar
from threading import Lock
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
_metrics_lock = Lock()
_requests: Counter[tuple[str, str, str]] = Counter()
_duration_ms: Counter[tuple[str, str]] = Counter()
_logger = logging.getLogger("prescripta.http")


class SafeObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        supplied = request.headers.get("x-request-id", "")
        request_id = supplied if _SAFE_REQUEST_ID.fullmatch(supplied) else str(uuid4())
        token = request_id_context.set(request_id)
        started = perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            elapsed_ms = max(0, round((perf_counter() - started) * 1000))
            route = request.scope.get("route")
            route_label = getattr(route, "path", "unmatched")
            status_code = response.status_code if response is not None else 500
            status_family = f"{status_code // 100}xx"
            with _metrics_lock:
                _requests[(request.method, route_label, status_family)] += 1
                _duration_ms[(request.method, route_label)] += elapsed_ms
            if response is not None:
                response.headers["X-Request-ID"] = request_id
            _logger.info(
                json.dumps(
                    {
                        "event": "http_request_complete",
                        "request_id": request_id,
                        "method": request.method,
                        "route": route_label,
                        "status_family": status_family,
                        "duration_ms": elapsed_ms,
                    },
                    separators=(",", ":"),
                )
            )
            request_id_context.reset(token)


def metrics_snapshot() -> dict:
    with _metrics_lock:
        requests = [
            {"method": method, "route": route, "status": status, "count": count}
            for (method, route, status), count in sorted(_requests.items())
        ]
        durations = [
            {"method": method, "route": route, "total_ms": total}
            for (method, route), total in sorted(_duration_ms.items())
        ]
    return {
        "schema": "bounded-http-metrics-v1",
        "requests": requests,
        "durations": durations,
        "labels": ["method", "route_template", "status_family"],
        "tracing": "optional_not_configured",
    }
