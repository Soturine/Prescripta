from pydantic import BaseModel, ConfigDict, Field


class MedicationBase(BaseModel):
    brand_name: str = Field(min_length=2, max_length=160)
    active_ingredient: str = Field(min_length=2, max_length=160)
    therapeutic_class: str = Field(min_length=2, max_length=160)
    max_daily_dose_mg: float = Field(gt=0)
    allowed_routes: list[str] = Field(default_factory=list, min_length=1)
    contraindications: list[str] = Field(default_factory=list)
    notes: str | None = None


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(BaseModel):
    brand_name: str | None = Field(default=None, min_length=2, max_length=160)
    active_ingredient: str | None = Field(default=None, min_length=2, max_length=160)
    therapeutic_class: str | None = Field(default=None, min_length=2, max_length=160)
    max_daily_dose_mg: float | None = Field(default=None, gt=0)
    allowed_routes: list[str] | None = None
    contraindications: list[str] | None = None
    notes: str | None = None


class MedicationRead(MedicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
