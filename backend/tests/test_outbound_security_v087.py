from __future__ import annotations

import socket

import httpx
import pytest

from app.core.config import Settings
from app.services.ai_settings import AIConfigurationError, AISettingsService
from app.services.outbound_http import (
    OutboundCredentialScopeError,
    OutboundRedirectBlocked,
    OutboundResponseTooLarge,
    SafeOutboundHTTPClient,
)
from app.services.safe_url import (
    UnsafeOutboundURLError,
    resolve_outbound_url,
    validate_outbound_base_url,
)

PUBLIC_ADDRESS = "93.184.216.34"


def _dns(address: str):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))]


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost",
        "https://127.0.0.1",
        "https://[::1]",
        "https://169.254.169.254/latest/meta-data",
        "https://224.0.0.1",
        "https://0.0.0.0",
        "https://[::ffff:127.0.0.1]",
    ],
)
def test_private_special_and_ipv6_mapped_targets_are_blocked(url: str) -> None:
    host = url.split("//", maxsplit=1)[1].split("/", maxsplit=1)[0].strip("[]")
    with pytest.raises(UnsafeOutboundURLError):
        validate_outbound_base_url(
            url,
            environment="production",
            allowed_hosts=[host],
            allowed_ports={443},
        )


@pytest.mark.parametrize(
    "host",
    ["2130706433", "0x7f000001", "127.1", "0177.0.0.1", "127.000.000.001"],
)
def test_alternative_ipv4_representations_are_rejected(host: str) -> None:
    with pytest.raises(UnsafeOutboundURLError, match="alternativa"):
        validate_outbound_base_url(
            f"https://{host}",
            environment="production",
            allowed_hosts=[host],
        )


def test_url_normalization_is_exact_and_rejects_deceptive_hosts(monkeypatch) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_args, **_kwargs: _dns(PUBLIC_ADDRESS))
    assert validate_outbound_base_url(
        "https://Provider.Example./v1/",
        environment="production",
        allowed_hosts=["provider.example"],
    ) == "https://provider.example/v1"
    with pytest.raises(UnsafeOutboundURLError, match="allowlist"):
        validate_outbound_base_url(
            "https://provider.example.attacker.test/v1",
            environment="production",
            allowed_hosts=["provider.example"],
        )


@pytest.mark.parametrize(
    "url",
    [
        "https://user:secret@provider.example/v1",
        "https://provider.example/v1#fragment",
        "https://provider.example/v1?api_key=secret",
        "https://provider.example:8443/v1",
    ],
)
def test_credentials_fragments_queries_and_unapproved_ports_are_rejected(
    url: str, monkeypatch
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_args, **_kwargs: _dns(PUBLIC_ADDRESS))
    with pytest.raises(UnsafeOutboundURLError):
        validate_outbound_base_url(
            url,
            environment="production",
            allowed_hosts=["provider.example"],
            allowed_ports={443},
        )


def test_dns_failure_is_fail_closed(monkeypatch) -> None:
    def fail_dns(*_args, **_kwargs):
        raise socket.gaierror("demo failure")

    monkeypatch.setattr(socket, "getaddrinfo", fail_dns)
    with pytest.raises(UnsafeOutboundURLError, match="resolvido"):
        resolve_outbound_url(
            "https://provider.example/v1",
            environment="production",
            allowed_hosts=["provider.example"],
        )


def test_dns_resolution_is_pinned_for_the_request(monkeypatch) -> None:
    resolutions = iter((PUBLIC_ADDRESS, "127.0.0.1"))
    calls = {"dns": 0}

    def alternating_dns(*_args, **_kwargs):
        calls["dns"] += 1
        return _dns(next(resolutions))

    monkeypatch.setattr(socket, "getaddrinfo", alternating_dns)
    client = SafeOutboundHTTPClient(
        environment="production",
        allowed_hosts=["provider.example"],
        allowed_ports={443},
    )
    captured: dict[str, tuple[str, ...]] = {}

    def fake_send(_method, target, **_kwargs):
        captured["addresses"] = target.addresses
        return httpx.Response(
            200,
            content=b'[{"ok":true}]',
            request=httpx.Request("GET", target.url),
        )

    monkeypatch.setattr(client, "_send", fake_send)
    response = client.request("GET", "https://provider.example/v1", timeout_seconds=5)

    assert response.status_code == 200
    assert calls["dns"] == 1
    assert captured["addresses"] == (PUBLIC_ADDRESS,)


@pytest.mark.parametrize(
    "location",
    ["http://127.0.0.1/admin", "https://attacker.example/steal"],
)
def test_redirects_are_never_followed(location: str, monkeypatch) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_args, **_kwargs: _dns(PUBLIC_ADDRESS))
    client = SafeOutboundHTTPClient(
        environment="production", allowed_hosts=["provider.example"]
    )

    def fake_send(_method, target, **_kwargs):
        return httpx.Response(
            302,
            headers={"Location": location},
            request=httpx.Request("GET", target.url),
        )

    monkeypatch.setattr(client, "_send", fake_send)
    with pytest.raises(OutboundRedirectBlocked):
        client.request("GET", "https://provider.example/v1")


def test_oversized_response_is_rejected(monkeypatch) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_args, **_kwargs: _dns(PUBLIC_ADDRESS))
    client = SafeOutboundHTTPClient(
        environment="production",
        allowed_hosts=["provider.example"],
        max_response_bytes=32,
    )

    def fake_send(_method, target, **_kwargs):
        return httpx.Response(
            200,
            content=b"x" * 33,
            request=httpx.Request("GET", target.url),
        )

    monkeypatch.setattr(client, "_send", fake_send)
    with pytest.raises(OutboundResponseTooLarge):
        client.request("GET", "https://provider.example/v1")


def test_timeout_is_bounded_and_propagated(monkeypatch) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_args, **_kwargs: _dns(PUBLIC_ADDRESS))
    client = SafeOutboundHTTPClient(
        environment="production", allowed_hosts=["provider.example"]
    )
    captured: dict[str, float] = {}

    def fake_send(_method, target, **kwargs):
        captured["timeout"] = kwargs["timeout"]
        raise httpx.TimeoutException("timeout", request=httpx.Request("GET", target.url))

    monkeypatch.setattr(client, "_send", fake_send)
    with pytest.raises(httpx.TimeoutException):
        client.request(
            "GET", "https://provider.example/v1", timeout_seconds=999
        )
    assert captured["timeout"] == 30


def test_credentials_are_forwarded_only_to_the_exact_expected_host(monkeypatch) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_args, **_kwargs: _dns(PUBLIC_ADDRESS))
    client = SafeOutboundHTTPClient(
        environment="production", allowed_hosts=["provider.example"]
    )
    with pytest.raises(OutboundCredentialScopeError):
        client.request(
            "GET",
            "https://provider.example/v1",
            headers={"Authorization": "Bearer secret"},
            credential_hosts={"other.example"},
        )


def test_local_ollama_policy_allows_only_loopback_and_expected_port(monkeypatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: _dns("127.0.0.1"),
    )
    assert validate_outbound_base_url(
        "http://localhost:11434",
        environment="development",
        allowed_hosts=[],
        allow_local_development=True,
        allowed_ports={11434},
    ) == "http://localhost:11434"
    with pytest.raises(UnsafeOutboundURLError):
        validate_outbound_base_url(
            "http://169.254.169.254:11434",
            environment="development",
            allowed_hosts=[],
            allow_local_development=True,
            allowed_ports={11434},
        )


def test_official_provider_rejects_custom_base_url(db_session) -> None:
    service = AISettingsService(
        db_session,
        Settings(environment="test", ai_allowed_hosts=["attacker.example"]),
    )
    with pytest.raises(AIConfigurationError, match="endpoint fixo"):
        service.runtime_config(
            provider_override="openai",
            base_url_override="https://attacker.example/v1",
        )
