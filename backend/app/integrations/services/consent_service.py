from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.models import ConsentRecordModel


class ConsentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_import_consent(
        self,
        *,
        consent_confirmed: bool,
        patient_id: int | None,
        authorized_by: str,
        purpose: str,
        source_system: str,
    ) -> ConsentRecordModel:
        if not consent_confirmed:
            raise ValueError("Importacao clinica exige consentimento ou base legal aplicavel.")
        record = ConsentRecordModel(
            patient_id=patient_id,
            authorized_by=authorized_by,
            purpose=purpose,
            source_system=source_system,
        )
        self.db.add(record)
        self.db.flush()
        return record

