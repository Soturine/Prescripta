from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import PatientModel
from app.schemas.patient_schema import PatientCreate, PatientUpdate


class PatientRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[PatientModel]:
        return list(self.db.scalars(select(PatientModel).order_by(PatientModel.name)))

    def get(self, patient_id: int) -> PatientModel | None:
        return self.db.get(PatientModel, patient_id)

    def count(self) -> int:
        return self.db.scalar(select(func.count(PatientModel.id))) or 0

    def create(self, data: PatientCreate) -> PatientModel:
        patient = PatientModel(**data.model_dump())
        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def update(self, patient: PatientModel, data: PatientUpdate) -> PatientModel:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(patient, field, value)
        self.db.commit()
        self.db.refresh(patient)
        return patient
