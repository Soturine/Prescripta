from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.domain.user import UserRole
from app.schemas.cds_schema import (
    CDSCard,
    CDSPrescriptionCheckRequest,
    CDSPrescriptionCheckResponse,
)
from app.schemas.prescription_schema import AlertRead
from app.services.audit_service import AuditService
from app.services.risk_engine import RiskEngine

router = APIRouter(prefix="/cds", tags=["cds"])
DbSession = Annotated[Session, Depends(get_db)]
CDSChecker = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM)),
]


@router.post("/prescription-check", response_model=CDSPrescriptionCheckResponse)
def cds_prescription_check(
    payload: CDSPrescriptionCheckRequest,
    db: DbSession,
    current_user: CDSChecker,
) -> CDSPrescriptionCheckResponse:
    patient = _patient_from_payload(payload)
    medication, prescription = _medication_and_prescription(payload.medication_request)
    result = RiskEngine().evaluate(patient, medication, prescription)
    audit = AuditService(db).record_action(
        user=current_user,
        action="cds.prescription_check",
        resource_type="cds",
        resource_id=None,
        status=result.status.value,
        risk_level=result.risk_level.value,
        details={
            "persist": payload.persist,
            "alerts_count": len(result.alerts),
            "observations_count": len(payload.observations),
            "clinical_data_persisted": False,
            "source": "external_cds_demo",
        },
    )
    return CDSPrescriptionCheckResponse(
        status=result.status.value,
        risk_level=result.risk_level.value,
        alerts=[AlertRead(**alert.to_dict()) for alert in result.alerts],
        cards=[
            CDSCard(
                summary=alert.title,
                indicator=_indicator(alert.severity.value),
                detail=alert.description,
                source={
                    "jurisdiction": medication.source_jurisdiction,
                    "type": medication.evidence_source_type,
                    "validation_status": medication.validation_status,
                },
            )
            for alert in result.alerts
        ],
        audit_id=f"demo-{audit.id}",
        educational_notice=(
            "CDS demonstrativo. Usa regras deterministicas, nao chama IA e nao salva dados "
            "clinicos permanentes quando persist=false."
        ),
    )


def _patient_from_payload(payload: CDSPrescriptionCheckRequest) -> Patient:
    patient_payload = payload.patient or {}
    return Patient(
        id=None,
        name=str(patient_payload.get("name") or "Paciente CDS"),
        birth_date=None,
        age=patient_payload.get("age"),
        weight_kg=float(patient_payload.get("weight_kg") or 70),
        height_cm=patient_payload.get("height_cm"),
        allergies=[*payload.allergies, *(patient_payload.get("allergies") or [])],
        comorbidities=[*payload.conditions, *(patient_payload.get("comorbidities") or [])],
        current_medications=[
            *payload.current_medications,
            *(patient_payload.get("current_medications") or []),
        ],
        renal_condition=patient_payload.get("renal_condition"),
        hepatic_condition=patient_payload.get("hepatic_condition"),
        cardiac_condition=patient_payload.get("cardiac_condition"),
        gastrointestinal_history=patient_payload.get("gastrointestinal_history"),
        hypertension=bool(patient_payload.get("hypertension", False)),
        diabetes=bool(patient_payload.get("diabetes", False)),
        pregnancy_or_lactation=patient_payload.get("pregnancy_or_lactation"),
        mental_health_factors=patient_payload.get("mental_health_factors") or [],
        reproductive_gynecologic_factors=patient_payload.get("reproductive_gynecologic_factors")
        or [],
        adverse_reactions=patient_payload.get("adverse_reactions") or [],
        clinical_profile_completeness_score=float(
            patient_payload.get("clinical_profile_completeness_score") or 0
        ),
    )


def _medication_and_prescription(payload: dict) -> tuple[Medication, PrescriptionInput]:
    active_ingredient = str(payload.get("active_ingredient") or payload.get("medication") or "")
    brand_name = str(payload.get("brand_name") or active_ingredient or "Medicamento CDS")
    route = str(payload.get("route") or "oral")
    medication = Medication(
        id=None,
        brand_name=brand_name,
        active_ingredient=active_ingredient or brand_name,
        therapeutic_class=str(payload.get("therapeutic_class") or "externo"),
        therapeutic_classes=payload.get("therapeutic_classes") or [],
        max_daily_dose_mg=float(payload.get("max_daily_dose_mg") or 999999),
        max_duration_days=payload.get("max_duration_days"),
        max_cumulative_dose_mg=payload.get("max_cumulative_dose_mg"),
        continuous_use=bool(payload.get("continuous_use", False)),
        monitoring_required=bool(payload.get("monitoring_required", False)),
        monitoring_notes=payload.get("monitoring_notes"),
        allowed_routes=payload.get("allowed_routes") or [route],
        contraindications=payload.get("contraindications") or [],
        renal_caution=bool(payload.get("renal_caution", False)),
        hepatic_caution=bool(payload.get("hepatic_caution", False)),
        cardiac_caution=bool(payload.get("cardiac_caution", False)),
        gastrointestinal_caution=bool(payload.get("gastrointestinal_caution", False)),
        metabolism_organs=payload.get("metabolism_organs") or [],
        elimination_organs=payload.get("elimination_organs") or [],
        renal_elimination_level=payload.get("renal_elimination_level") or "nao_informado",
        hepatic_metabolism_level=payload.get("hepatic_metabolism_level") or "nao_informado",
        neuropsychiatric_cautions=payload.get("neuropsychiatric_cautions") or [],
        reproductive_cautions=payload.get("reproductive_cautions") or [],
        source_jurisdiction=str(payload.get("source_jurisdiction") or "BR"),
        evidence_source_type=str(payload.get("evidence_source_type") or "external_demo"),
        validation_status=str(payload.get("validation_status") or "pending_review"),
    )
    prescription = PrescriptionInput(
        dose_mg=float(payload.get("dose_mg") or 1),
        frequency_per_day=int(payload.get("frequency_per_day") or 1),
        route=route,
        duration_days=payload.get("duration_days"),
        indication=payload.get("indication"),
        professional_notes=payload.get("professional_notes"),
    )
    return medication, prescription


def _indicator(risk_level: str) -> str:
    return {
        "critico": "critical",
        "alto": "warning",
        "moderado": "info",
        "baixo": "info",
    }.get(risk_level, "info")
