from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.medication_repository import MedicationRepository
from app.schemas.medication_schema import MedicationCreate, MedicationRead, MedicationUpdate

router = APIRouter(prefix="/medications", tags=["medications"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[MedicationRead])
def list_medications(db: DbSession) -> list[MedicationRead]:
    return MedicationRepository(db).list()


@router.post("", response_model=MedicationRead, status_code=status.HTTP_201_CREATED)
def create_medication(payload: MedicationCreate, db: DbSession) -> MedicationRead:
    return MedicationRepository(db).create(payload)


@router.get("/{medication_id}", response_model=MedicationRead)
def get_medication(medication_id: int, db: DbSession) -> MedicationRead:
    medication = MedicationRepository(db).get(medication_id)
    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento nao encontrado."
        )
    return medication


@router.put("/{medication_id}", response_model=MedicationRead)
def update_medication(
    medication_id: int, payload: MedicationUpdate, db: DbSession
) -> MedicationRead:
    repository = MedicationRepository(db)
    medication = repository.get(medication_id)
    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento nao encontrado."
        )
    return repository.update(medication, payload)
