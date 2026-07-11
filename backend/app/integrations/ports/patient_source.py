from __future__ import annotations

from typing import Protocol


class PatientSourcePort(Protocol):
    def get_patient(self) -> dict: ...

    def get_patient_identifiers(self) -> list[dict]: ...

    def normalize_patient(self) -> dict: ...
