from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.core.config import settings
from app.database.models import PrescriptionAuditModel, UserModel
from app.database.session import get_db
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.domain.user import UserRole
from app.knowledge.rag_service import ClinicalRAGService
from app.repositories.medication_repository import MedicationRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.prescription_schema import (
    AlertRead,
    PatientCounselingResponse,
    PrescriptionCheckRequest,
    PrescriptionCheckResponse,
    PrescriptionExplainRequest,
    PrescriptionExplainResponse,
)
from app.services.ai_explainer import AIExplainer
from app.services.alternative_service import AlternativeService
from app.services.audit_service import AuditService
from app.services.clinical_context_graph import build_clinical_context_graph
from app.services.patient_counseling_service import PatientCounselingService
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado."
        )

    medication_record = MedicationRepository(db).get(payload.medication_id)
    if medication_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento não encontrado."
        )

    patient = Patient.from_record(patient_record)
    medication = Medication.from_record(medication_record)
    prescription = PrescriptionInput(
        dose_mg=payload.dose_mg,
        frequency_per_day=payload.frequency_per_day,
        route=payload.route,
        duration_days=payload.duration_days,
        indication=payload.indication,
        professional_notes=payload.professional_notes,
    )
    result = RiskEngine().evaluate(patient, medication, prescription)
    rag_evidence = ClinicalRAGService().retrieve_for_prescription(patient, medication, prescription)
    result.clinical_context_graph.update(
        build_clinical_context_graph(
            patient,
            medication,
            prescription,
            [alert.to_dict() for alert in result.alerts],
            rag_evidence,
        )
    )
    should_include_alternatives = (
        result.compatibility["level"] == "baixa" or result.status.value == "bloqueado"
    )
    alternatives = AlternativeService(MedicationRepository(db)).evaluated_options(
        patient,
        medication,
        prescription,
        should_include=should_include_alternatives,
    )
    audit = AuditService(db).record_check(patient, medication, prescription, result, current_user)
    patient_counseling = PatientCounselingService(db).build_for_prescription(
        patient_record,
        medication_record,
        contextual_activity_answer=payload.contextual_activity_answer,
    )

    return PrescriptionCheckResponse(
        status=result.status.value,
        risk_level=result.risk_level.value,
        alerts=[AlertRead(**alert.to_dict()) for alert in result.alerts],
        recommendation=result.recommendation,
        human_review_required=result.human_review_required,
        audit_id=audit.id,
        dose_summary=result.dose_summary,
        compatibility=result.compatibility,
        patient_factors_considered=result.compatibility["patient_factors_considered"],
        medication_factors_considered=result.compatibility["medication_factors_considered"],
        rag_evidence=rag_evidence,
        clinical_context_graph=result.clinical_context_graph,
        alternatives=alternatives,
        patient_counseling=patient_counseling,
        missing_data_mode=patient_counseling.missing_data_mode,
        contextual_question=patient_counseling.functional_context.question,
    )


@router.post("/explain", response_model=PrescriptionExplainResponse)
def explain_prescription(
    payload: PrescriptionExplainRequest,
    db: DbSession,
    current_user: PrescriptionChecker,
) -> PrescriptionExplainResponse:
    explanation = AIExplainer(settings, db).explain(payload, requester_role=current_user.role)
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


@router.post("/{audit_id}/patient-counseling", response_model=PatientCounselingResponse)
def patient_counseling_for_audit(
    audit_id: int,
    db: DbSession,
    _current_user: PrescriptionChecker,
) -> PatientCounselingResponse:
    audit = db.get(PrescriptionAuditModel, audit_id)
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checagem de prescricao nao encontrada.",
        )
    patient_record = PatientRepository(db).get(audit.patient_id) if audit.patient_id else None
    medication_record = (
        MedicationRepository(db).get(audit.medication_id) if audit.medication_id else None
    )
    if patient_record is None or medication_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente ou medicamento da checagem nao encontrado.",
        )
    return PatientCounselingService(db).build_for_prescription(
        patient_record,
        medication_record,
    )
