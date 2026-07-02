from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.repositories.medication_repository import MedicationRepository
from app.schemas.medication_schema import MedicationCreate, MedicationRead, MedicationUpdate
from app.services.audit_service import AuditService

router = APIRouter(prefix="/medications", tags=["medications"])
DbSession = Annotated[Session, Depends(get_db)]
MedicationReader = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM)),
]
MedicationManager = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN))]


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


@router.get("/{medication_id}", response_model=MedicationRead)
def get_medication(
    medication_id: int,
    db: DbSession,
    _current_user: MedicationReader,
) -> MedicationRead:
    medication = MedicationRepository(db).get(medication_id)
    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento nao encontrado."
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento nao encontrado."
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
