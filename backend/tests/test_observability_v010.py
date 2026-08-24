from __future__ import annotations

import json
import logging

from fastapi.testclient import TestClient

from app.domain.user import UserRole


def test_request_id_safe_log_and_bounded_metrics(
    client: TestClient, create_test_user, auth_headers, caplog
) -> None:
    email = "observability-admin@example.test"
    create_test_user(email=email, password="Admin@12345", role=UserRole.ADMIN)
    headers = auth_headers(email, "Admin@12345") | {"X-Request-ID": "release-test-123"}
    with caplog.at_level(logging.INFO, logger="prescripta.http"):
        health = client.get("/health?patient_name=NeverLogMe", headers=headers)
    assert health.status_code == 200
    assert health.headers["X-Request-ID"] == "release-test-123"
    log = next(
        json.loads(record.message) for record in caplog.records if record.name == "prescripta.http"
    )
    assert log["route"] == "/health"
    assert "NeverLogMe" not in json.dumps(log)
    assert set(log) == {"event", "request_id", "method", "route", "status_family", "duration_ms"}

    metrics = client.get("/api/metrics", headers=headers)
    assert metrics.status_code == 200
    assert metrics.json()["labels"] == ["method", "route_template", "status_family"]
    assert metrics.json()["tracing"] == "optional_not_configured"


def test_metrics_require_system_health_capability(
    client: TestClient, create_test_user, auth_headers
) -> None:
    email = "observability-nurse@example.test"
    create_test_user(email=email, password="Admin@12345", role=UserRole.ENFERMAGEM)
    assert client.get("/api/metrics", headers=auth_headers(email, "Admin@12345")).status_code == 403
