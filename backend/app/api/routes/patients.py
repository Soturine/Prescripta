from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_schema import PatientCreate, PatientRead, PatientUpdate
from app.services.audit_service import AuditService

router = APIRouter(prefix="/patients", tags=["patients"])
DbSession = Annotated[Session, Depends(get_db)]
PatientReader = Annotated[
    UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM))
]
PatientManager = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO))]


@router.get("", response_model=list[PatientRead])
def list_patients(db: DbSession, _current_user: PatientReader) -> list[PatientRead]:
    return PatientRepository(db).list()


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    db: DbSession,
    current_user: PatientManager,
) -> PatientRead:
    patient = PatientRepository(db).create(payload)
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
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
