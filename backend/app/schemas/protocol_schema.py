from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

WarningLevel = Literal["info", "attention", "high", "critical"]


class ProtocolContextField(BaseModel):
    name: str
    label: str
    field_type: Literal["number", "text", "boolean", "select", "multiselect"]
    required: bool = False
    unit: str | None = None
    helper: str | None = None
    options: list[str] = Field(default_factory=list)


class ProtocolStepRead(BaseModel):
    order: int
    title: str
    action: str
    explanation: str
    warning_level: WarningLevel = "info"
    requires_human_judgment: bool = True
    evidence_ref: str


class ProtocolCalculatorRead(BaseModel):
    id: str
    label: str
    description: str
    input_fields: list[str] = Field(default_factory=list)
    source_note: str
    requires_human_confirmation: bool = True


class EmergencyProtocolRead(BaseModel):
    id: str
    slug: str
    title: str
    category: str
    summary: str
    clinical_goal: str
    severity_level: WarningLevel
    audience: str
    jurisdiction: str = "BR"
    source_name: str
    source_url: str | None = None
    source_version: str | None = None
    validation_status: str = "demo_curated"
    last_reviewed_at: str
    disclaimer: str
    red_flags: list[str] = Field(default_factory=list)
    immediate_measures: list[str] = Field(default_factory=list)
    medication_references: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)
    referral_criteria: list[str] = Field(default_factory=list)
    monitoring: list[str] = Field(default_factory=list)
    documentation_items: list[str] = Field(default_factory=list)
    do_not_apply_when: list[str] = Field(default_factory=list)
    human_judgment_points: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    context_fields: list[ProtocolContextField] = Field(default_factory=list)
    calculators: list[ProtocolCalculatorRead] = Field(default_factory=list)
    steps: list[ProtocolStepRead] = Field(default_factory=list)


class ProtocolCalculatedValue(BaseModel):
    label: str
    value: str
    formula: str
    source_ref: str
    warning: str
    requires_human_confirmation: bool = True


class ProtocolEvidenceRead(BaseModel):
    evidence_ref: str
    source_name: str
    source_url: str | None = None
    source_version: str | None = None
    summary: str
    validation_status: str


class ProtocolRunRequest(BaseModel):
    patient_id: int | None = Field(default=None, gt=0)
    context: dict[str, Any] = Field(default_factory=dict)
    selected_step_orders: list[int] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=1000)


class ProtocolRunResponse(BaseModel):
    run_id: int
    audit_event_id: int | None = None
    protocol_id: str
    protocol_version: str
    title: str
    status: str
    warning_level: WarningLevel
    patient_id: int | None = None
    patient_context_summary: dict[str, Any] = Field(default_factory=dict)
    triage_flags: list[str] = Field(default_factory=list)
    calculated_values: list[ProtocolCalculatedValue] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[ProtocolEvidenceRead] = Field(default_factory=list)
    audit_notice: str
    educational_notice: str


class ProtocolExplainRequest(BaseModel):
    context: dict[str, Any] = Field(default_factory=dict)
    run_id: int | None = Field(default=None, gt=0)
    question: str | None = Field(default=None, max_length=500)


class ProtocolExplainResponse(BaseModel):
    provider: str
    model: str | None = None
    used_fallback: bool = True
    protocol_id: str
    simple_explanation: str
    professional_summary: str
    safety_note: str
    cited_evidence_refs: list[str] = Field(default_factory=list)
    structure_locked: bool = True
    educational_notice: str


class ProtocolReportPreview(BaseModel):
    title: str
    protocol_id: str
    protocol_version: str | None = None
    run_id: int | None = None
    generated_report_id: int | None = None
    generated_at: datetime
    report_lines: list[str]
    report_payload: dict[str, Any]
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[ProtocolEvidenceRead] = Field(default_factory=list)


class ProtocolRunEventExport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    resource_type: str
    resource_id: str | None
    created_at: datetime
    status: str | None = None
    risk_level: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
