from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import PatientIdentifierModel

ALLOWED_IDENTIFIER_TYPES = {
    "internal_record_number",
    "hospital_record_number",
    "insurance_member_number",
    "CNS",
    "CPF",
    "external_system_id",
}


def normalize_identifier_type(identifier_type: str) -> str:
    value = identifier_type.strip()
    if value.upper() in {"CPF", "CNS"}:
        return value.upper()
    return value.lower()


def hash_identifier(identifier_type: str, identifier_value: str) -> str:
    normalized_type = normalize_identifier_type(identifier_type)
    normalized_value = "".join(char for char in identifier_value if char.isalnum()).upper()
    payload = f"{settings.secret_key}:{normalized_type}:{normalized_value}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def mask_identifier(identifier_type: str, identifier_value: str) -> str:
    normalized_type = normalize_identifier_type(identifier_type)
    compact = "".join(char for char in identifier_value if char.isalnum())
    if not compact:
        return "***"
    visible = compact[-4:] if len(compact) >= 4 else compact[-2:]
    return f"{normalized_type}: ***{visible}"


class PatientIdentifierService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        patient_id: int,
        identifier_type: str,
        identifier_value: str,
        issuing_system: str | None = None,
        is_primary: bool = False,
    ) -> PatientIdentifierModel:
        normalized_type = normalize_identifier_type(identifier_type)
        if normalized_type not in ALLOWED_IDENTIFIER_TYPES:
            raise ValueError("Tipo de identificador nao permitido.")
        identifier_hash = hash_identifier(normalized_type, identifier_value)
        existing = self.db.scalar(
            select(PatientIdentifierModel).where(
                PatientIdentifierModel.patient_id == patient_id,
                PatientIdentifierModel.identifier_type == normalized_type,
                PatientIdentifierModel.identifier_value_hash == identifier_hash,
            )
        )
        if existing:
            return existing
        if is_primary:
            self.db.query(PatientIdentifierModel).filter(
                PatientIdentifierModel.patient_id == patient_id
            ).update({"is_primary": False})
        record = PatientIdentifierModel(
            patient_id=patient_id,
            identifier_type=normalized_type,
            identifier_value_hash=identifier_hash,
            issuing_system=issuing_system,
            display_masked=mask_identifier(normalized_type, identifier_value),
            is_primary=is_primary,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_for_patient(self, patient_id: int) -> list[PatientIdentifierModel]:
        return list(
            self.db.scalars(
                select(PatientIdentifierModel)
                .where(PatientIdentifierModel.patient_id == patient_id)
                .order_by(PatientIdentifierModel.is_primary.desc(), PatientIdentifierModel.id)
            )
        )

    def find_by_value(
        self,
        *,
        identifier_type: str,
        identifier_value: str,
    ) -> list[PatientIdentifierModel]:
        normalized_type = normalize_identifier_type(identifier_type)
        identifier_hash = hash_identifier(normalized_type, identifier_value)
        return list(
            self.db.scalars(
                select(PatientIdentifierModel).where(
                    PatientIdentifierModel.identifier_type == normalized_type,
                    PatientIdentifierModel.identifier_value_hash == identifier_hash,
                )
            )
        )
