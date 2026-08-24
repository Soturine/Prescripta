from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EvidenceProvider = Literal["pubmed", "crossref", "openalex"]


class EvidenceSearchPlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(min_length=36, max_length=36)
    providers: list[EvidenceProvider] = Field(min_length=1, max_length=3)
    canonical_query: str = Field(min_length=3, max_length=500)
    provider_queries: dict[EvidenceProvider, str] = Field(default_factory=dict)
    filters: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def provider_query_scope(self) -> EvidenceSearchPlanCreate:
        if set(self.provider_queries) - set(self.providers):
            raise ValueError("Provider query fora da lista autorizada.")
        return self


class EvidenceSearchPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    study_id: str
    version: int
    providers: list[str]
    canonical_query: str
    provider_queries: dict
    filters: dict
    status: str
    result_count: int
    identifiers: list[dict]
    content_hash: str
    created_by_user_id: int
    reviewed_by_user_id: int | None
    executed_at: datetime | None
    created_at: datetime


class EvidenceSearchExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm_metadata_retrieval: Literal[True]


class AgentRunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(min_length=36, max_length=36)
    template: Literal["evidence_review", "study_design"]
    goal: str = Field(min_length=4, max_length=1000)
    data_classification: Literal["public", "synthetic"] = "public"
    source_ids: list[str] = Field(default_factory=list, max_length=30)


class AgentStepRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(min_length=8, max_length=160)


class AgentReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["approve_as_draft", "reject", "request_revision", "cancel"]
    note: str = Field(default="", max_length=1000)


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    study_id: str
    template: str
    template_version: str
    state: str
    goal_hash: str
    budgets: dict
    usage: dict
    allowed_tools: list[str]
    steps: list[dict]
    source_ids: list[str]
    proposal: dict
    human_checkpoint: dict
    provider: str | None
    model: str | None
    stop_reason: str | None
    created_by_user_id: int
    reviewed_by_user_id: int | None
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None
