from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OmopPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    study_id: str
    cohort_run_id: str
    terminology_release_ids: list[str] = Field(default_factory=list, max_length=20)


class OmopEtlRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    study_id: str | None
    cohort_run_id: str | None
    source_classification: str
    synthetic_only: bool
    source_snapshot_marker: str
    source_snapshot_hash: str
    source_schema_version: str
    adapter_version: str
    cdm_version: str
    terminology_release_ids: list[str]
    mapping_hashes: list[str]
    status: str
    metrics: dict
    warnings: list[str]
    errors: list[str]
    manifest: dict
    export_files: dict
    export_hash: str
    executed_by_user_id: int
    started_at: datetime
    completed_at: datetime | None


class OmopCompatibilityRead(BaseModel):
    cdm_version: Literal["5.4"]
    claim_level: Literal["omop_v5_4_partial_adapter"]
    targets: list[dict]
    synthetic_only: bool
    ohdsi_tool_validated: bool
    content_hash: str
