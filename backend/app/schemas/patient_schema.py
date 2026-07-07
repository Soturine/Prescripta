from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PatientBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    birth_date: date | None = None
    age: int | None = Field(default=None, ge=0, le=130)
    weight_kg: float = Field(gt=0, le=400)
    height_cm: float | None = Field(default=None, gt=0, le=260)
    phone: str | None = Field(default=None, max_length=80)
    email: str | None = Field(default=None, max_length=220)
    mother_name: str | None = Field(default=None, max_length=160)
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
    mental_health_factors: list[str] = Field(default_factory=list)
    reproductive_gynecologic_factors: list[str] = Field(default_factory=list)
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
    phone: str | None = Field(default=None, max_length=80)
    email: str | None = Field(default=None, max_length=220)
    mother_name: str | None = Field(default=None, max_length=160)
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
    mental_health_factors: list[str] | None = None
    reproductive_gynecologic_factors: list[str] | None = None
    adverse_reactions: list[str] | None = None
    clinical_notes: str | None = None


class PatientIdentifierCreate(BaseModel):
    identifier_type: str = Field(min_length=2, max_length=80)
    identifier_value: str = Field(min_length=2, max_length=160)
    issuing_system: str | None = Field(default=None, max_length=160)
    is_primary: bool = False


class PatientIdentifierRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    identifier_type: str
    issuing_system: str | None = None
    display_masked: str
    is_primary: bool


class PatientRead(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clinical_profile_reviewed_at: datetime | None = None
    clinical_profile_completeness_score: float = 0
    clinical_profile_badge: str = "Perfil clínico incompleto"


    identifiers: list[PatientIdentifierRead] = Field(default_factory=list)
    possible_duplicate_matches: list[dict] = Field(default_factory=list)


class QuickTriageRequest(BaseModel):
    renal_condition: bool | str | None = None
    hepatic_condition: bool | str | None = None
    cardiac_condition: bool | str | None = None
    hypertension: bool | None = None
    diabetes: bool | None = None
    pregnancy_or_lactation: bool | None = None
    mental_health_factors: list[str] = Field(default_factory=list)
    reproductive_gynecologic_factors: list[str] = Field(default_factory=list)
    gastrointestinal_history: bool | str | None = None
    adverse_reactions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    clinical_notes: str | None = None
    condition_to_review: str | None = None


class PatientFunctionalProfileBase(BaseModel):
    drives_regularly: bool | None = None
    professional_driver: bool | None = None
    operates_machinery: bool | None = None
    works_at_height: bool | None = None
    fall_risk_activity: bool | None = None
    night_shift: bool | None = None
    caregiver_responsibility: bool | None = None
    high_attention_activity: bool | None = None
    frequent_alcohol_use: bool | None = None
    history_of_falls: bool | None = None
    low_tolerance_to_sedation_or_dizziness: bool | None = None
    source: str = Field(default="manual", max_length=80)
    notes: str | None = None


class PatientFunctionalProfileUpdate(PatientFunctionalProfileBase):
    last_reviewed_at: datetime | None = None


class PatientFunctionalProfileRead(PatientFunctionalProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    patient_id: int
    last_reviewed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    unknown_fields: list[str] = Field(default_factory=list)
    educational_notice: str = (
        "Perfil funcional demonstrativo; dados desconhecidos geram alerta geral, nao bloqueio."
    )
