from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class MedicationKnowledgeLookupRequest(BaseModel):
    query: str = Field(min_length=2, max_length=180)
    source_name: str = Field(default="fonte_informada", min_length=2, max_length=180)
    source_url: str | None = Field(default=None, max_length=500)
    source_text: str | None = Field(default=None, max_length=12000)


class MedicationBulkImportRequest(BaseModel):
    items: list[dict[str, Any]] = Field(min_length=1, max_length=250)
    source_name: str = Field(default="importacao_lote", min_length=2, max_length=180)
    source_url: str | None = Field(default=None, max_length=500)
    dry_run: bool = False


class MedicationKnowledgeReviewRequest(BaseModel):
    decision: Literal["approve", "reject"]
    justification: str | None = Field(default=None, max_length=500)
    edited_payload: dict[str, Any] | None = None


class MedicationKnowledgeCurationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    source_name: str
    source_url: str | None = None
    source_text_excerpt: str
    extracted_payload: dict
    provider: str
    model: str | None = None
    validation_status: str
    review_status: str
    reviewed_by: int | None = None
    created_by: int | None = None
