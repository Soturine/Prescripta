from __future__ import annotations

from dataclasses import dataclass

from app.services.controlled_vocabulary import normalize_clinical_code
from app.services.normalizer import normalize_text

MEDICATION_ALIASES = {
    "dipirona": ("dipirona", "dipirona", 0.95),
    "dipirona sodica": ("dipirona", "dipirona", 0.9),
    "dipirona monoidratada": ("dipirona", "dipirona", 0.9),
    "novalgina": ("dipirona", "dipirona", 0.9),
    "anador": ("dipirona", "dipirona", 0.88),
    "dorflex": ("dipirona", "dipirona", 0.82),
    "neosaldina": ("dipirona", "dipirona", 0.82),
    "lisador": ("dipirona", "dipirona", 0.86),
    "metamizole": ("dipirona", "dipirona", 0.9),
    "metamizol": ("dipirona", "dipirona", 0.9),
    "ibuprofeno": ("ibuprofeno", "ibuprofeno", 0.95),
    "ibuvida": ("ibuprofeno", "ibuprofeno", 0.85),
    "rifampicina": ("rifampicina", "rifampicina", 0.95),
    "rifabutina": ("rifabutina", "rifabutina", 0.95),
}


@dataclass(frozen=True)
class DeduplicationResult:
    original_value: str
    normalized_value: str
    mapped_code: str | None
    confidence: float
    requires_review: bool
    source: str = "manual_curated"
    jurisdiction: str = "BR"
    clinical_category: str | None = None

    def to_dict(self) -> dict:
        payload = {
            "original_value": self.original_value,
            "normalized_value": self.normalized_value,
            "mapped_code": self.mapped_code,
            "confidence": self.confidence,
            "requires_review": self.requires_review,
            "source": self.source,
            "jurisdiction": self.jurisdiction,
        }
        if self.clinical_category:
            payload["clinical_category"] = self.clinical_category
        return payload


class ClinicalDeduplicationService:
    def deduplicate_medication(self, value: str) -> DeduplicationResult:
        normalized = normalize_text(value)
        match = MEDICATION_ALIASES.get(normalized)
        if match:
            normalized_value, mapped_code, confidence = match
            return DeduplicationResult(
                original_value=value,
                normalized_value=normalized_value,
                mapped_code=mapped_code,
                confidence=confidence,
                requires_review=False,
                source="Anvisa/DCB/manual_curated",
                jurisdiction="BR",
            )
        return DeduplicationResult(
            original_value=value,
            normalized_value=normalized,
            mapped_code=None,
            confidence=0.45,
            requires_review=True,
        )

    def deduplicate_condition(self, value: str) -> DeduplicationResult:
        normalized = normalize_text(value)
        for category in (
            "renal",
            "hepatic",
            "cardiac",
            "gastrointestinal",
            "mental_health",
            "reproductive_gynecologic",
            "pregnancy_lactation",
        ):
            code = normalize_clinical_code(category, value)
            if not code or code == "sem_informacao":
                continue
            if code.startswith("sem_"):
                continue
            return DeduplicationResult(
                original_value=value,
                normalized_value=normalized,
                mapped_code=code,
                confidence=0.86 if "a_revisar" not in code else 0.72,
                requires_review="a_revisar" in code,
                source="controlled_vocabulary/manual_curated",
                jurisdiction="BR",
                clinical_category=category,
            )
        return DeduplicationResult(
            original_value=value,
            normalized_value=normalized,
            mapped_code=None,
            confidence=0.4,
            requires_review=True,
        )
