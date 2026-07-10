from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.version import APP_VERSION_LABEL, REPORT_TEMPLATE_VERSION

PRESCRIPTA_VERSION = APP_VERSION_LABEL

ReportType = Literal[
    "prescription_analysis",
    "patient_guidance",
    "reconciliation",
    "audit",
]
ReportMode = Literal[
    "complete_internal",
    "anonymized",
    "patient_friendly",
    "technical_audit",
]


class ReportPatientContext(BaseModel):
    patient_reference: str
    age_group: str = "unknown"
    sex_or_reproductive_context: str = "unknown"
    clinical_profile: dict[str, str | bool | None] = Field(default_factory=dict)
    functional_profile: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)


class ReportAlertEvidence(BaseModel):
    code: str
    title: str | None = None
    severity: str
    source_id: str
    evidence_summary: str
    rule_id: str
    recommendation: str | None = None


class ReportPrescriptionResult(BaseModel):
    risk_level: str
    status: str
    medication_name: str
    active_ingredient: str | None = None
    commercial_name: str | None = None
    dose_per_administration: str
    frequency: str
    route: str
    daily_dose: str
    accumulated_dose: str | None = None
    duration: str | None = None
    continuous_use: bool = False
    alerts: list[ReportAlertEvidence] = Field(default_factory=list)


class ReportSource(BaseModel):
    source_id: str
    source_name: str
    jurisdiction: str = "BR"
    validation_status: str = "demo"
    evidence_type: str = "internal_record"
    source_url: str | None = None
    confidence: str | None = None
    reviewed_at: str | None = None


class ReportAIContext(BaseModel):
    allow_external_ai: bool = False
    provider: str = "fallback"
    model: str | None = "deterministic"
    send_identifiable_data: bool = False


class ReportEvidenceBundle(BaseModel):
    report_type: ReportType
    report_mode: ReportMode
    report_version: str = PRESCRIPTA_VERSION
    prescripta_version: str = PRESCRIPTA_VERSION
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    patient_context: ReportPatientContext | None = None
    prescription_result: ReportPrescriptionResult | None = None
    reconciliation_result: dict[str, Any] | None = None
    audit_result: dict[str, Any] | None = None
    rules_fired: list[str] = Field(default_factory=list)
    sources: list[ReportSource] = Field(default_factory=list)
    ai_context: ReportAIContext = Field(default_factory=ReportAIContext)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def stable_payload(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json")
        payload.pop("generated_at", None)
        return payload

    def hash(self) -> str:
        encoded = json.dumps(
            self.stable_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


class ReportNarrativeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str = ""
    professional_explanation: str = ""
    patient_guidance: str = ""
    evidence_summary: str = ""
    missing_data_note: str = ""
    functional_context_note: str = ""
    reconciliation_summary: str = ""
    safety_counseling_summary: str = ""
    limitations_note: str = ""
    human_review_note: str = ""
    source_note: str = ""
    confidence: float = Field(default=0.55, ge=0, le=1)
    requires_human_review: bool = True
    warnings: list[str] = Field(default_factory=list)
    cited_source_ids: list[str] = Field(default_factory=list)

    @field_validator(
        "executive_summary",
        "professional_explanation",
        "patient_guidance",
        "evidence_summary",
        "missing_data_note",
        "functional_context_note",
        "reconciliation_summary",
        "safety_counseling_summary",
        "limitations_note",
        "human_review_note",
        "source_note",
        mode="before",
    )
    @classmethod
    def safe_text(cls, value: object) -> str:
        text = str(value or "").strip()
        if "<" in text or ">" in text:
            raise ValueError("HTML bruto nao e aceito em narrativa de relatorio.")
        return text[:3000]

    @field_validator("warnings", "cited_source_ids", mode="before")
    @classmethod
    def safe_text_list(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        clean = []
        for item in value:
            text = str(item or "").strip()
            if text and "<" not in text and ">" not in text:
                clean.append(text[:500])
        return clean[:12]


class ReportNarrativeComposition(BaseModel):
    narrative: ReportNarrativeSchema
    provider: str
    model: str | None = None
    prompt_version: str
    ai_used: bool = False
    fallback_used: bool = True
    status: str = "fallback"
    response_time_ms: int | None = None
    error_summary: str | None = None


class GeneratedReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_type: str
    target_type: str
    target_id: str
    generated_by_user_id: int | None
    generated_at: datetime
    template_version: str
    prescripta_version: str
    evidence_bundle_hash: str
    ai_provider: str | None
    ai_model: str | None
    ai_prompt_version: str | None
    ai_used: bool
    fallback_used: bool
    anonymized: bool
    file_hash: str | None
    status: str
    metadata_json: dict


class ReportPreview(BaseModel):
    title: str
    report_type: str
    report_mode: str
    template_version: str = REPORT_TEMPLATE_VERSION
    prescripta_version: str = PRESCRIPTA_VERSION
    evidence_bundle_hash: str
    evidence_bundle: dict
    narrative: ReportNarrativeSchema
    narrative_metadata: dict
    timeline: list[dict]
    evidence: list[dict]
    html: str
