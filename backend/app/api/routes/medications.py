from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.repositories.medication_repository import MedicationRepository
from app.schemas.counseling_schema import (
    MedicationCounselingGenerateRequest,
    MedicationCounselingReviewRequest,
    MedicationCounselingSummaryRead,
)
from app.schemas.medication_knowledge_schema import (
    MedicationBulkImportRequest,
    MedicationKnowledgeCurationRead,
    MedicationKnowledgeLookupRequest,
    MedicationKnowledgeReviewRequest,
)
from app.schemas.medication_schema import MedicationCreate, MedicationRead, MedicationUpdate
from app.services.adverse_effect_taxonomy import taxonomy_snapshot
from app.services.audit_service import AuditService
from app.services.medication_counseling_service import MedicationCounselingService
from app.services.medication_knowledge_service import MedicationKnowledgeService

router = APIRouter(prefix="/medications", tags=["medications"])
DbSession = Annotated[Session, Depends(get_db)]
MedicationReader = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM)),
]
MedicationManager = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN))]
CounselingReader = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM, UserRole.AUDITOR)),
]
CounselingManager = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO)),
]


@router.get("", response_model=list[MedicationRead])
def list_medications(db: DbSession, _current_user: MedicationReader) -> list[MedicationRead]:
    return MedicationRepository(db).list()


@router.post("", response_model=MedicationRead, status_code=status.HTTP_201_CREATED)
def create_medication(
    payload: MedicationCreate,
    db: DbSession,
    current_user: MedicationManager,
) -> MedicationRead:
    medication = MedicationRepository(db).create(payload)
    AuditService(db).record_action(
        user=current_user,
        action="medication.create",
        resource_type="medication",
        resource_id=str(medication.id),
        details={"brand_name": medication.brand_name},
    )
    return medication


@router.get("/adverse-effect-taxonomy", response_model=list[dict])
def adverse_effect_taxonomy(_current_user: CounselingReader) -> list[dict]:
    return taxonomy_snapshot()


@router.post("/knowledge/lookup", response_model=MedicationKnowledgeCurationRead)
def medication_knowledge_lookup(
    payload: MedicationKnowledgeLookupRequest,
    db: DbSession,
    current_user: MedicationManager,
) -> MedicationKnowledgeCurationRead:
    return MedicationKnowledgeService(db).lookup(payload, user=current_user)


@router.post("/knowledge/bulk-import", response_model=list[MedicationKnowledgeCurationRead])
def medication_knowledge_bulk_import(
    payload: MedicationBulkImportRequest,
    db: DbSession,
    current_user: MedicationManager,
) -> list[MedicationKnowledgeCurationRead]:
    return MedicationKnowledgeService(db).bulk_import(payload, user=current_user)


@router.get("/knowledge/curation-queue", response_model=list[MedicationKnowledgeCurationRead])
def medication_knowledge_queue(
    db: DbSession,
    _current_user: MedicationReader,
    review_status: str | None = None,
) -> list[MedicationKnowledgeCurationRead]:
    return MedicationKnowledgeService(db).list_queue(review_status=review_status)


@router.post(
    "/knowledge/curation-queue/{item_id}/review",
    response_model=MedicationKnowledgeCurationRead,
)
def review_medication_knowledge(
    item_id: int,
    payload: MedicationKnowledgeReviewRequest,
    db: DbSession,
    current_user: MedicationManager,
) -> MedicationKnowledgeCurationRead:
    try:
        return MedicationKnowledgeService(db).review(item_id, payload, user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{medication_id}/counseling-summary",
    response_model=MedicationCounselingSummaryRead | None,
)
def get_counseling_summary(
    medication_id: int,
    db: DbSession,
    _current_user: CounselingReader,
) -> MedicationCounselingSummaryRead | None:
    medication = MedicationRepository(db).get(medication_id)
    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento não encontrado."
        )
    service = MedicationCounselingService(db)
    return service.read_model(service.get_best_for_medication(medication))


@router.post(
    "/{medication_id}/counseling-summary/generate",
    response_model=MedicationCounselingSummaryRead,
)
def generate_counseling_summary(
    medication_id: int,
    payload: MedicationCounselingGenerateRequest,
    db: DbSession,
    current_user: CounselingManager,
) -> MedicationCounselingSummaryRead:
    medication = MedicationRepository(db).get(medication_id)
    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento não encontrado."
        )
    summary = MedicationCounselingService(db).generate_for_medication(
        medication,
        source_text=payload.source_text,
        force_regenerate=payload.force_regenerate,
        provider_name=payload.provider_name,
    )
    AuditService(db).record_action(
        user=current_user,
        action="medication_counseling.generate",
        resource_type="medication",
        resource_id=str(medication.id),
        details={
            "summary_id": summary.id,
            "source_id": summary.source_id,
            "status": summary.validation_status,
            "generated_by": summary.generated_by,
            "provider": summary.provider_name,
            "requires_review": summary.requires_review,
        },
    )
    return MedicationCounselingSummaryRead.model_validate(summary)


@router.post(
    "/{medication_id}/counseling-summary/review",
    response_model=MedicationCounselingSummaryRead,
)
def review_counseling_summary(
    medication_id: int,
    payload: MedicationCounselingReviewRequest,
    db: DbSession,
    current_user: CounselingManager,
) -> MedicationCounselingSummaryRead:
    medication = MedicationRepository(db).get(medication_id)
    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento não encontrado."
        )
    service = MedicationCounselingService(db)
    summary = service.get_best_for_medication(medication)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resumo de orientação não encontrado.",
        )
    updated = service.review_summary(summary, payload)
    AuditService(db).record_action(
        user=current_user,
        action="medication_counseling.review",
        resource_type="medication",
        resource_id=str(medication.id),
        status=updated.validation_status,
        details={
            "summary_id": updated.id,
            "source_id": updated.source_id,
            "validation_status": updated.validation_status,
            "justification": payload.justification,
        },
    )
    return MedicationCounselingSummaryRead.model_validate(updated)


@router.get("/{medication_id}", response_model=MedicationRead)
def get_medication(
    medication_id: int,
    db: DbSession,
    _current_user: MedicationReader,
) -> MedicationRead:
    medication = MedicationRepository(db).get(medication_id)
    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento não encontrado."
        )
    return medication


@router.put("/{medication_id}", response_model=MedicationRead)
def update_medication(
    medication_id: int,
    payload: MedicationUpdate,
    db: DbSession,
    current_user: MedicationManager,
) -> MedicationRead:
    repository = MedicationRepository(db)
    medication = repository.get(medication_id)
    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento não encontrado."
        )
    updated = repository.update(medication, payload)
    AuditService(db).record_action(
        user=current_user,
        action="medication.update",
        resource_type="medication",
        resource_id=str(updated.id),
        details={"brand_name": updated.brand_name},
    )
    return updated
