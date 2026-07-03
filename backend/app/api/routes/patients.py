from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_schema import (
    PatientCreate,
    PatientRead,
    PatientUpdate,
    QuickTriageRequest,
)
from app.services.audit_service import AuditService
from app.services.clinical_profile import (
    clinical_profile_badge,
    normalize_patient_payload,
    reviewed_now,
)
from app.services.normalizer import merge_terms

router = APIRouter(prefix="/patients", tags=["patients"])
DbSession = Annotated[Session, Depends(get_db)]
PatientReader = Annotated[
    UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM))
]
PatientManager = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO))]


@router.get("", response_model=list[PatientRead])
def list_patients(db: DbSession, _current_user: PatientReader) -> list[PatientRead]:
    patients = PatientRepository(db).list()
    for patient in patients:
        patient.clinical_profile_badge = clinical_profile_badge(
            patient.clinical_profile_completeness_score or 0
        )
    return patients


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    db: DbSession,
    current_user: PatientManager,
) -> PatientRead:
    repository = PatientRepository(db)
    duplicate = repository.find_duplicate(payload)
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Paciente possivelmente duplicado. Revise o cadastro existente.",
        )
    patient = repository.create(payload)
    AuditService(db).record_action(
        user=current_user,
        action="patient.create",
        resource_type="patient",
        resource_id=str(patient.id),
        details={"name": patient.name},
    )
    return patient


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: int, db: DbSession, _current_user: PatientReader) -> PatientRead:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado."
        )
    patient.clinical_profile_badge = clinical_profile_badge(
        patient.clinical_profile_completeness_score or 0
    )
    return patient


@router.put("/{patient_id}", response_model=PatientRead)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: DbSession,
    current_user: PatientManager,
) -> PatientRead:
    repository = PatientRepository(db)
    patient = repository.get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado."
        )
    updated = repository.update(patient, payload)
    AuditService(db).record_action(
        user=current_user,
        action="patient.update",
        resource_type="patient",
        resource_id=str(updated.id),
        details={"name": updated.name},
    )
    return updated


@router.patch("/{patient_id}/quick-triage", response_model=PatientRead)
def quick_triage_patient(
    patient_id: int,
    payload: QuickTriageRequest,
    db: DbSession,
    current_user: PatientManager,
) -> PatientRead:
    repository = PatientRepository(db)
    patient = repository.get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado."
        )

    before = {
        "renal_condition": patient.renal_condition,
        "hepatic_condition": patient.hepatic_condition,
        "cardiac_condition": patient.cardiac_condition,
        "gastrointestinal_history": patient.gastrointestinal_history,
        "allergies": list(patient.allergies or []),
        "current_medications": list(patient.current_medications or []),
        "adverse_reactions": list(patient.adverse_reactions or []),
    }
    conflicts: list[str] = []

    values = {
        "renal_condition": "renal" if payload.renal_condition else patient.renal_condition,
        "hepatic_condition": "hepatico" if payload.hepatic_condition else patient.hepatic_condition,
        "cardiac_condition": "cardiaco" if payload.cardiac_condition else patient.cardiac_condition,
        "gastrointestinal_history": (
            "gastrointestinal"
            if payload.gastrointestinal_history
            else patient.gastrointestinal_history
        ),
        "hypertension": (
            patient.hypertension if payload.hypertension is None else payload.hypertension
        ),
        "diabetes": patient.diabetes if payload.diabetes is None else payload.diabetes,
        "pregnancy_or_lactation": (
            patient.pregnancy_or_lactation
            if payload.pregnancy_or_lactation is None
            else payload.pregnancy_or_lactation
        ),
        "allergies": merge_terms(patient.allergies, payload.allergies),
        "current_medications": merge_terms(
            patient.current_medications,
            payload.current_medications,
        ),
        "adverse_reactions": merge_terms(patient.adverse_reactions, payload.adverse_reactions),
        "clinical_notes": payload.clinical_notes or patient.clinical_notes,
        "clinical_profile_reviewed_at": reviewed_now(),
    }
    if payload.condition_to_review:
        values["comorbidities"] = merge_terms(patient.comorbidities, [payload.condition_to_review])

    for field in ("renal_condition", "hepatic_condition", "cardiac_condition"):
        if before[field] and values[field] and before[field] != values[field]:
            conflicts.append(field)

    normalized = normalize_patient_payload(values)
    for field, value in normalized.items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    patient.clinical_profile_badge = clinical_profile_badge(
        patient.clinical_profile_completeness_score or 0
    )
    AuditService(db).record_action(
        user=current_user,
        action="patient.quick_triage",
        resource_type="patient",
        resource_id=str(patient.id),
        details={
            "patient_name": patient.name,
            "before": before,
            "after_score": patient.clinical_profile_completeness_score,
            "conflicts": conflicts,
        },
    )
    return patient


@router.get("/{patient_id}/clinical-context", response_model=dict)
def patient_clinical_context(
    patient_id: int,
    db: DbSession,
    _current_user: PatientReader,
) -> dict:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado."
        )
    factors = [
        factor
        for factor in [
            patient.renal_condition,
            patient.hepatic_condition,
            patient.cardiac_condition,
            patient.gastrointestinal_history,
            "hipertensão" if patient.hypertension else None,
            "diabetes" if patient.diabetes else None,
            *(patient.allergies or []),
            *(patient.adverse_reactions or []),
            *(patient.current_medications or []),
        ]
        if factor
    ]
    return {
        "patient_id": patient.id,
        "patient_name": patient.name,
        "nodes": [
            {"id": "patient", "label": patient.name, "type": "Paciente"},
            *[
                {"id": f"factor-{index}", "label": factor, "type": "Fator clínico"}
                for index, factor in enumerate(factors)
            ],
        ],
        "edges": [
            {"from": "patient", "to": f"factor-{index}", "label": "possui histórico"}
            for index, _factor in enumerate(factors)
        ],
        "clinical_profile_completeness_score": patient.clinical_profile_completeness_score or 0,
        "educational_notice": "Mapa lógico demonstrativo; não é grafo clínico validado.",
    }
