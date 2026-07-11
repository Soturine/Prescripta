from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImportConsentPayload(BaseModel):
    consent_confirmed: bool
    purpose: str = Field(min_length=3, max_length=240)
    authorized_by: str = Field(min_length=2, max_length=160)
    source_system: str = Field(min_length=2, max_length=120)
    patient_id: int | None = Field(default=None, gt=0)


class FhirBundleImportRequest(ImportConsentPayload):
    bundle: dict


class GenericJsonImportRequest(ImportConsentPayload):
    payload: dict


class CsvImportRequest(ImportConsentPayload):
    csv_text: str = Field(min_length=3)


class ImportReviewRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class ClinicalSourceRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    record_type: str
    source_payload: dict
    mapped_payload: dict
    confidence: float
    accepted_by_user: bool
    rejected_reason: str | None = None
    created_at: datetime


class ClinicalImportBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_system: str
    source_type: str
    imported_by: int | None = None
    patient_id: int | None = None
    consent_id: int | None = None
    status: str
    imported_at: datetime
    finished_at: datetime | None = None
    errors: list[str] = Field(default_factory=list)
    records: list[ClinicalSourceRecordRead] = Field(default_factory=list)
    educational_notice: str = "Importação assistida: dados ficam pendentes até revisão humana."


class ReconciliationDecisionRequest(BaseModel):
    justification: str | None = Field(default=None, max_length=500)


class ClinicalReconciliationItemRead(BaseModel):
    item_id: str
    source_record_id: int | None = None
    record_type: str
    field_path: str
    current_value: dict
    imported_value: dict
    source_system: str
    source_type: str
    confidence: float
    badge: str
    suggestion: str
    conflict: bool
    decision: str | None = None
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    justification: str | None = None


class ClinicalReconciliationRead(BaseModel):
    batch_id: int
    patient_id: int | None = None
    status: str
    summary: dict
    items: list[ClinicalReconciliationItemRead]
    badges: list[str] = Field(default_factory=list)
    educational_notice: str = "Reconciliação assistida: conflitos exigem decisão humana por item."
