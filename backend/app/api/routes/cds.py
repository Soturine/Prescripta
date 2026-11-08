from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import require_capabilities
from app.database.models import CDSIdempotencyModel, MedicationModel, UserModel
from app.database.session import get_db
from app.domain.dose import MedicationDoseInput
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.domain.user import Capability
from app.schemas.cds_schema import (
    CDSCard,
    CDSMedicationRequest,
    CDSObservationsEvaluation,
    CDSPrescriptionCheckRequest,
    CDSPrescriptionCheckResponse,
)
from app.schemas.prescription_schema import AlertRead
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256
from app.services.clinical_decision_orchestrator import (
    ClinicalDecisionEvaluation,
    ClinicalDecisionOrchestrator,
)
from app.services.normalizer import normalize_text

router = APIRouter(prefix="/cds", tags=["cds"])
DbSession = Annotated[Session, Depends(get_db)]
CDSChecker = Annotated[
    UserModel,
    Depends(require_capabilities(Capability.PRESCRIPTION_CHECK)),
]


@router.post("/prescription-check", response_model=CDSPrescriptionCheckResponse)
def cds_prescription_check(
    payload: CDSPrescriptionCheckRequest,
    db: DbSession,
    current_user: CDSChecker,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> CDSPrescriptionCheckResponse:
    if payload.persist:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "persistent_cds_import_not_supported",
                "message": "Use o fluxo de importação com consentimento e reconciliação.",
            },
        )

    request_hash = canonical_sha256(payload.model_dump(mode="json"))
    effective_key = (idempotency_key or f"auto-{request_hash}").strip()
    if not effective_key or len(effective_key) > 160:
        raise HTTPException(status_code=422, detail="Idempotency-Key inválida.")
    previous = _find_idempotent_response(db, current_user.id, effective_key)
    if previous is not None:
        return _replay_or_conflict(previous, request_hash)

    medication_record = _resolve_canonical_medication(db, payload.medication_request)
    patient, missing_context = _patient_from_payload(payload)
    medication = Medication.from_record(medication_record)
    prescription = _prescription_from_payload(payload.medication_request)
    evaluation = ClinicalDecisionOrchestrator(db).evaluate(
        patient=patient,
        medication=medication,
        prescription=prescription,
        user=current_user,
        missing_context=missing_context,
        rag_evidence=[],
    )
    observations_received = len(payload.observations)
    observations_evaluation = CDSObservationsEvaluation(
        status="not_evaluated" if observations_received else "none_received",
        received_count=observations_received,
        evaluated_count=0,
        reason=(
            "O motor demonstrativo não interpreta observações/exames; elas não influenciaram "
            "a decisão."
            if observations_received
            else None
        ),
    )
    # Auditoria e registro idempotente formam uma única unidade: se outra requisição concorrente
    # gravar a mesma chave primeiro, o savepoint desfaz ambos e a resposta vencedora é reproduzida
    # (ou 409, se o conteúdo divergir), em vez de 500 com auditoria órfã já confirmada.
    savepoint = db.begin_nested()
    try:
        response = _evaluate_audit_and_store(
            db,
            current_user=current_user,
            effective_key=effective_key,
            request_hash=request_hash,
            medication=medication,
            evaluation=evaluation,
            observations_evaluation=observations_evaluation,
        )
        savepoint.commit()
    except IntegrityError:
        savepoint.rollback()
        winner = _find_idempotent_response(db, current_user.id, effective_key)
        if winner is None:
            raise
        return _replay_or_conflict(winner, request_hash)
    return response


def _evaluate_audit_and_store(
    db: Session,
    *,
    current_user: UserModel,
    effective_key: str,
    request_hash: str,
    medication: Medication,
    evaluation: ClinicalDecisionEvaluation,
    observations_evaluation: CDSObservationsEvaluation,
) -> CDSPrescriptionCheckResponse:
    result = evaluation.legacy_result
    audit = AuditService(db, auto_commit=False).record_action(
        user=current_user,
        action="cds.prescription_check",
        resource_type="cds",
        resource_id=None,
        status=evaluation.envelope.decision_status.value,
        risk_level=evaluation.envelope.highest_severity.value,
        details={
            "request_hash": request_hash,
            "idempotency_key": effective_key,
            "medication_id": medication.id,
            "alerts_count": len(result.alerts),
            "observations_count": observations_evaluation.received_count,
            "observations_evaluated": observations_evaluation.evaluated_count,
            "clinical_data_persisted": False,
            "coverage_status": evaluation.envelope.coverage.status.value,
            "source": "external_cds_canonical_lookup",
        },
    )
    cards = [
        CDSCard(
            summary=alert.title,
            indicator=_indicator(alert.severity.value),
            detail=alert.description,
            source={
                "medication_id": medication.id,
                "jurisdiction": medication.source_jurisdiction,
                "type": medication.evidence_source_type,
                "validation_status": medication.validation_status,
            },
        )
        for alert in result.alerts
    ]
    if not evaluation.envelope.coverage.sufficient:
        cards.append(
            CDSCard(
                summary="Cobertura clínica insuficiente",
                indicator="warning",
                detail=evaluation.envelope.recommendation,
                source={
                    "coverage_status": evaluation.envelope.coverage.status.value,
                    "source_ids": evaluation.envelope.coverage.source_ids,
                },
            )
        )
    if observations_evaluation.status == "not_evaluated":
        cards.append(
            CDSCard(
                summary="Observações recebidas não foram avaliadas",
                indicator="warning",
                detail=(
                    "As observações enviadas não são interpretadas por este CDS demonstrativo. "
                    "Ausência de alerta relacionado a exames não indica segurança."
                ),
                source={
                    "observations_received": observations_evaluation.received_count,
                    "observations_evaluated": observations_evaluation.evaluated_count,
                },
            )
        )
    response = CDSPrescriptionCheckResponse(
        decision=evaluation.envelope.to_dict(),
        coverage_status=evaluation.envelope.coverage.status.value,
        status=result.status.value,
        risk_level=result.risk_level.value,
        alerts=[AlertRead(**alert.to_dict()) for alert in result.alerts],
        cards=cards,
        audit_id=f"cds-{audit.id}",
        idempotency_key=effective_key,
        educational_notice=(
            "CDS demonstrativo. Identidade e regras do medicamento são resolvidas no servidor; "
            "persist=false não salva dados clínicos do paciente."
        ),
        observations_evaluation=observations_evaluation,
    )
    db.add(
        CDSIdempotencyModel(
            user_id=current_user.id,
            idempotency_key=effective_key,
            request_hash=request_hash,
            response_payload=response.model_dump(mode="json"),
        )
    )
    db.flush()
    return response


def _find_idempotent_response(
    db: Session, user_id: int, idempotency_key: str
) -> CDSIdempotencyModel | None:
    return db.scalar(
        select(CDSIdempotencyModel).where(
            CDSIdempotencyModel.user_id == user_id,
            CDSIdempotencyModel.idempotency_key == idempotency_key,
        )
    )


def _replay_or_conflict(
    previous: CDSIdempotencyModel, request_hash: str
) -> CDSPrescriptionCheckResponse:
    if previous.request_hash != request_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "idempotency_key_reused",
                "message": "A chave já foi usada com outro conteúdo.",
            },
        )
    return CDSPrescriptionCheckResponse.model_validate(previous.response_payload)


def _resolve_canonical_medication(
    db: Session,
    request: CDSMedicationRequest,
) -> MedicationModel:
    if request.medication_id is not None:
        medication = db.get(MedicationModel, request.medication_id)
        if medication is None:
            raise _unknown_medication()
        ingredient_conflicts = request.active_ingredient and normalize_text(
            request.active_ingredient
        ) != normalize_text(medication.active_ingredient)
        if ingredient_conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "medication_identity_conflict",
                    "message": "O ID e o princípio ativo não resolvem para o mesmo cadastro.",
                },
            )
        return medication

    wanted = normalize_text(request.active_ingredient or "")
    candidates: list[MedicationModel] = []
    for medication in db.scalars(select(MedicationModel)):
        terms = {
            normalize_text(medication.active_ingredient),
            normalize_text(medication.brand_name),
            *(normalize_text(alias) for alias in medication.commercial_aliases or []),
        }
        if wanted in terms:
            candidates.append(medication)
    if not candidates:
        raise _unknown_medication()
    if len(candidates) > 1:
        # PRE-02: apresentações do mesmo princípio ativo podem ter concentração, forma, via e
        # limites de dose distintos. Nunca escolher uma arbitrariamente (antes: menor ID).
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ambiguous_medication",
                "message": (
                    "A terminologia resolve para mais de um cadastro; informe medication_id "
                    "da apresentação desejada."
                ),
                "candidates": [
                    {
                        "medication_id": item.id,
                        "brand_name": item.brand_name,
                        "active_ingredient": item.active_ingredient,
                        "concentration": item.concentration,
                        "pharmaceutical_form": item.pharmaceutical_form,
                    }
                    for item in sorted(candidates, key=lambda item: item.id)
                ],
            },
        )
    return candidates[0]


def _unknown_medication() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "code": "unknown_medication",
            "message": "Medicamento não resolvido no catálogo canônico do servidor.",
        },
    )


def _patient_from_payload(
    payload: CDSPrescriptionCheckRequest,
) -> tuple[Patient, list[str]]:
    data = payload.patient
    missing: list[str] = []
    for value, label in (
        (payload.allergies, "histórico de alergias"),
        (payload.conditions, "condições clínicas"),
        (payload.current_medications, "medicamentos atuais"),
    ):
        if value is None:
            missing.append(label)
    if data.hypertension is None:
        missing.append("status de hipertensão")
    if data.diabetes is None:
        missing.append("status de diabetes")
    return (
        Patient(
            id=None,
            name="Paciente CDS pseudonimizado",
            birth_date=None,
            age=data.age,
            weight_kg=data.weight_kg,
            height_cm=data.height_cm,
            sex_for_dosing_calculation=data.sex_for_dosing_calculation,
            allergies=list(payload.allergies or []),
            comorbidities=list(payload.conditions or []),
            current_medications=list(payload.current_medications or []),
            renal_condition=data.renal_condition,
            hepatic_condition=data.hepatic_condition,
            cardiac_condition=data.cardiac_condition,
            gastrointestinal_history=data.gastrointestinal_history,
            hypertension=bool(data.hypertension),
            diabetes=bool(data.diabetes),
            pregnancy_or_lactation=data.pregnancy_or_lactation,
            mental_health_factors=data.mental_health_factors or [],
            reproductive_gynecologic_factors=data.reproductive_gynecologic_factors or [],
            adverse_reactions=data.adverse_reactions or [],
            clinical_profile_completeness_score=0,
        ),
        missing,
    )


def _prescription_from_payload(payload: CDSMedicationRequest) -> PrescriptionInput:
    structured = MedicationDoseInput(**payload.dose.model_dump()) if payload.dose else None
    return PrescriptionInput(
        dose_mg=payload.dose_mg,
        frequency_per_day=payload.frequency_per_day,
        route=payload.route or (structured.route if structured else None) or "não informada",
        duration_days=payload.duration_days,
        indication=payload.indication,
        professional_notes=payload.professional_notes,
        dose=structured,
    )


def _indicator(risk_level: str) -> str:
    return {
        "critico": "critical",
        "alto": "warning",
        "moderado": "info",
        "baixo": "info",
    }.get(risk_level, "info")
