from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TerminologySourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_system: str = Field(min_length=2, max_length=120)
    public_name: str = Field(min_length=2, max_length=220)
    steward: str = Field(min_length=2, max_length=220)
    family: Literal["icd", "snomed", "loinc", "rxnorm", "atc", "omop", "synthetic"]
    source_reference: str = Field(min_length=8, max_length=500)
    jurisdiction: str | None = Field(default=None, max_length=80)
    locale: str | None = Field(default=None, max_length=40)


class TerminologySourceRead(TerminologySourceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    active: bool
    created_by_user_id: int
    created_at: datetime


class TerminologyReleaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edition: str = Field(default="", max_length=120)
    version: str = Field(min_length=1, max_length=120)
    release_date: date | None = None
    source_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_artifact_name: str = Field(min_length=1, max_length=240)
    license_identifier: str = Field(min_length=1, max_length=120)
    license_name: str = Field(min_length=2, max_length=240)
    license_reference: str = Field(min_length=8, max_length=500)
    redistributable: bool = False
    requires_license: bool = False
    requires_login: bool = False
    requires_attribution: bool = False
    commercial_redistribution_allowed: bool | None = None
    license_note: str = Field(default="", max_length=2000)
    license_status: Literal[
        "metadata_only", "license_required", "authorized", "not_applicable"
    ] = "metadata_only"
    provenance: dict = Field(min_length=1)


class TerminologyReleaseRead(TerminologyReleaseCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    institution_id: str
    imported_at: datetime | None
    status: str
    imported_by_user_id: int | None
    import_run_id: str | None
    content_hash: str


class TerminologyImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_name: str = Field(min_length=1, max_length=240)
    format: Literal["csv", "zip_csv"]
    content_base64: str = Field(min_length=1, max_length=8_000_000)


class TerminologyImportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    release_id: str
    institution_id: str
    input_hash: str
    artifact_name: str
    status: str
    inserted_count: int
    updated_count: int
    skipped_count: int
    rejected_count: int
    error_summary: dict
    imported_by_user_id: int
    started_at: datetime
    completed_at: datetime | None


class TerminologyConceptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    release_id: str
    source_system: str
    source_code: str
    display: str
    aliases: list[str]
    domain: str
    concept_class: str | None
    standard_status: str
    omop_concept_id: int | None
    valid_start_date: date | None
    valid_end_date: date | None
    invalid_reason: str | None
    provenance: dict
    content_hash: str


class TerminologyConceptPage(BaseModel):
    items: list[TerminologyConceptRead]
    offset: int
    limit: int
    total: int
    suggestion_only: bool


class TerminologyMappingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_concept_id: str
    target_concept_id: str
    relationship_type: Literal["Maps to", "Maps to value", "Mapped from"]
    mapping_method: Literal["manual", "omop_vocabulary", "explicit_fixture"]
    domain_expectation: str = Field(min_length=2, max_length=80)
    confidence: float | None = Field(default=None, ge=0, le=1)
    rationale: str = Field(min_length=8, max_length=2000)
    provenance: dict = Field(min_length=1)
    supersedes_mapping_id: str | None = None


class TerminologyMappingReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approved_for_demo", "rejected", "deprecated"]
    note: str = Field(min_length=8, max_length=2000)


class TerminologyMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    mapping_family_id: str
    institution_id: str
    source_concept_id: str
    target_concept_id: str
    relationship_type: str
    mapping_method: str
    domain_expectation: str
    confidence: float | None
    rationale: str
    provenance: dict
    version: int
    mapping_hash: str
    status: str
    authored_by_user_id: int
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    review_note: str | None
    supersedes_mapping_id: str | None
    created_at: datetime


class TerminologyDriftRead(BaseModel):
    source_release_id: str
    target_release_id: str
    summary: dict[str, int]
    changes: list[dict]
    content_hash: str
