from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PatientBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    birth_date: date | None = None
    age: int | None = Field(default=None, ge=0, le=130)
    weight_kg: float = Field(gt=0, le=400)
    height_cm: float | None = Field(default=None, gt=0, le=260)
    allergies: list[str] = Field(default_factory=list)
    comorbidities: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    renal_condition: str | None = Field(default=None, max_length=120)
    hepatic_condition: str | None = Field(default=None, max_length=120)
    cardiac_condition: str | None = Field(default=None, max_length=120)
    gastrointestinal_history: str | None = Field(default=None, max_length=160)
    hypertension: bool = False
    diabetes: bool = False
    pregnancy_or_lactation: bool | None = None
    adverse_reactions: list[str] = Field(default_factory=list)
    clinical_notes: str | None = None

    @model_validator(mode="after")
    def ensure_age_or_birth_date(self) -> "PatientBase":
        if self.age is None and self.birth_date is None:
            raise ValueError("Informe idade ou data de nascimento.")
        return self


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    birth_date: date | None = None
    age: int | None = Field(default=None, ge=0, le=130)
    weight_kg: float | None = Field(default=None, gt=0, le=400)
    height_cm: float | None = Field(default=None, gt=0, le=260)
    allergies: list[str] | None = None
    comorbidities: list[str] | None = None
    current_medications: list[str] | None = None
    renal_condition: str | None = Field(default=None, max_length=120)
    hepatic_condition: str | None = Field(default=None, max_length=120)
    cardiac_condition: str | None = Field(default=None, max_length=120)
    gastrointestinal_history: str | None = Field(default=None, max_length=160)
    hypertension: bool | None = None
    diabetes: bool | None = None
    pregnancy_or_lactation: bool | None = None
    adverse_reactions: list[str] | None = None
    clinical_notes: str | None = None


class PatientRead(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clinical_profile_reviewed_at: datetime | None = None
    clinical_profile_completeness_score: float = 0
    clinical_profile_badge: str = "Perfil clínico incompleto"


class QuickTriageRequest(BaseModel):
    renal_condition: bool | None = None
    hepatic_condition: bool | None = None
    cardiac_condition: bool | None = None
    hypertension: bool | None = None
    diabetes: bool | None = None
    pregnancy_or_lactation: bool | None = None
    gastrointestinal_history: bool | None = None
    adverse_reactions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    clinical_notes: str | None = None
    condition_to_review: str | None = None
