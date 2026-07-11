from pydantic import BaseModel


class DashboardSummary(BaseModel):
    patient_count: int
    medication_count: int
    prescription_checks: int
    alerts_by_severity: dict[str, int]
    catalog_quality: dict[str, int]
