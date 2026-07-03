from pydantic import BaseModel, ConfigDict, Field


class PrescriptionCheckRequest(BaseModel):
    patient_id: int = Field(gt=0)
    medication_id: int = Field(gt=0)
    dose_mg: float = Field(gt=0)
    frequency_per_day: int = Field(gt=0, le=24)
    route: str = Field(min_length=2, max_length=80)
    duration_days: int | None = Field(default=None, gt=0, le=365)
    indication: str | None = Field(default=None, max_length=180)
    professional_notes: str | None = None


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
    dose_summary: dict
    compatibility: dict
    patient_factors_considered: list[str]
    medication_factors_considered: list[str]
    rag_evidence: list[dict] = Field(default_factory=list)
    clinical_context_graph: dict
    alternatives: list[dict] = Field(default_factory=list)


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
    renal_condition: str | None = None
    hepatic_condition: str | None = None
    cardiac_condition: str | None = None
    gastrointestinal_history: str | None = None
    hypertension: bool = False
    diabetes: bool = False
    pregnancy_or_lactation: bool | None = None
    adverse_reactions: list[str] = Field(default_factory=list)
    clinical_notes: str | None = None
    clinical_profile_completeness_score: float = 0


class PrescriptionExplainMedication(BaseModel):
    id: int | None = Field(default=None, gt=0)
    active_ingredient_id: int | None = Field(default=None, gt=0)
    brand_name: str = Field(min_length=2, max_length=160)
    active_ingredient: str = Field(min_length=2, max_length=160)
    commercial_aliases: list[str] = Field(default_factory=list)
    therapeutic_class: str = Field(min_length=2, max_length=160)
    therapeutic_classes: list[str] = Field(default_factory=list)
    source_jurisdiction: str = "BR"
    evidence_source_type: str = "demo_seed"
    validation_status: str = "demo"
    concentration: str | None = None
    pharmaceutical_form: str | None = None
    evidence_source_url: str | None = None
    max_daily_dose_mg: float = Field(gt=0)
    max_duration_days: int | None = None
    max_cumulative_dose_mg: float | None = None
    condition_specific_limits: dict[str, float] = Field(default_factory=dict)
    allowed_routes: list[str] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)
    renal_caution: bool = False
    hepatic_caution: bool = False
    cardiac_caution: bool = False
    gastrointestinal_caution: bool = False
    elderly_caution: bool = False
    metabolism_organs: list[str] = Field(default_factory=list)
    elimination_organs: list[str] = Field(default_factory=list)
    organs_involved: list[str] = Field(default_factory=list)
    relevant_adverse_effects: list[str] = Field(default_factory=list)
    structured_contraindications: list[str] = Field(default_factory=list)
    therapeutic_action: str | None = None
    alternative_group: str | None = None
    related_medications: list[str] = Field(default_factory=list)
    knowledge_source: str | None = None
    notes: str | None = None


class PrescriptionExplainRequest(BaseModel):
    patient: PrescriptionExplainPatient
    medication: PrescriptionExplainMedication
    dose_mg: float = Field(gt=0)
    frequency_per_day: int = Field(gt=0, le=24)
    route: str = Field(min_length=2, max_length=80)
    duration_days: int | None = Field(default=None, gt=0, le=365)
    indication: str | None = None
    professional_notes: str | None = None
    status: str = Field(min_length=2, max_length=40)
    risk_level: str = Field(min_length=2, max_length=40)
    alerts: list[AlertRead] = Field(default_factory=list)
    recommendation: str = Field(min_length=2)
    human_review_required: bool
    audit_id: int | None = Field(default=None, gt=0)
    user_profile: str = Field(min_length=2, max_length=80)
    dose_summary: dict = Field(default_factory=dict)
    compatibility: dict = Field(default_factory=dict)
    patient_factors_considered: list[str] = Field(default_factory=list)
    medication_factors_considered: list[str] = Field(default_factory=list)
    rag_evidence: list[dict] = Field(default_factory=list)
    clinical_context_graph: dict = Field(default_factory=dict)
    alternatives: list[dict] = Field(default_factory=list)


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
    missing_patient_data: list[str] = Field(default_factory=list)
    rag_sources: list[str] = Field(default_factory=list)
