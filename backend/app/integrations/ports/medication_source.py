from __future__ import annotations

from typing import Protocol


class MedicationSourcePort(Protocol):
    def get_current_medications(self) -> list[dict]: ...

    def get_medication_history(self) -> list[dict]: ...

    def normalize_medications(self) -> list[dict]: ...

