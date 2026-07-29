from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


class UnsafeOutboundURLError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedOutboundTarget:
    url: str
    scheme: str
    host: str
    port: int
    addresses: tuple[str, ...]


_LOCAL_ENVIRONMENTS = {"local", "dev", "development", "test", "testing"}
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
_ALTERNATIVE_IPV4 = re.compile(
    r"^(?:0x[0-9a-f]+|[0-9]+|(?:[0-9]+\.){1,3}[0-9]+)$", re.IGNORECASE
)


def validate_outbound_base_url(
    value: str,
    *,
    environment: str,
    allowed_hosts: list[str],
    allow_local_development: bool = False,
    allowed_ports: set[int] | None = None,
) -> str:
    return resolve_outbound_url(
        value,
        environment=environment,
        allowed_hosts=allowed_hosts,
        allow_local_development=allow_local_development,
        allowed_ports=allowed_ports,
    ).url


def resolve_outbound_url(
    value: str,
    *,
    environment: str,
    allowed_hosts: list[str],
    allow_local_development: bool = False,
    allowed_ports: set[int] | None = None,
) -> ResolvedOutboundTarget:
    raw = value.strip()
    if not raw or "\\" in raw or any(ord(character) < 32 for character in raw):
        raise UnsafeOutboundURLError("A URL externa possui formato não permitido.")
    parsed = urlsplit(raw)
    local_environment = environment.strip().lower() in _LOCAL_ENVIRONMENTS
    local_mode = local_environment and allow_local_development
    allowed_schemes = {"http", "https"} if local_mode else {"https"}
    if parsed.scheme.casefold() not in allowed_schemes:
        raise UnsafeOutboundURLError("A URL externa deve usar HTTPS.")
    if (
        not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or parsed.query
    ):
        raise UnsafeOutboundURLError("A URL externa possui formato não permitido.")

    host = _normalize_hostname(parsed.hostname)
    try:
        port = parsed.port or (443 if parsed.scheme.casefold() == "https" else 80)
    except ValueError as exc:
        raise UnsafeOutboundURLError("A porta externa é inválida.") from exc
    effective_ports = allowed_ports or ({443} if parsed.scheme.casefold() == "https" else {80})
    if port not in effective_ports:
        raise UnsafeOutboundURLError("A porta externa não consta na política de saída.")

    normalized_allowlist = {_normalize_hostname(item) for item in allowed_hosts if item.strip()}
    if local_mode:
        if host not in _LOOPBACK_HOSTS:
            raise UnsafeOutboundURLError(
                "Provider local deve usar apenas loopback no ambiente local/teste."
            )
    elif not normalized_allowlist:
        raise UnsafeOutboundURLError(
            "Configure a allowlist PRESCRIPTA_AI_ALLOWED_HOSTS para o provider."
        )
    elif host not in normalized_allowlist:
        raise UnsafeOutboundURLError("O host não consta na allowlist de saída.")

    literal = _literal_ip(host)
    if literal is not None:
        addresses = (literal.compressed,)
    else:
        try:
            resolved = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except (socket.gaierror, UnicodeError) as exc:
            raise UnsafeOutboundURLError("O host externo não pôde ser resolvido.") from exc
        addresses = tuple(
            sorted({str(item[4][0]).split("%", maxsplit=1)[0] for item in resolved})
        )
    if not addresses:
        raise UnsafeOutboundURLError("O host externo não pôde ser resolvido.")
    for address in addresses:
        _validate_address(address, local_mode=local_mode)

    scheme = parsed.scheme.casefold()
    rendered_host = f"[{host}]" if ":" in host else host
    default_port = 443 if scheme == "https" else 80
    netloc = rendered_host if port == default_port else f"{rendered_host}:{port}"
    path = parsed.path.rstrip("/")
    normalized_url = urlunsplit((scheme, netloc, path, "", ""))
    return ResolvedOutboundTarget(
        url=normalized_url,
        scheme=scheme,
        host=host,
        port=port,
        addresses=addresses,
    )


def _normalize_hostname(value: str) -> str:
    host = value.casefold().rstrip(".")
    if not host or "%" in host:
        raise UnsafeOutboundURLError("O hostname externo é inválido.")
    try:
        normalized = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise UnsafeOutboundURLError("O hostname externo é inválido.") from exc
    if len(normalized) > 253:
        raise UnsafeOutboundURLError("O hostname externo é inválido.")
    return normalized


def _literal_ip(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        if _ALTERNATIVE_IPV4.fullmatch(host):
            raise UnsafeOutboundURLError(
                "Endereços IPv4 em representação alternativa não são permitidos."
            ) from None
        return None


def _validate_address(address: str, *, local_mode: bool) -> None:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError as exc:
        raise UnsafeOutboundURLError("A resolução DNS retornou endereço inválido.") from exc
    effective = ip.ipv4_mapped if isinstance(ip, ipaddress.IPv6Address) else None
    effective = effective or ip
    if local_mode:
        if not effective.is_loopback:
            raise UnsafeOutboundURLError(
                "Provider local resolveu fora da interface de loopback."
            )
        return
    if (
        not effective.is_global
        or effective.is_private
        or effective.is_loopback
        or effective.is_link_local
        or effective.is_multicast
        or effective.is_reserved
        or effective.is_unspecified
    ):
        raise UnsafeOutboundURLError("A URL resolve para uma faixa de rede não permitida.")
