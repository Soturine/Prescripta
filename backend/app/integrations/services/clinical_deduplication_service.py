from __future__ import annotations

from dataclasses import dataclass

from app.services.controlled_vocabulary import normalize_clinical_code
from app.services.normalizer import normalize_text

MEDICATION_ALIASES = {
    "dipirona": ("dipirona", "dipirona", 0.95),
    "dipirona sodica": ("dipirona", "dipirona", 0.9),
    "novalgina": ("dipirona", "dipirona", 0.9),
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

    def to_dict(self) -> dict:
        return {
            "original_value": self.original_value,
            "normalized_value": self.normalized_value,
            "mapped_code": self.mapped_code,
            "confidence": self.confidence,
            "requires_review": self.requires_review,
            "source": self.source,
            "jurisdiction": self.jurisdiction,
        }


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
        renal_code = normalize_clinical_code("renal", value)
        if renal_code in {"doenca_renal_cronica", "funcao_renal_a_revisar"}:
            return DeduplicationResult(
                original_value=value,
                normalized_value="doenca renal cronica"
                if renal_code == "doenca_renal_cronica"
                else "funcao renal a revisar",
                mapped_code=renal_code,
                confidence=0.85,
                requires_review=renal_code == "funcao_renal_a_revisar",
            )
        return DeduplicationResult(
            original_value=value,
            normalized_value=normalized,
            mapped_code=None,
            confidence=0.4,
            requires_review=True,
        )
