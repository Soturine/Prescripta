from pydantic import BaseModel, ConfigDict, Field


class PrescriptionCheckRequest(BaseModel):
    patient_id: int = Field(gt=0)
    medication_id: int = Field(gt=0)
    dose_mg: float = Field(gt=0)
    frequency_per_day: int = Field(gt=0, le=24)
    route: str = Field(min_length=2, max_length=80)


class AlertRead(BaseModel):
    code: str
    title: str
    description: str
    severity: str
    recommendation: str


class PrescriptionCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    risk_level: str
    alerts: list[AlertRead]
    recommendation: str
    human_review_required: bool
    audit_id: int


class PrescriptionExplainPatient(BaseModel):
    id: int | None = Field(default=None, gt=0)
    name: str = Field(min_length=2, max_length=160)
    birth_date: str | None = None
    age: int | None = Field(default=None, ge=0, le=130)
    weight_kg: float = Field(gt=0, le=400)
    height_cm: float | None = Field(default=None, gt=0, le=260)
    allergies: list[str] = Field(default_factory=list)
    comorbidities: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)


class PrescriptionExplainMedication(BaseModel):
    id: int | None = Field(default=None, gt=0)
    brand_name: str = Field(min_length=2, max_length=160)
    active_ingredient: str = Field(min_length=2, max_length=160)
    therapeutic_class: str = Field(min_length=2, max_length=160)
    max_daily_dose_mg: float = Field(gt=0)
    allowed_routes: list[str] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)
    notes: str | None = None


class PrescriptionExplainRequest(BaseModel):
    patient: PrescriptionExplainPatient
    medication: PrescriptionExplainMedication
    dose_mg: float = Field(gt=0)
    frequency_per_day: int = Field(gt=0, le=24)
    route: str = Field(min_length=2, max_length=80)
    status: str = Field(min_length=2, max_length=40)
    risk_level: str = Field(min_length=2, max_length=40)
    alerts: list[AlertRead] = Field(default_factory=list)
    recommendation: str = Field(min_length=2)
    human_review_required: bool
    audit_id: int | None = Field(default=None, gt=0)
    user_profile: str = Field(min_length=2, max_length=80)


class PrescriptionExplainResponse(BaseModel):
    provider: str
    model: str | None
    used_fallback: bool
    simple_explanation: str
    technical_summary: str
    review_questions: list[str]
    educational_notice: str
    prescription_status: str
    risk_level: str
    critical_alert_codes: list[str]
