from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ValidationStatus = Literal[
    "generated_by_ai",
    "pending_review",
    "curated",
    "validated",
    "rejected",
    "obsolete",
]
GeneratedBy = Literal[
    "ai_provider",
    "fallback_deterministic",
    "manual_curated",
    "seed_demo",
]
ConfidenceLevel = Literal["low", "medium", "high", "insufficient_evidence"]


class CounselingEvidence(BaseModel):
    source_id: str
    source_name: str
    jurisdiction: str = "BR"
    excerpt: str
    source_url: str | None = None
    validation_status: str = "demo"


class MedicationCounselingProviderOutput(BaseModel):
    main_adverse_effects: list[str] = Field(default_factory=list)
    patient_relevant_effects: list[str] = Field(default_factory=list)
    activity_warnings: list[str] = Field(default_factory=list)
    driving_warning: bool = False
    machine_operation_warning: bool = False
    work_at_height_warning: bool = False
    fall_risk_warning: bool = False
    sedation_attention_warning: bool = False
    sleep_effects: list[str] = Field(default_factory=list)
    appetite_weight_effects: list[str] = Field(default_factory=list)
    mood_behavior_effects: list[str] = Field(default_factory=list)
    libido_sexual_effects: list[str] = Field(default_factory=list)
    neurologic_effects: list[str] = Field(default_factory=list)
    tremor_warning: bool = False
    headache_warning: bool = False
    temperature_regulation_effects: list[str] = Field(default_factory=list)
    blood_pressure_warning: bool = False
    gastrointestinal_effects: list[str] = Field(default_factory=list)
    renal_effects: list[str] = Field(default_factory=list)
    hepatic_effects: list[str] = Field(default_factory=list)
    reproductive_contraceptive_effects: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    monitoring_required: list[str] = Field(default_factory=list)
    patient_friendly_summary: str = ""
    professional_summary: str = ""
    source_ids: list[str] = Field(default_factory=list)
    extracted_evidence: list[CounselingEvidence] = Field(default_factory=list)
    confidence: ConfidenceLevel = "low"
    requires_review: bool = True


class MedicationCounselingSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    active_ingredient_id: int | None = None
    medication_id: int | None = None
    source_id: str
    jurisdiction: str
    source_name: str
    source_url: str | None = None
    source_version: str | None = None
    validation_status: str
    generated_by: str
    provider_name: str | None = None
    confidence: str
    requires_review: bool
    main_adverse_effects: list[str] = Field(default_factory=list)
    patient_relevant_effects: list[str] = Field(default_factory=list)
    activity_warnings: list[str] = Field(default_factory=list)
    driving_warning: bool
    machine_operation_warning: bool
    work_at_height_warning: bool
    fall_risk_warning: bool
    sedation_attention_warning: bool
    sleep_effects: list[str] = Field(default_factory=list)
    appetite_weight_effects: list[str] = Field(default_factory=list)
    mood_behavior_effects: list[str] = Field(default_factory=list)
    libido_sexual_effects: list[str] = Field(default_factory=list)
    neurologic_effects: list[str] = Field(default_factory=list)
    tremor_warning: bool
    headache_warning: bool
    temperature_regulation_effects: list[str] = Field(default_factory=list)
    blood_pressure_warning: bool
    gastrointestinal_effects: list[str] = Field(default_factory=list)
    renal_effects: list[str] = Field(default_factory=list)
    hepatic_effects: list[str] = Field(default_factory=list)
    reproductive_contraceptive_effects: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    monitoring_required: list[str] = Field(default_factory=list)
    patient_friendly_summary: str
    professional_summary: str
    extracted_evidence: list[dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MedicationCounselingGenerateRequest(BaseModel):
    provider_name: str | None = Field(default=None, max_length=80)
    source_text: str | None = None
    force_regenerate: bool = False


class MedicationCounselingReviewRequest(BaseModel):
    validation_status: Literal["curated", "validated", "rejected", "obsolete"]
    patient_friendly_summary: str | None = None
    professional_summary: str | None = None
    main_adverse_effects: list[str] | None = None
    patient_relevant_effects: list[str] | None = None
    activity_warnings: list[str] | None = None
    red_flags: list[str] | None = None
    justification: str | None = Field(default=None, max_length=500)
