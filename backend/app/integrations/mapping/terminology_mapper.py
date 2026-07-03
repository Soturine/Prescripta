from __future__ import annotations

from app.integrations.services.clinical_deduplication_service import ClinicalDeduplicationService
from app.services.controlled_vocabulary import normalize_clinical_code, normalize_clinical_terms
from app.services.normalizer import normalize_text


class TerminologyMapper:
    def __init__(self) -> None:
        self.deduplication = ClinicalDeduplicationService()

    def medication(self, value: str) -> dict:
        return self.deduplication.deduplicate_medication(value).to_dict()

    def condition(self, value: str) -> dict:
        return self.deduplication.deduplicate_condition(value).to_dict()

    def allergy(self, value: str) -> dict:
        normalized = normalize_text(value)
        medication = self.deduplication.deduplicate_medication(value)
        return {
            "original_value": value,
            "normalized_value": (
                medication.normalized_value if medication.confidence >= 0.85 else normalized
            ),
            "mapped_code": medication.mapped_code,
            "confidence": medication.confidence if medication.confidence >= 0.85 else 0.55,
            "requires_review": True,
        }

    def mental_health(self, values: list[str]) -> list[str]:
        return normalize_clinical_terms("mental_health", values)

    def reproductive_gynecologic(self, values: list[str]) -> list[str]:
        return normalize_clinical_terms("reproductive_gynecologic", values)

    def clinical_code(self, category: str, value: str | None) -> str | None:
        return normalize_clinical_code(category, value)
