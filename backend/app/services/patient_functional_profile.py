from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import PatientFunctionalProfileModel
from app.schemas.patient_schema import PatientFunctionalProfileRead, PatientFunctionalProfileUpdate

FUNCTIONAL_FIELDS = (
    "drives_regularly",
    "professional_driver",
    "operates_machinery",
    "works_at_height",
    "fall_risk_activity",
    "night_shift",
    "caregiver_responsibility",
    "high_attention_activity",
    "frequent_alcohol_use",
    "history_of_falls",
    "low_tolerance_to_sedation_or_dizziness",
)


class PatientFunctionalProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_for_patient(self, patient_id: int) -> PatientFunctionalProfileModel | None:
        return self.db.scalar(
            select(PatientFunctionalProfileModel).where(
                PatientFunctionalProfileModel.patient_id == patient_id
            )
        )

    def read_for_patient(self, patient_id: int) -> PatientFunctionalProfileRead:
        profile = self.get_for_patient(patient_id)
        if profile is None:
            return PatientFunctionalProfileRead(
                id=None,
                patient_id=patient_id,
                unknown_fields=list(FUNCTIONAL_FIELDS),
            )
        return self._to_read(profile)

    def upsert(
        self, patient_id: int, payload: PatientFunctionalProfileUpdate
    ) -> PatientFunctionalProfileModel:
        profile = self.get_for_patient(patient_id)
        values = payload.model_dump(exclude_unset=True)
        if not values.get("last_reviewed_at"):
            values["last_reviewed_at"] = datetime.now(UTC)
        if profile is None:
            profile = PatientFunctionalProfileModel(patient_id=patient_id, **values)
            self.db.add(profile)
        else:
            for field, value in values.items():
                setattr(profile, field, value)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def _to_read(self, profile: PatientFunctionalProfileModel) -> PatientFunctionalProfileRead:
        unknown_fields = [
            field for field in FUNCTIONAL_FIELDS if getattr(profile, field, None) is None
        ]
        result = PatientFunctionalProfileRead.model_validate(profile)
        result.unknown_fields = unknown_fields
        return result
