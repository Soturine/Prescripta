from collections.abc import Iterator

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import MedicationModel
from app.schemas.medication_schema import MedicationCreate, MedicationUpdate
from app.services.medication_metadata import normalize_medication_payload


class MedicationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, *, offset: int = 0, limit: int = 50) -> list[MedicationModel]:
        statement = (
            select(MedicationModel)
            .order_by(MedicationModel.brand_name)
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement))

    def iter_all(self) -> Iterator[MedicationModel]:
        """Percorre o catálogo inteiro em lotes; para varreduras que não podem ser paginadas."""
        statement = select(MedicationModel).order_by(MedicationModel.brand_name)
        yield from self.db.scalars(statement.execution_options(yield_per=200))

    def get(self, medication_id: int) -> MedicationModel | None:
        return self.db.get(MedicationModel, medication_id)

    def count(self) -> int:
        return self.db.scalar(select(func.count(MedicationModel.id))) or 0

    def create(self, data: MedicationCreate) -> MedicationModel:
        medication = MedicationModel(**normalize_medication_payload(data.model_dump()))
        self.db.add(medication)
        self.db.flush()
        self.db.refresh(medication)
        return medication

    def update(self, medication: MedicationModel, data: MedicationUpdate) -> MedicationModel:
        values = normalize_medication_payload(data.model_dump(exclude_unset=True))
        for field, value in values.items():
            setattr(medication, field, value)
        self.db.flush()
        self.db.refresh(medication)
        return medication
