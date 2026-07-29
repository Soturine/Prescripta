from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientAccessGrantCreate(BaseModel):
    user_id: int = Field(gt=0)
    capability: str = Field(min_length=3, max_length=80)
    purpose: str = Field(default="treatment", max_length=40)
    reason: str = Field(min_length=8, max_length=220)
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    care_episode_id: str | None = Field(default=None, max_length=80)


class PatientAccessGrantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    user_id: int
    institution_id: str
    capability: str
    purpose: str
    reason: str | None
    starts_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    status: str
    care_episode_id: str | None


class AccessRevokeRequest(BaseModel):
    reason: str = Field(min_length=8, max_length=220)


class CareTeamMembershipCreate(BaseModel):
    user_id: int = Field(gt=0)
    team_code: str = Field(min_length=2, max_length=80)
    care_role: str = Field(min_length=2, max_length=80)
    capabilities: list[str] = Field(min_length=1)
    purpose: str = Field(default="treatment", max_length=40)
    starts_at: datetime | None = None
    expires_at: datetime | None = None


class CareTeamMembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    user_id: int
    institution_id: str
    team_code: str
    care_role: str
    capabilities: list[str]
    purpose: str
    starts_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None


class CareEpisodeAssignmentCreate(BaseModel):
    user_id: int = Field(gt=0)
    episode_id: str = Field(min_length=3, max_length=80)
    capabilities: list[str] = Field(min_length=1)
    purpose: str = Field(default="treatment", max_length=40)
    starts_at: datetime | None = None
    expires_at: datetime | None = None


class CareEpisodeAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    episode_id: str
    patient_id: int
    user_id: int
    institution_id: str
    capabilities: list[str]
    purpose: str
    starts_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None


class BreakGlassCreate(BaseModel):
    capability: str = Field(default="patient.read", min_length=3, max_length=80)
    purpose: str = Field(default="treatment", max_length=40)
    reason: str = Field(min_length=20, max_length=500)
    duration_minutes: int = Field(default=30, ge=5, le=60)
    idempotency_key: str = Field(min_length=8, max_length=160)


class BreakGlassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    user_id: int
    institution_id: str
    capability: str
    purpose: str
    reason: str
    started_at: datetime
    expires_at: datetime
    ended_at: datetime | None
    review_status: str
    reviewed_at: datetime | None
    objects_accessed: list[dict]
    status: str


class BreakGlassReview(BaseModel):
    decision: str = Field(pattern="^(approved|concern|rejected)$")
    notes: str = Field(min_length=8, max_length=500)
