from __future__ import annotations

from typing import Protocol


class ObservationSourcePort(Protocol):
    def get_observations(self) -> list[dict]: ...

    def normalize_observations(self) -> list[dict]: ...

