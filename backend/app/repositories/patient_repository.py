from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import PatientAccessGrantModel, PatientModel
from app.schemas.patient_schema import PatientCreate, PatientUpdate
from app.services.clinical_profile import clinical_profile_badge, normalize_patient_payload
from app.services.normalizer import normalize_text
from app.services.object_authorization import ObjectAuthorizationService


class PatientRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[PatientModel]:
        statement = select(PatientModel)
        current_user = self.db.info.get("current_user")
        if current_user is not None:
            statement = statement.where(
                ObjectAuthorizationService(self.db).patient_scope(current_user)
            )
        return list(self.db.scalars(statement.order_by(PatientModel.name)))

    def get(self, patient_id: int) -> PatientModel | None:
        patient = self.db.get(PatientModel, patient_id)
        current_user = self.db.info.get("current_user")
        if (
            patient is not None
            and current_user is not None
            and not ObjectAuthorizationService(self.db).require_patient(current_user, patient_id)
        ):
            return None
        return patient

    def count(self) -> int:
        return self.db.scalar(select(func.count(PatientModel.id))) or 0

    def find_duplicate(self, data: PatientCreate) -> PatientModel | None:
        normalized_name = normalize_text(data.name)
        for patient in self.list():
            same_name = normalize_text(patient.name) == normalized_name
            same_birth = patient.birth_date and patient.birth_date == data.birth_date
            same_age = data.age is not None and patient.age == data.age
            if same_name and (same_birth or same_age):
                return patient
        return None

    def create(self, data: PatientCreate) -> PatientModel:
        values = normalize_patient_payload(data.model_dump())
        current_user = self.db.info.get("current_user")
        if current_user is not None:
            values["institution_id"] = current_user.institution_id
            values["created_by_user_id"] = current_user.id
        patient = PatientModel(**values)
        self.db.add(patient)
        self.db.flush()
        if current_user is not None:
            self.db.add(
                PatientAccessGrantModel(
                    patient_id=patient.id,
                    user_id=current_user.id,
                    permission="owner",
                    reason="patient_creator",
                )
            )
        self.db.commit()
        self.db.refresh(patient)
        self._attach_badge(patient)
        return patient

    def update(self, patient: PatientModel, data: PatientUpdate) -> PatientModel:
        values = normalize_patient_payload(data.model_dump(exclude_unset=True))
        for field, value in values.items():
            setattr(patient, field, value)
        self.db.commit()
        self.db.refresh(patient)
        self._attach_badge(patient)
        return patient

    def _attach_badge(self, patient: PatientModel) -> None:
        patient.clinical_profile_badge = clinical_profile_badge(
            patient.clinical_profile_completeness_score or 0
        )
