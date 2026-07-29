from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.prescription_schema import (
    AlertRead,
    ClinicalDecisionEnvelopeRead,
    MedicationDoseInputSchema,
)


class CDSPatientContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: int | None = Field(default=None, ge=0, le=130)
    weight_kg: float = Field(gt=0, le=400)
    height_cm: float | None = Field(default=None, gt=0, le=260)
    sex_for_dosing_calculation: str | None = None
    renal_condition: str | None = None
    hepatic_condition: str | None = None
    cardiac_condition: str | None = None
    gastrointestinal_history: str | None = None
    hypertension: bool | None = None
    diabetes: bool | None = None
    pregnancy_or_lactation: bool | None = None
    mental_health_factors: list[str] | None = None
    reproductive_gynecologic_factors: list[str] | None = None
    adverse_reactions: list[str] | None = None


class CDSMedicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medication_id: int | None = Field(default=None, gt=0)
    active_ingredient: str | None = Field(default=None, min_length=2, max_length=160)
    dose_mg: float | None = Field(default=None, gt=0)
    frequency_per_day: int | None = Field(default=None, gt=0, le=24)
    route: str | None = Field(default=None, min_length=2, max_length=80)
    dose: MedicationDoseInputSchema | None = None
    duration_days: int | None = Field(default=None, gt=0, le=365)
    indication: str | None = Field(default=None, max_length=180)
    professional_notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_identity_and_dose(self) -> CDSMedicationRequest:
        if self.medication_id is None and not self.active_ingredient:
            raise ValueError("informe medication_id ou princípio ativo canônico")
        legacy = self.dose_mg is not None and self.frequency_per_day is not None and self.route
        if self.dose is None and not legacy:
            raise ValueError("informe dose estruturada ou todos os campos legados")
        if self.dose is not None and any(
            value is not None for value in (self.dose_mg, self.frequency_per_day)
        ):
            raise ValueError("não misture dose estruturada e dose legada")
        return self


class CDSPrescriptionCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient: CDSPatientContext
    medication_request: CDSMedicationRequest
    allergies: list[str] | None = None
    conditions: list[str] | None = None
    current_medications: list[str] | None = None
    observations: list[dict] = Field(default_factory=list)
    persist: bool = False


class CDSCard(BaseModel):
    summary: str
    indicator: str
    detail: str
    source: dict = Field(default_factory=dict)


class CDSPrescriptionCheckResponse(BaseModel):
    decision: ClinicalDecisionEnvelopeRead
    coverage_status: str
    status: str
    risk_level: str
    alerts: list[AlertRead]
    cards: list[CDSCard]
    audit_id: str
    idempotency_key: str
    educational_notice: str
