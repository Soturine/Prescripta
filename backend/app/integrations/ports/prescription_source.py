from __future__ import annotations

from typing import Protocol


class PrescriptionSourcePort(Protocol):
    def get_medication_request(self) -> dict: ...

    def normalize_prescription(self) -> dict: ...

