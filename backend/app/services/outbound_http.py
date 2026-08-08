from __future__ import annotations

import http.client
import json
import socket
import ssl
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode, urlsplit

import httpx

from app.services.safe_url import ResolvedOutboundTarget, resolve_outbound_url

MAX_OUTBOUND_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_OUTBOUND_REQUEST_BYTES = 1024 * 1024
MAX_OUTBOUND_TIMEOUT_SECONDS = 30
_SENSITIVE_HEADERS = {"authorization", "proxy-authorization", "x-api-key", "x-goog-api-key"}
_SENSITIVE_QUERY_KEYS = {"key", "api_key", "apikey", "access_token", "token"}


class SafeOutboundHTTPError(RuntimeError):
    pass


class OutboundRedirectBlocked(SafeOutboundHTTPError):
    pass


class OutboundResponseTooLarge(SafeOutboundHTTPError):
    pass


class OutboundCredentialScopeError(SafeOutboundHTTPError):
    pass


class SafeOutboundHTTPClient:
    """Cliente sem proxy/redirect e com conexão fixada no IP validado."""

    def __init__(
        self,
        *,
        environment: str,
        allowed_hosts: list[str],
        allow_local_development: bool = False,
        allowed_ports: set[int] | None = None,
        max_response_bytes: int = MAX_OUTBOUND_RESPONSE_BYTES,
    ) -> None:
        self.environment = environment
        self.allowed_hosts = list(allowed_hosts)
        self.allow_local_development = allow_local_development
        self.allowed_ports = allowed_ports
        self.max_response_bytes = max_response_bytes

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        timeout_seconds: int | float = 10,
        credential_hosts: set[str] | None = None,
    ) -> httpx.Response:
        target = resolve_outbound_url(
            url,
            environment=self.environment,
            allowed_hosts=self.allowed_hosts,
            allow_local_development=self.allow_local_development,
            allowed_ports=self.allowed_ports,
        )
        normalized_headers = {str(key): str(value) for key, value in (headers or {}).items()}
        self._validate_credential_scope(
            target,
            normalized_headers,
            params or {},
            credential_hosts or set(),
        )
        timeout = max(1.0, min(float(timeout_seconds), MAX_OUTBOUND_TIMEOUT_SECONDS))
        response = self._send(
            method.upper(),
            target,
            headers=normalized_headers,
            json_body=json_body,
            params=params or {},
            timeout=timeout,
        )
        if 300 <= response.status_code < 400:
            raise OutboundRedirectBlocked("Redirect externo bloqueado pela política de saída.")
        if len(response.content) > self.max_response_bytes:
            raise OutboundResponseTooLarge("Resposta externa excede o limite permitido.")
        return response

    def _send(
        self,
        method: str,
        target: ResolvedOutboundTarget,
        *,
        headers: dict[str, str],
        json_body: dict[str, Any] | None,
        params: Mapping[str, Any],
        timeout: float,
    ) -> httpx.Response:
        body = None
        if json_body is not None:
            body = json.dumps(json_body, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )
            if len(body) > MAX_OUTBOUND_REQUEST_BYTES:
                raise SafeOutboundHTTPError("Payload externo excede o limite permitido.")
            headers.setdefault("Content-Type", "application/json")
        headers.setdefault("Accept", "application/json")
        headers.setdefault("User-Agent", "Prescripta/0.8.8")
        headers.setdefault("Connection", "close")
        rendered_host = f"[{target.host}]" if ":" in target.host else target.host
        default_port = 443 if target.scheme == "https" else 80
        headers["Host"] = (
            rendered_host
            if target.port == default_port
            else f"{rendered_host}:{target.port}"
        )
        parsed = urlsplit(target.url)
        request_target = parsed.path or "/"
        if params:
            request_target += "?" + urlencode(params, doseq=True)

        request = httpx.Request(method, target.url)
        last_error: Exception | None = None
        for address in target.addresses:
            connection: http.client.HTTPConnection
            if target.scheme == "https":
                connection = _PinnedHTTPSConnection(
                    target.host,
                    address,
                    target.port,
                    timeout=timeout,
                )
            else:
                connection = _PinnedHTTPConnection(
                    target.host,
                    address,
                    target.port,
                    timeout=timeout,
                )
            try:
                connection.request(method, request_target, body=body, headers=headers)
                raw_response = connection.getresponse()
                content_length = raw_response.getheader("Content-Length")
                if content_length and int(content_length) > self.max_response_bytes:
                    raise OutboundResponseTooLarge(
                        "Resposta externa excede o limite permitido."
                    )
                content = raw_response.read(self.max_response_bytes + 1)
                if len(content) > self.max_response_bytes:
                    raise OutboundResponseTooLarge(
                        "Resposta externa excede o limite permitido."
                    )
                return httpx.Response(
                    raw_response.status,
                    headers=dict(raw_response.getheaders()),
                    content=content,
                    request=request,
                )
            except TimeoutError:
                last_error = httpx.TimeoutException(
                    "Tempo limite da chamada externa excedido.", request=request
                )
                break
            except OutboundResponseTooLarge:
                raise
            except (OSError, ssl.SSLError, http.client.HTTPException):
                last_error = httpx.ConnectError(
                    "Falha na conexão externa validada.", request=request
                )
            finally:
                connection.close()
        if last_error is not None:
            raise last_error
        raise SafeOutboundHTTPError("Nenhum destino externo validado ficou disponível.")

    @staticmethod
    def _validate_credential_scope(
        target: ResolvedOutboundTarget,
        headers: Mapping[str, str],
        params: Mapping[str, Any],
        credential_hosts: set[str],
    ) -> None:
        has_sensitive_header = any(key.casefold() in _SENSITIVE_HEADERS for key in headers)
        has_sensitive_query = any(str(key).casefold() in _SENSITIVE_QUERY_KEYS for key in params)
        if not has_sensitive_header and not has_sensitive_query:
            return
        normalized_hosts = {host.casefold().rstrip(".") for host in credential_hosts}
        if target.host not in normalized_hosts:
            raise OutboundCredentialScopeError(
                "Credencial externa não pode ser enviada a este host."
            )


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(
        self,
        host: str,
        pinned_address: str,
        port: int,
        *,
        timeout: float,
    ) -> None:
        super().__init__(host, port=port, timeout=timeout)
        self._pinned_address = pinned_address

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self._pinned_address, self.port),
            self.timeout,
            self.source_address,
        )


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        host: str,
        pinned_address: str,
        port: int,
        *,
        timeout: float,
    ) -> None:
        super().__init__(
            host,
            port=port,
            timeout=timeout,
            context=ssl.create_default_context(),
        )
        self._pinned_address = pinned_address

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._pinned_address, self.port),
            self.timeout,
            self.source_address,
        )
        self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)
