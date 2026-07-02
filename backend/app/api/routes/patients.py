from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_schema import PatientCreate, PatientRead, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[PatientRead])
def list_patients(db: DbSession) -> list[PatientRead]:
    return PatientRepository(db).list()


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: DbSession) -> PatientRead:
    return PatientRepository(db).create(payload)


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: int, db: DbSession) -> PatientRead:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
        )
    return patient


@router.put("/{patient_id}", response_model=PatientRead)
def update_patient(patient_id: int, payload: PatientUpdate, db: DbSession) -> PatientRead:
    repository = PatientRepository(db)
    patient = repository.get(patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
        )
    return repository.update(patient, payload)
