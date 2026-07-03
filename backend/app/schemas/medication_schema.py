from pydantic import BaseModel, ConfigDict, Field


class MedicationBase(BaseModel):
    brand_name: str = Field(min_length=2, max_length=160)
    active_ingredient: str = Field(min_length=2, max_length=160)
    therapeutic_class: str = Field(min_length=2, max_length=160)
    max_daily_dose_mg: float = Field(gt=0)
    max_duration_days: int | None = Field(default=None, gt=0, le=365)
    max_cumulative_dose_mg: float | None = Field(default=None, gt=0)
    condition_specific_limits: dict[str, float] = Field(default_factory=dict)
    allowed_routes: list[str] = Field(default_factory=list, min_length=1)
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
    therapeutic_action: str | None = Field(default=None, max_length=180)
    alternative_group: str | None = Field(default=None, max_length=120)
    related_medications: list[str] = Field(default_factory=list)
    knowledge_source: str | None = Field(default=None, max_length=220)
    notes: str | None = None


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(BaseModel):
    brand_name: str | None = Field(default=None, min_length=2, max_length=160)
    active_ingredient: str | None = Field(default=None, min_length=2, max_length=160)
    therapeutic_class: str | None = Field(default=None, min_length=2, max_length=160)
    max_daily_dose_mg: float | None = Field(default=None, gt=0)
    max_duration_days: int | None = Field(default=None, gt=0, le=365)
    max_cumulative_dose_mg: float | None = Field(default=None, gt=0)
    condition_specific_limits: dict[str, float] | None = None
    allowed_routes: list[str] | None = None
    contraindications: list[str] | None = None
    renal_caution: bool | None = None
    hepatic_caution: bool | None = None
    cardiac_caution: bool | None = None
    gastrointestinal_caution: bool | None = None
    elderly_caution: bool | None = None
    metabolism_organs: list[str] | None = None
    elimination_organs: list[str] | None = None
    organs_involved: list[str] | None = None
    relevant_adverse_effects: list[str] | None = None
    structured_contraindications: list[str] | None = None
    therapeutic_action: str | None = Field(default=None, max_length=180)
    alternative_group: str | None = Field(default=None, max_length=120)
    related_medications: list[str] | None = None
    knowledge_source: str | None = Field(default=None, max_length=220)
    notes: str | None = None


class MedicationRead(MedicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
