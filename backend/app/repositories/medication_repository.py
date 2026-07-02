from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import MedicationModel
from app.schemas.medication_schema import MedicationCreate, MedicationUpdate


class MedicationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[MedicationModel]:
        return list(self.db.scalars(select(MedicationModel).order_by(MedicationModel.brand_name)))

    def get(self, medication_id: int) -> MedicationModel | None:
        return self.db.get(MedicationModel, medication_id)

    def count(self) -> int:
        return self.db.scalar(select(func.count(MedicationModel.id))) or 0

    def create(self, data: MedicationCreate) -> MedicationModel:
        medication = MedicationModel(**data.model_dump())
        self.db.add(medication)
        self.db.commit()
        self.db.refresh(medication)
        return medication

    def update(self, medication: MedicationModel, data: MedicationUpdate) -> MedicationModel:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(medication, field, value)
        self.db.commit()
        self.db.refresh(medication)
        return medication
