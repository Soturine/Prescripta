from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AITaskType = Literal[
    "clinical_decision_explanation",
    "research_question_structuring",
    "cohort_draft",
    "study_protocol_draft",
    "evidence_summary",
    "patient_journey_summary",
    "data_quality_explanation",
]
AIDataClassification = Literal[
    "public",
    "synthetic",
    "internal_demo",
    "sensitive",
    "restricted",
]


class AIRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_type: AITaskType
    data_classification: AIDataClassification
    study_id: str | None = Field(default=None, max_length=36)
    patient_id: int | None = Field(default=None, gt=0)
    source_ids: list[str] = Field(default_factory=list, max_length=30)
    requires_structured_output: bool = True
    schema_version: str = Field(default="v1", max_length=40)
    preferred_provider: str | None = Field(default=None, max_length=60)
    allowed_providers: list[str] = Field(default_factory=list, max_length=5)
    max_context: int = Field(default=12000, gt=0, le=50000)
    timeout: int = Field(default=30, gt=0, le=120)
    purpose: str = Field(min_length=3, max_length=120)
    input: dict

    @model_validator(mode="after")
    def validate_task_context(self) -> AIRequestSchema:
        if self.task_type in {
            "research_question_structuring",
            "cohort_draft",
            "study_protocol_draft",
        } and not self.study_id:
            raise ValueError("task de pesquisa exige study_id")
        if self.task_type == "patient_journey_summary" and not self.patient_id:
            raise ValueError("resumo de jornada exige patient_id")
        if not self.requires_structured_output:
            raise ValueError("v0.8.8 aceita somente saída estruturada")
        return self


class AIInteractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: str
    model: str | None
    provider_model_identifier: str | None
    task_type: str
    prompt_template_version: str
    structured_schema_version: str
    source_ids: list[str]
    study_id: str | None
    patient_id: int | None
    user_id: int
    institution_id: str
    input_hash: str
    output_hash: str
    generated_at: datetime
    latency_ms: int
    status: str
    fallback_used: bool
    data_classification: str
    human_review_status: str
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    sanitized_error_class: str | None
    usage_metadata: dict
    output_payload: dict


class AIInteractionReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["accepted_as_draft", "rejected", "superseded"]
    note: str = Field(min_length=8, max_length=1000)
