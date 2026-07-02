from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.core.config import settings
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.domain.user import UserRole
from app.repositories.medication_repository import MedicationRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.prescription_schema import (
    AlertRead,
    PrescriptionCheckRequest,
    PrescriptionCheckResponse,
    PrescriptionExplainRequest,
    PrescriptionExplainResponse,
)
from app.services.ai_explainer import AIExplainer
from app.services.audit_service import AuditService
from app.services.risk_engine import RiskEngine

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])
DbSession = Annotated[Session, Depends(get_db)]
PrescriptionChecker = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM)),
]


@router.post("/check", response_model=PrescriptionCheckResponse)
def check_prescription(
    payload: PrescriptionCheckRequest,
    db: DbSession,
    current_user: PrescriptionChecker,
) -> PrescriptionCheckResponse:
    patient_record = PatientRepository(db).get(payload.patient_id)
    if patient_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
        )

    medication_record = MedicationRepository(db).get(payload.medication_id)
    if medication_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento nao encontrado."
        )

    patient = Patient.from_record(patient_record)
    medication = Medication.from_record(medication_record)
    prescription = PrescriptionInput(
        dose_mg=payload.dose_mg,
        frequency_per_day=payload.frequency_per_day,
        route=payload.route,
    )
    result = RiskEngine().evaluate(patient, medication, prescription)
    audit = AuditService(db).record_check(patient, medication, prescription, result, current_user)

    return PrescriptionCheckResponse(
        status=result.status.value,
        risk_level=result.risk_level.value,
        alerts=[AlertRead(**alert.to_dict()) for alert in result.alerts],
        recommendation=result.recommendation,
        human_review_required=result.human_review_required,
        audit_id=audit.id,
    )


@router.post("/explain", response_model=PrescriptionExplainResponse)
def explain_prescription(
    payload: PrescriptionExplainRequest,
    db: DbSession,
    current_user: PrescriptionChecker,
) -> PrescriptionExplainResponse:
    explanation = AIExplainer(settings).explain(payload, requester_role=current_user.role)
    AuditService(db).record_action(
        user=current_user,
        action="prescription.explain",
        resource_type="prescription",
        resource_id=str(payload.audit_id) if payload.audit_id else None,
        status=payload.status,
        risk_level=payload.risk_level,
        details={
            "audit_id": payload.audit_id,
            "alerts_count": len(payload.alerts),
            "critical_alert_codes": explanation.critical_alert_codes,
            "provider": explanation.provider,
            "used_fallback": explanation.used_fallback,
        },
    )
    return explanation
