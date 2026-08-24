from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from threading import Lock, Semaphore
from time import monotonic
from typing import Any

from app.services.canonical_json import canonical_sha256


@dataclass(frozen=True)
class ProviderPolicy:
    requests_per_second: float
    concurrency: int
    max_retries: int = 1
    retry_after_cap_seconds: float = 5.0


POLICIES = {
    # Conservative defaults below the published NCBI unauthenticated ceiling.
    "pubmed": ProviderPolicy(requests_per_second=2.0, concurrency=1),
    "crossref": ProviderPolicy(requests_per_second=2.0, concurrency=1),
    "openalex": ProviderPolicy(requests_per_second=1.0, concurrency=1),
}


class ProviderGovernor:
    def __init__(self) -> None:
        self._lock = Lock()
        self._next_slot = {provider: 0.0 for provider in POLICIES}
        self._semaphores = {
            provider: Semaphore(policy.concurrency) for provider, policy in POLICIES.items()
        }

    def reserve(self, provider: str, sleeper) -> Semaphore:
        policy = POLICIES[provider]
        semaphore = self._semaphores[provider]
        semaphore.acquire()
        with self._lock:
            now = monotonic()
            wait = max(0.0, self._next_slot[provider] - now)
            self._next_slot[provider] = max(now, self._next_slot[provider]) + (
                1.0 / policy.requests_per_second
            )
        if wait:
            sleeper(wait)
        return semaphore


class BoundedTTLCache:
    """Small process-local metadata cache; never stores credentials or response objects."""

    def __init__(self, *, ttl_seconds: int = 900, max_entries: int = 256) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._lock = Lock()
        self._values: dict[str, tuple[float, dict[str, Any]]] = {}

    @staticmethod
    def key(provider: str, url: str, params: dict[str, Any]) -> str:
        safe_params = {key: value for key, value in params.items() if key != "api_key"}
        return canonical_sha256({"provider": provider, "url": url, "params": safe_params})

    def get(self, key: str) -> dict[str, Any] | None:
        now = monotonic()
        with self._lock:
            stored = self._values.get(key)
            if stored is None:
                return None
            expires_at, value = stored
            if expires_at <= now:
                self._values.pop(key, None)
                return None
            return deepcopy(value)

    def put(self, key: str, value: dict[str, Any]) -> None:
        with self._lock:
            if len(self._values) >= self.max_entries:
                oldest = min(self._values, key=lambda item: self._values[item][0])
                self._values.pop(oldest, None)
            self._values[key] = (monotonic() + self.ttl_seconds, deepcopy(value))


GOVERNOR = ProviderGovernor()
CACHE = BoundedTTLCache()
