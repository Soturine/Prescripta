from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit


class UnsafeOutboundURLError(ValueError):
    pass


def validate_outbound_base_url(
    value: str,
    *,
    environment: str,
    allowed_hosts: list[str],
    allow_local_development: bool = False,
) -> str:
    parsed = urlsplit(value.strip())
    local_environment = environment.lower() in {
        "local",
        "dev",
        "development",
        "test",
        "testing",
    }
    if parsed.scheme not in ({"http", "https"} if local_environment else {"https"}):
        raise UnsafeOutboundURLError("A URL externa deve usar HTTPS.")
    if not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise UnsafeOutboundURLError("A URL externa possui formato não permitido.")
    host = parsed.hostname.casefold().rstrip(".")
    allow_local = local_environment and allow_local_development
    normalized_allowlist = {item.casefold().rstrip(".") for item in allowed_hosts}
    if not allow_local and normalized_allowlist and host not in normalized_allowlist:
        raise UnsafeOutboundURLError("O host não consta na allowlist de saída.")
    if not allow_local and not normalized_allowlist:
        raise UnsafeOutboundURLError(
            "Configure a allowlist PRESCRIPTA_AI_ALLOWED_HOSTS para o provider."
        )
    if host == "localhost" and not allow_local:
        raise UnsafeOutboundURLError("Hosts locais não são permitidos.")
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise UnsafeOutboundURLError("O host externo não pôde ser resolvido.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ) and not allow_local:
            raise UnsafeOutboundURLError("A URL resolve para uma faixa de rede não permitida.")
    return value.rstrip("/")
