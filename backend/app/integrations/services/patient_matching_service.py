from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import PatientModel
from app.services.normalizer import normalize_text
from app.services.patient_identifier_service import PatientIdentifierService


@dataclass(frozen=True)
class PatientMatchCandidate:
    patient_id: int
    score: float
    reasons: list[str]
    requires_human_review: bool = True
    auto_merge_allowed: bool = False

    def to_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "score": self.score,
            "reasons": self.reasons,
            "requires_human_review": self.requires_human_review,
            "auto_merge_allowed": self.auto_merge_allowed,
        }


class PatientMatchingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.identifier_service = PatientIdentifierService(db)

    def find_matches(
        self,
        *,
        patient_payload: dict,
        identifiers: list[dict] | None = None,
    ) -> list[PatientMatchCandidate]:
        candidates: dict[int, PatientMatchCandidate] = {}
        for identifier in identifiers or []:
            identifier_type = str(identifier.get("identifier_type") or "")
            identifier_value = str(identifier.get("identifier_value") or "")
            if not identifier_type or not identifier_value:
                continue
            for existing in self.identifier_service.find_by_value(
                identifier_type=identifier_type,
                identifier_value=identifier_value,
            ):
                candidates[existing.patient_id] = PatientMatchCandidate(
                    patient_id=existing.patient_id,
                    score=0.99,
                    reasons=[f"identificador exato: {existing.identifier_type}"],
                )

        incoming_name = normalize_text(str(patient_payload.get("name") or ""))
        incoming_birth = patient_payload.get("birth_date")
        incoming_phone = normalize_text(str(patient_payload.get("phone") or ""))
        incoming_email = normalize_text(str(patient_payload.get("email") or ""))
        incoming_mother = normalize_text(str(patient_payload.get("mother_name") or ""))
        if not incoming_name:
            return sorted(candidates.values(), key=lambda item: item.score, reverse=True)

        for patient in self.db.scalars(select(PatientModel)):
            if patient.id in candidates:
                continue
            name_score = SequenceMatcher(
                None,
                incoming_name,
                normalize_text(patient.name),
            ).ratio()
            same_birth = bool(incoming_birth and patient.birth_date == incoming_birth)
            same_phone = bool(incoming_phone and incoming_phone == normalize_text(patient.phone))
            same_email = bool(incoming_email and incoming_email == normalize_text(patient.email))
            same_mother = bool(
                incoming_mother and incoming_mother == normalize_text(patient.mother_name)
            )
            reasons: list[str] = []
            score = name_score * 0.45
            if same_birth:
                score += 0.2
                reasons.append("nome normalizado + data de nascimento")
            if same_phone or same_email:
                score += 0.2
                reasons.append("telefone/email coincide")
            if same_mother:
                score += 0.15
                reasons.append("nome da mae coincide")
            if name_score >= 0.9 and same_birth and not (same_phone or same_email or same_mother):
                reasons.append("nome + nascimento apenas; merge automatico proibido")
            if score >= 0.65:
                candidates[patient.id] = PatientMatchCandidate(
                    patient_id=patient.id,
                    score=round(min(score, 0.95), 2),
                    reasons=reasons or ["similaridade textual"],
                )

        return sorted(candidates.values(), key=lambda item: item.score, reverse=True)
