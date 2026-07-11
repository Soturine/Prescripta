from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.prescription_schema import AlertRead


class CDSPrescriptionCheckRequest(BaseModel):
    patient: dict = Field(default_factory=dict)
    medication_request: dict = Field(default_factory=dict)
    allergies: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    observations: list[dict] = Field(default_factory=list)
    persist: bool = False


class CDSCard(BaseModel):
    summary: str
    indicator: str
    detail: str
    source: dict = Field(default_factory=dict)


class CDSPrescriptionCheckResponse(BaseModel):
    status: str
    risk_level: str
    alerts: list[AlertRead]
    cards: list[CDSCard]
    audit_id: str
    educational_notice: str
