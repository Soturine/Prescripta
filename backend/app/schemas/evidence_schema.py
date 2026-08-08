from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceSourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: Literal[
        "guideline",
        "regulatory_source",
        "systematic_review",
        "observational_study",
        "randomized_trial",
        "institutional_protocol",
        "terminology_source",
        "other",
    ]
    title: str = Field(min_length=4, max_length=300)
    identifier: str = Field(min_length=3, max_length=180)
    url: str | None = Field(default=None, max_length=500)
    publisher: str | None = Field(default=None, max_length=220)
    jurisdiction: str | None = Field(default=None, max_length=40)
    publication_date: date | None = None
    access_date: date | None = None
    source_version: str | None = Field(default=None, max_length=120)
    license_metadata: dict = Field(min_length=1)
    content_hash: str | None = Field(default=None, min_length=64, max_length=64)
    provenance: dict = Field(min_length=1)


class EvidenceSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    source_type: str
    title: str
    identifier: str
    url: str | None
    publisher: str | None
    jurisdiction: str | None
    publication_date: date | None
    access_date: date | None
    source_version: str | None
    review_status: str
    reviewer_user_id: int | None
    license_metadata: dict
    content_hash: str | None
    provenance: dict
    created_by_user_id: int
    created_at: datetime


class EvidenceLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=36, max_length=36)
    target_type: Literal[
        "clinical_finding",
        "dose_rule",
        "medication",
        "protocol",
        "study",
        "outcome",
        "concept_set",
    ]
    target_id: str = Field(min_length=1, max_length=100)
    relationship: str = Field(min_length=2, max_length=80)
    locator: str = Field(default="", max_length=220)


class EvidenceLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    source_id: str
    target_type: str
    target_id: str
    relationship: str
    locator: str
    review_status: str
    created_by_user_id: int
    created_at: datetime
