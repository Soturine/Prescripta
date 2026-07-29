import socket

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, UnsafeRuntimeConfiguration, validate_runtime_settings
from app.domain.user import UserRole
from app.services.safe_url import UnsafeOutboundURLError, validate_outbound_base_url


def test_non_local_startup_rejects_demo_defaults():
    with pytest.raises(UnsafeRuntimeConfiguration):
        validate_runtime_settings(Settings(environment="production"))


def test_non_local_startup_accepts_explicit_safe_configuration():
    validate_runtime_settings(
        Settings(
            environment="production",
            database_url="postgresql+psycopg://prescripta@db/prescripta",
            secret_key="production-secret-provided-by-secret-manager",
            auto_seed=False,
            cors_origins=["https://prescripta.example"],
            config_encryption_key="configured-by-secret-manager",
        )
    )


def test_ssrf_validator_rejects_loopback_and_requires_allowlist(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(UnsafeOutboundURLError):
        validate_outbound_base_url(
            "https://metadata.example/v1",
            environment="production",
            allowed_hosts=["metadata.example"],
        )
    with pytest.raises(UnsafeOutboundURLError, match="allowlist"):
        validate_outbound_base_url(
            "https://provider.example/v1",
            environment="production",
            allowed_hosts=[],
        )


def test_ssrf_validator_accepts_allowlisted_public_host(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )
    assert (
        validate_outbound_base_url(
            "https://provider.example/v1/",
            environment="production",
            allowed_hosts=["provider.example"],
        )
        == "https://provider.example/v1"
    )


def test_login_is_rate_limited_and_lockout_is_persisted(
    client: TestClient, create_test_user
):
    create_test_user(
        email="rate@test.local", password="Correct@123", role=UserRole.MEDICO
    )
    for _ in range(5):
        response = client.post(
            "/api/auth/login",
            json={"email": "rate@test.local", "password": "wrong"},
        )
        assert response.status_code == 401
    locked = client.post(
        "/api/auth/login",
        json={"email": "rate@test.local", "password": "Correct@123"},
    )
    assert locked.status_code == 429
    assert locked.headers["retry-after"] == "900"


def test_http_only_cookie_authentication_and_logout(client: TestClient, create_test_user):
    create_test_user(
        email="cookie@test.local", password="Cookie@123", role=UserRole.MEDICO
    )
    login = client.post(
        "/api/auth/login",
        json={"email": "cookie@test.local", "password": "Cookie@123"},
    )
    assert login.status_code == 200
    cookie_header = login.headers.get("set-cookie", "").lower()
    assert "prescripta_session=" in cookie_header
    assert "httponly" in cookie_header
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401
