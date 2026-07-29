from __future__ import annotations

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from app.database.models import (
    AuditEventModel,
    PatientAccessGrantModel,
    PatientModel,
    UserModel,
)


class ObjectAuthorizationService:
    """Aplica escopo institucional ou concessão explícita a recursos de paciente."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def can_access_patient(self, user: UserModel, patient: PatientModel | int) -> bool:
        patient_id = patient if isinstance(patient, int) else patient.id
        institution_id = (
            self.db.scalar(
                select(PatientModel.institution_id).where(PatientModel.id == patient_id)
            )
            if isinstance(patient, int)
            else patient.institution_id
        )
        if institution_id is None:
            return False
        if user.institution_id and user.institution_id == institution_id:
            return True
        return bool(
            self.db.scalar(
                select(
                    exists().where(
                        PatientAccessGrantModel.patient_id == patient_id,
                        PatientAccessGrantModel.user_id == user.id,
                        PatientAccessGrantModel.active.is_(True),
                    )
                )
            )
        )

    def patient_scope(self, user: UserModel):
        granted = select(PatientAccessGrantModel.patient_id).where(
            PatientAccessGrantModel.user_id == user.id,
            PatientAccessGrantModel.active.is_(True),
        )
        return or_(
            PatientModel.institution_id == user.institution_id,
            PatientModel.id.in_(granted),
        )

    def record_denied(self, user: UserModel, *, resource_type: str, resource_id: str) -> None:
        self.db.add(
            AuditEventModel(
                user_id=user.id,
                user_role=user.role,
                action="authorization.denied",
                resource_type=resource_type,
                resource_id=resource_id,
                status="denied",
                details={
                    "institution_id": user.institution_id,
                    "reason": "object_scope_mismatch",
                },
            )
        )
        self.db.commit()

    def require_patient(self, user: UserModel, patient_id: int) -> bool:
        allowed = self.can_access_patient(user, patient_id)
        if not allowed:
            self.record_denied(user, resource_type="patient", resource_id=str(patient_id))
        return allowed
