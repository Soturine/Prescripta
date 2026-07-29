from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.core.config import settings
from app.database.models import (
    DecisionOverrideModel,
    PatientFunctionalProfileModel,
    PrescriptionAuditModel,
    UserModel,
)
from app.database.session import get_db
from app.domain.dose import MedicationDoseInput
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.domain.user import UserRole
from app.knowledge.rag_service import ClinicalRAGService
from app.repositories.medication_repository import MedicationRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.prescription_schema import (
    AlertRead,
    DecisionOverrideRead,
    DecisionOverrideRequest,
    DecisionOverrideReviewRequest,
    PatientCounselingResponse,
    PrescriptionCheckRequest,
    PrescriptionCheckResponse,
    PrescriptionExplainByAuditRequest,
    PrescriptionExplainResponse,
)
from app.services.ai_explainer import AIExplainer
from app.services.alternative_service import AlternativeService
from app.services.audit_service import AuditService
from app.services.clinical_context_graph import build_clinical_context_graph
from app.services.clinical_decision_orchestrator import ClinicalDecisionOrchestrator
from app.services.clinical_snapshot import build_clinical_snapshot
from app.services.decision_override_service import (
    DecisionOverrideError,
    DecisionOverrideService,
)
from app.services.object_authorization import ObjectAuthorizationService
from app.services.patient_counseling_service import PatientCounselingService
from app.services.patient_history_service import PatientHistoryService

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])
DbSession = Annotated[Session, Depends(get_db)]
PrescriptionChecker = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM)),
]
SecondReviewer = Annotated[
    UserModel, Depends(require_roles(UserRole.MEDICO, UserRole.ENFERMAGEM))
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
    structured_dose = MedicationDoseInput(**payload.dose.model_dump()) if payload.dose else None
    prescription = PrescriptionInput(
        dose_mg=payload.dose_mg,
        frequency_per_day=payload.frequency_per_day,
        route=(
            payload.route
            or (structured_dose.route if structured_dose else None)
            or "não informada"
        ),
        duration_days=payload.duration_days,
        indication=payload.indication,
        professional_notes=payload.professional_notes,
        dose=structured_dose,
    )
    rag_evidence = ClinicalRAGService().retrieve_for_prescription(patient, medication, prescription)
    patient_knowledge_bundle = PatientHistoryService(db).knowledge_bundle(patient_record)
    functional_profile = (
        db.query(PatientFunctionalProfileModel)
        .filter(PatientFunctionalProfileModel.patient_id == patient_record.id)
        .first()
    )
    evaluation = ClinicalDecisionOrchestrator().evaluate(
        patient=patient,
        medication=medication,
        prescription=prescription,
        user=current_user,
        functional_profile=functional_profile,
        rag_evidence=rag_evidence,
        missing_context=list(patient_knowledge_bundle.get("missing_data") or []),
    )
    result = evaluation.legacy_result
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
    patient_counseling = PatientCounselingService(db).build_for_prescription(
        patient_record,
        medication_record,
        contextual_activity_answer=payload.contextual_activity_answer,
    )
    dose_intelligence = evaluation.dose_intelligence
    psychotropic_safety = evaluation.psychotropic_safety
    prescribing_policy = evaluation.prescribing_policy
    snapshot = build_clinical_snapshot(
        patient=patient,
        medication=medication,
        prescription=prescription,
        result=result,
        decision=evaluation.envelope,
        dose_intelligence=dose_intelligence,
        psychotropic_safety=psychotropic_safety,
        prescribing_policy=prescribing_policy,
        rag_evidence=rag_evidence,
        patient_knowledge_bundle=patient_knowledge_bundle,
    )
    audit_service = AuditService(db, auto_commit=False)
    try:
        audit = audit_service.record_check(
            patient,
            medication,
            prescription,
            result,
            current_user,
            clinical_snapshot=snapshot,
            clinical_decision=evaluation.envelope.to_dict(),
            dose_intelligence=dose_intelligence,
            psychotropic_safety=psychotropic_safety,
            prescribing_policy=prescribing_policy,
        )
        audit_service.record_action(
            user=current_user,
            action="prescription.clinical_intelligence_evaluated",
            resource_type="prescription",
            resource_id=str(audit.id),
            status=prescribing_policy["status"],
            risk_level=result.risk_level.value,
            details={
                "decision_status": evaluation.envelope.decision_status.value,
                "coverage_status": evaluation.envelope.coverage.status.value,
                "correlation_id": evaluation.envelope.correlation_id,
                "specialty": current_user.specialty_code,
                "policy_type": medication.policy_type,
                "policy_strength": medication.policy_strength,
                "dose_rule_id": f"medication:{medication.id}:dose",
                "psychotropic_signal_code": [item["code"] for item in psychotropic_safety],
                "prescriber_policy_status": prescribing_policy["status"],
                "credential_verification_status": current_user.credential_verification_status,
                "high_alert_category": medication.high_alert_category,
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    patient_data_considered = result.dose_summary.get("patient_data_considered", [])
    technical_details = {
        "dose_summary": result.dose_summary,
        "compatibility": result.compatibility,
        "rag_evidence": rag_evidence,
        "clinical_context_graph": result.clinical_context_graph,
        "patient_knowledge_bundle": patient_knowledge_bundle,
        "rules_fired": [alert.code for alert in result.alerts],
        "dose_intelligence": dose_intelligence,
        "psychotropic_safety": psychotropic_safety,
        "prescribing_policy": prescribing_policy,
    }
    clinical_view = {
        "decision_status": evaluation.envelope.decision_status.value,
        "coverage_status": evaluation.envelope.coverage.status.value,
        "status": evaluation.envelope.legacy_status.value,
        "risk_level": evaluation.envelope.highest_severity.value,
        "primary_recommendation": evaluation.envelope.recommendation,
        "patient_data_considered": patient_data_considered,
        "missing_data": patient_knowledge_bundle.get("missing_data", []),
        "relevant_alerts": [
            {
                "code": alert.code,
                "title": alert.title,
                "severity": alert.severity.value,
                "recommendation": alert.recommendation,
            }
            for alert in result.alerts
        ],
        "technical_details_available": True,
        "dose_intelligence": dose_intelligence,
        "psychotropic_safety": psychotropic_safety,
        "prescribing_policy": prescribing_policy,
    }

    return PrescriptionCheckResponse(
        decision=evaluation.envelope.to_dict(),
        coverage_status=evaluation.envelope.coverage.status.value,
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
        patient_knowledge_bundle=patient_knowledge_bundle,
        clinical_view=clinical_view,
        technical_details=technical_details,
        dose_intelligence=dose_intelligence,
        psychotropic_safety=psychotropic_safety,
        prescribing_policy=prescribing_policy,
    )


@router.post(
    "/{audit_id}/overrides",
    response_model=DecisionOverrideRead,
    status_code=status.HTTP_201_CREATED,
)
def request_decision_override(
    audit_id: int,
    payload: DecisionOverrideRequest,
    db: DbSession,
    current_user: SecondReviewer,
) -> DecisionOverrideRead:
    audit = db.get(PrescriptionAuditModel, audit_id)
    if audit is None or (
        audit.patient_id
        and not ObjectAuthorizationService(db).require_patient(current_user, audit.patient_id)
    ):
        raise HTTPException(status_code=404, detail="Decisão clínica não encontrada.")
    try:
        override = DecisionOverrideService(db).request(
            audit=audit, requester=current_user, reason=payload.reason
        )
        AuditService(db, auto_commit=False).record_action(
            user=current_user,
            action="decision_override.requested",
            resource_type="prescription",
            resource_id=str(audit.id),
            status=override.status,
            risk_level=audit.risk_level,
            details={"override_id": override.id},
        )
        db.commit()
        db.refresh(override)
        return override
    except DecisionOverrideError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/overrides/{override_id}/review", response_model=DecisionOverrideRead)
def review_decision_override(
    override_id: int,
    payload: DecisionOverrideReviewRequest,
    db: DbSession,
    current_user: SecondReviewer,
) -> DecisionOverrideRead:
    override = db.get(DecisionOverrideModel, override_id)
    audit = (
        db.get(PrescriptionAuditModel, override.prescription_audit_id)
        if override is not None
        else None
    )
    if audit is None or override is None or (
        audit.patient_id
        and not ObjectAuthorizationService(db).require_patient(current_user, audit.patient_id)
    ):
        raise HTTPException(status_code=404, detail="Solicitação de override não encontrada.")
    required_role = str(
        (audit.clinical_decision.get("override_policy") or {}).get(
            "second_reviewer_role"
        )
        or "medico"
    )
    try:
        reviewed = DecisionOverrideService(db).review(
            override=override,
            reviewer=current_user,
            decision=payload.decision,
            note=payload.note,
            required_role=required_role,
        )
        AuditService(db, auto_commit=False).record_action(
            user=current_user,
            action="decision_override.reviewed",
            resource_type="prescription",
            resource_id=str(audit.id),
            status=reviewed.status,
            risk_level=audit.risk_level,
            details={"override_id": reviewed.id, "review_decision": reviewed.review_decision},
        )
        db.commit()
        db.refresh(reviewed)
        return reviewed
    except DecisionOverrideError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/explain", response_model=PrescriptionExplainResponse)
def explain_prescription(
    payload: PrescriptionExplainByAuditRequest,
    db: DbSession,
    current_user: PrescriptionChecker,
) -> PrescriptionExplainResponse:
    audit = db.get(PrescriptionAuditModel, payload.audit_id)
    if audit is None or not audit.clinical_snapshot:
        raise HTTPException(status_code=404, detail="Decisão clínica não encontrada.")
    if audit.patient_id and not ObjectAuthorizationService(db).require_patient(
        current_user, audit.patient_id
    ):
        raise HTTPException(status_code=404, detail="Decisão clínica não encontrada.")
    explanation = AIExplainer(settings, db).explain_snapshot(
        audit.clinical_snapshot, requester_role=current_user.role
    )
    AuditService(db).record_action(
        user=current_user,
        action="prescription.explain",
        resource_type="prescription",
        resource_id=str(payload.audit_id),
        status=str(audit.clinical_decision.get("decision_status")),
        risk_level=audit.risk_level,
        details={
            "audit_id": payload.audit_id,
            "alerts_count": len(audit.alerts or []),
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
            detail="Checagem de prescrição não encontrada.",
        )
    patient_record = PatientRepository(db).get(audit.patient_id) if audit.patient_id else None
    medication_record = (
        MedicationRepository(db).get(audit.medication_id) if audit.medication_id else None
    )
    if patient_record is None or medication_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente ou medicamento da checagem não encontrado.",
        )
    return PatientCounselingService(db).build_for_prescription(
        patient_record,
        medication_record,
    )
