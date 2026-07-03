from __future__ import annotations

from typing import Protocol


class ConditionSourcePort(Protocol):
    def get_conditions(self) -> list[dict]: ...

    def normalize_conditions(self) -> list[dict]: ...

