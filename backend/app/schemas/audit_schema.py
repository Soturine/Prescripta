from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.prescription_schema import AlertRead


class AuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int | None
    medication_id: int | None
    patient_name: str
    medication_name: str
    dose_mg: float
    frequency_per_day: int
    route: str
    status: str
    risk_level: str
    checked_at: datetime
    alerts: list[AlertRead]
