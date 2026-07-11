from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import (
    PatientClinicalDocumentModel,
    PatientDocumentExtractionModel,
    UserModel,
)
from app.database.session import get_db
from app.domain.user import UserRole
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_history_schema import (
    PatientClinicalDocumentCreate,
    PatientClinicalDocumentRead,
    PatientDocumentExtractionRead,
    PatientDocumentReviewRequest,
    PatientKnowledgeBundleRead,
)
from app.schemas.patient_schema import (
    PatientCreate,
    PatientFunctionalProfileRead,
    PatientFunctionalProfileUpdate,
    PatientIdentifierCreate,
    PatientIdentifierRead,
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
from app.services.controlled_vocabulary import label_for_code
from app.services.normalizer import merge_terms
from app.services.patient_functional_profile import PatientFunctionalProfileService
from app.services.patient_history_service import PatientHistoryService
from app.services.patient_identifier_service import PatientIdentifierService

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
        _attach_patient_metadata(db, patient)
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
    _attach_patient_metadata(db, patient)
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
    _attach_patient_metadata(db, patient)
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
    _attach_patient_metadata(db, updated)
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
        "renal_condition": _triage_value(
            payload.renal_condition,
            patient.renal_condition,
            "funcao_renal_a_revisar",
        ),
        "hepatic_condition": _triage_value(
            payload.hepatic_condition,
            patient.hepatic_condition,
            "funcao_hepatica_a_revisar",
        ),
        "cardiac_condition": _triage_value(
            payload.cardiac_condition,
            patient.cardiac_condition,
            "risco_cardiovascular_a_revisar",
        ),
        "gastrointestinal_history": _triage_value(
            payload.gastrointestinal_history,
            patient.gastrointestinal_history,
            "historico_gastrointestinal_a_revisar",
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
        "mental_health_factors": merge_terms(
            patient.mental_health_factors,
            payload.mental_health_factors,
        ),
        "reproductive_gynecologic_factors": merge_terms(
            patient.reproductive_gynecologic_factors,
            payload.reproductive_gynecologic_factors,
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
    _attach_patient_metadata(db, patient)
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


@router.get("/{patient_id}/identifiers", response_model=list[PatientIdentifierRead])
def list_patient_identifiers(
    patient_id: int,
    db: DbSession,
    _current_user: PatientReader,
) -> list[PatientIdentifierRead]:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado."
        )
    return PatientIdentifierService(db).list_for_patient(patient_id)


@router.get("/{patient_id}/functional-profile", response_model=PatientFunctionalProfileRead)
def get_functional_profile(
    patient_id: int,
    db: DbSession,
    _current_user: PatientReader,
) -> PatientFunctionalProfileRead:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado."
        )
    return PatientFunctionalProfileService(db).read_for_patient(patient_id)


@router.put("/{patient_id}/functional-profile", response_model=PatientFunctionalProfileRead)
def update_functional_profile(
    patient_id: int,
    payload: PatientFunctionalProfileUpdate,
    db: DbSession,
    current_user: PatientManager,
) -> PatientFunctionalProfileRead:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado."
        )
    service = PatientFunctionalProfileService(db)
    profile = service.upsert(patient_id, payload)
    read_profile = service._to_read(profile)
    AuditService(db).record_action(
        user=current_user,
        action="patient.functional_profile.update",
        resource_type="patient",
        resource_id=str(patient_id),
        details={
            "patient_name": patient.name,
            "unknown_fields": read_profile.unknown_fields,
            "source": read_profile.source,
        },
    )
    return read_profile


@router.get(
    "/{patient_id}/documents",
    response_model=list[PatientClinicalDocumentRead],
)
def list_patient_documents(
    patient_id: int,
    db: DbSession,
    _current_user: PatientReader,
) -> list[PatientClinicalDocumentRead]:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
        )
    return PatientHistoryService(db).list_documents(patient_id)


@router.post(
    "/{patient_id}/documents",
    response_model=PatientClinicalDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_patient_document(
    patient_id: int,
    payload: PatientClinicalDocumentCreate,
    db: DbSession,
    current_user: PatientManager,
) -> PatientClinicalDocumentRead:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
        )
    return PatientHistoryService(db).create_document(patient, payload, current_user)


@router.post(
    "/{patient_id}/documents/{document_id}/extract",
    response_model=PatientDocumentExtractionRead,
)
def extract_patient_document(
    patient_id: int,
    document_id: int,
    db: DbSession,
    current_user: PatientManager,
) -> PatientDocumentExtractionRead:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
        )
    document = db.get(PatientClinicalDocumentModel, document_id)
    if document is None or document.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento clinico nao encontrado.",
        )
    return PatientHistoryService(db).extract_document(patient, document, current_user)


@router.post(
    "/{patient_id}/document-extractions/{extraction_id}/review",
    response_model=PatientDocumentExtractionRead,
)
def review_patient_document_extraction(
    patient_id: int,
    extraction_id: int,
    payload: PatientDocumentReviewRequest,
    db: DbSession,
    current_user: PatientManager,
) -> PatientDocumentExtractionRead:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
        )
    extraction = db.get(PatientDocumentExtractionModel, extraction_id)
    if extraction is None or extraction.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extracao clinica nao encontrada.",
        )
    return PatientHistoryService(db).review_extraction(
        patient,
        extraction,
        decision=payload.decision,
        accepted_entities=payload.accepted_entities,
        user=current_user,
        justification=payload.justification,
    )


@router.get(
    "/{patient_id}/timeline",
    response_model=list[dict],
)
def patient_timeline(
    patient_id: int,
    db: DbSession,
    _current_user: PatientReader,
) -> list[dict]:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
        )
    return PatientHistoryService(db).timeline(patient_id)


@router.get(
    "/{patient_id}/knowledge-bundle",
    response_model=PatientKnowledgeBundleRead,
)
def patient_knowledge_bundle(
    patient_id: int,
    db: DbSession,
    _current_user: PatientReader,
) -> PatientKnowledgeBundleRead:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
        )
    return PatientHistoryService(db).knowledge_bundle(patient)


@router.post(
    "/{patient_id}/identifiers",
    response_model=PatientIdentifierRead,
    status_code=status.HTTP_201_CREATED,
)
def create_patient_identifier(
    patient_id: int,
    payload: PatientIdentifierCreate,
    db: DbSession,
    current_user: PatientManager,
) -> PatientIdentifierRead:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado."
        )
    try:
        identifier = PatientIdentifierService(db).create(
            patient_id=patient_id,
            identifier_type=payload.identifier_type,
            identifier_value=payload.identifier_value,
            issuing_system=payload.issuing_system,
            is_primary=payload.is_primary,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    AuditService(db).record_action(
        user=current_user,
        action="patient.identifier.create",
        resource_type="patient",
        resource_id=str(patient_id),
        details={
            "identifier_type": identifier.identifier_type,
            "issuing_system": identifier.issuing_system,
            "display_masked": identifier.display_masked,
        },
    )
    return identifier


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
            label_for_code(patient.renal_condition),
            label_for_code(patient.hepatic_condition),
            label_for_code(patient.cardiac_condition),
            label_for_code(patient.gastrointestinal_history),
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


def _triage_value(
    incoming: bool | str | None,
    existing: str | None,
    default_code: str,
) -> str | None:
    if isinstance(incoming, str):
        return incoming or existing
    if incoming:
        return default_code
    return existing


def _attach_patient_metadata(db: Session, patient) -> None:
    patient.clinical_profile_badge = clinical_profile_badge(
        patient.clinical_profile_completeness_score or 0
    )
    patient.identifiers = PatientIdentifierService(db).list_for_patient(patient.id)
    patient.possible_duplicate_matches = []
