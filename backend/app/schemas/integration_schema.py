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
    educational_notice: str = (
        "Importacao demonstrativa: dados ficam pendentes ate revisao humana."
    )

