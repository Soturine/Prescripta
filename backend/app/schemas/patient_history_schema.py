from __future__ import annotations

from datetime import datetime
from pathlib import PurePath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PatientClinicalDocumentCreate(BaseModel):
    document_type: str = Field(default="clinical_note", max_length=80)
    title: str = Field(min_length=2, max_length=180)
    summary: str | None = None
    source_type: str = Field(default="manual_text", max_length=80)
    source_system: str | None = Field(default=None, max_length=120)
    document_date: datetime | None = None
    raw_text: str = Field(default="", max_length=20000)
    structured_payload: dict[str, Any] = Field(default_factory=dict)
    storage_path: str | None = Field(default=None, max_length=500)

    @field_validator("storage_path")
    @classmethod
    def validate_demo_storage_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        path = PurePath(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Caminho de documento inválido.")
        if path.suffix.lower() not in {".pdf", ".png", ".jpg", ".jpeg", ".txt"}:
            raise ValueError("Extensão de documento não permitida.")
        return value


class PatientClinicalDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    document_type: str
    title: str
    summary: str
    source_type: str
    source_system: str | None
    document_date: datetime | None
    uploaded_at: datetime
    uploaded_by: int | None
    raw_text: str
    structured_payload: dict[str, Any]
    extracted_entities: dict[str, Any]
    confidence: float
    validation_status: str
    review_status: str
    reviewed_by: int | None
    reviewed_at: datetime | None
    file_hash: str | None
    storage_path: str | None


class PatientDocumentExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    document_id: int
    provider: str
    model: str | None
    extracted_entities: dict[str, Any]
    confidence: float
    validation_status: str
    review_status: str
    reviewed_by: int | None
    reviewed_at: datetime | None
    created_at: datetime


class PatientDocumentReviewRequest(BaseModel):
    decision: Literal["accept", "reject"]
    accepted_entities: dict[str, Any] | None = None
    justification: str | None = Field(default=None, max_length=1000)


class PatientClinicalTimelineEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    event_type: str
    title: str
    summary: str
    source_type: str
    source_system: str | None
    event_date: datetime | None
    payload: dict[str, Any]
    validation_status: str
    created_by: int | None
    created_at: datetime


class PatientKnowledgeBundleRead(BaseModel):
    patient_id: int
    patient_reference: str
    generated_at: datetime
    send_identifiable_data: bool = False
    structured_profile: dict[str, Any]
    documents: list[dict[str, Any]] = Field(default_factory=list)
    reviewed_documents: list[dict[str, Any]] = Field(default_factory=list)
    reviewed_entities: dict[str, Any] = Field(default_factory=dict)
    reviewed_extractions: list[dict[str, Any]] = Field(default_factory=list)
    medication_history: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    imported_context: list[dict[str, Any]] = Field(default_factory=list)
    imports: list[dict[str, Any]] = Field(default_factory=list)
    protocol_context: list[dict[str, Any]] = Field(default_factory=list)
    protocol_runs: list[dict[str, Any]] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    educational_notice: str = (
        "Bundle minimizado para apoio explicativo; nao substitui revisao humana."
    )
