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
