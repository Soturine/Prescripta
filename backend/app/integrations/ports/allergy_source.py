from __future__ import annotations

from typing import Protocol


class AllergySourcePort(Protocol):
    def get_allergies(self) -> list[dict]: ...

    def normalize_allergies(self) -> list[dict]: ...

