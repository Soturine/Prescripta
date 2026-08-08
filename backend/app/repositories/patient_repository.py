from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import PatientAccessGrantModel, PatientModel
from app.schemas.patient_schema import PatientCreate, PatientUpdate, age_on_date
from app.services.clinical_profile import clinical_profile_badge, normalize_patient_payload
from app.services.normalizer import normalize_text
from app.services.object_authorization import ObjectAuthorizationService


class PatientRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        capability: str = "patient.read",
        purpose: str = "treatment",
    ) -> list[PatientModel]:
        statement = select(PatientModel)
        current_user = self.db.info.get("current_user")
        if current_user is not None:
            statement = statement.where(
                ObjectAuthorizationService(self.db).patient_scope(
                    current_user, capability=capability, purpose=purpose
                )
            )
        statement = statement.order_by(PatientModel.name).offset(offset).limit(limit)
        return list(self.db.scalars(statement))

    def get(
        self,
        patient_id: int,
        *,
        capability: str = "patient.read",
        purpose: str = "treatment",
    ) -> PatientModel | None:
        patient = self.db.get(PatientModel, patient_id)
        current_user = self.db.info.get("current_user")
        if (
            patient is not None
            and current_user is not None
            and not ObjectAuthorizationService(self.db).require_patient(
                current_user,
                patient_id,
                capability=capability,
                purpose=purpose,
            )
        ):
            return None
        return patient

    def count(
        self,
        *,
        capability: str = "patient.read",
        purpose: str = "treatment",
    ) -> int:
        statement = select(func.count(PatientModel.id))
        current_user = self.db.info.get("current_user")
        if current_user is not None:
            statement = statement.where(
                ObjectAuthorizationService(self.db).patient_scope(
                    current_user, capability=capability, purpose=purpose
                )
            )
        return self.db.scalar(statement) or 0

    def find_duplicate(self, data: PatientCreate) -> PatientModel | None:
        normalized_name = normalize_text(data.name)
        statement = select(PatientModel)
        current_user = self.db.info.get("current_user")
        if current_user is not None:
            statement = statement.where(
                ObjectAuthorizationService(self.db).patient_scope(current_user)
            )
        for patient in self.db.scalars(statement):
            same_name = normalize_text(patient.name) == normalized_name
            same_birth = patient.birth_date and patient.birth_date == data.birth_date
            same_age = data.age is not None and patient.age == data.age
            if same_name and (same_birth or same_age):
                return patient
        return None

    def create(self, data: PatientCreate) -> PatientModel:
        values = normalize_patient_payload(data.model_dump())
        if values.get("birth_date") is not None:
            values["age"] = None
        current_user = self.db.info.get("current_user")
        if current_user is not None:
            values["institution_id"] = current_user.institution_id
            values["created_by_user_id"] = current_user.id
        patient = PatientModel(**values)
        self.db.add(patient)
        self.db.flush()
        if current_user is not None:
            object_capabilities = {
                "patient.read",
                "patient.write",
                "prescription.check",
                "prescription.override",
                "report.read",
                "report.create",
                "patient_guidance.create",
                "reconciliation.review",
                "psychology.context.write",
                "patient.sensitive_psychology.read",
            }
            for capability in sorted(
                set(current_user.capabilities or []) & object_capabilities
            ):
                self.db.add(
                    PatientAccessGrantModel(
                        patient_id=patient.id,
                        user_id=current_user.id,
                        institution_id=current_user.institution_id,
                        permission=capability,
                        capability=capability,
                        purpose="treatment",
                        granted_by_user_id=current_user.id,
                        reason="patient_creator",
                    )
                )
        self.db.flush()
        self.db.refresh(patient)
        self._attach_badge(patient)
        return patient

    def update(self, patient: PatientModel, data: PatientUpdate) -> PatientModel:
        values = normalize_patient_payload(data.model_dump(exclude_unset=True))
        effective_birth_date = values.get("birth_date", patient.birth_date)
        supplied_age = values.get("age")
        if effective_birth_date is not None:
            if supplied_age is not None and supplied_age != age_on_date(effective_birth_date):
                raise ValueError(
                    "Idade divergente da data de nascimento na data clínica atual."
                )
            values["age"] = None
        for field, value in values.items():
            setattr(patient, field, value)
        self.db.flush()
        self.db.refresh(patient)
        self._attach_badge(patient)
        return patient

    def _attach_badge(self, patient: PatientModel) -> None:
        patient.clinical_profile_badge = clinical_profile_badge(
            patient.clinical_profile_completeness_score or 0
        )
