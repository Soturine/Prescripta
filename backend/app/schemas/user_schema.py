from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.user import Profession, UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: UserRole
    profession: Profession
    capabilities: list[str] = Field(default_factory=list)
    capability_policy_version: str = "explicit-v1"
    is_active: bool
    created_at: datetime
    specialty_code: str | None = None
    specialty_codes: list[str] = Field(default_factory=list)
    credential_type: str | None = None
    credential_code_demo: str | None = None
    credential_region: str | None = None
    credential_expires_at: datetime | None = None
    institutional_policy: dict = Field(default_factory=dict)
    sensitive_data_segments: list[str] = Field(default_factory=list)
    crm_demo: str | None = None
    crm_uf: str | None = None
    rqe_demo: str | None = None
    credential_verification_status: str = "demo_unverified"
    institution_id: str = "demo"
    mfa_enabled: bool = False


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=220, pattern=r"^[^@\s]+@[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    profession: Profession | None = None
    capabilities: list[str] = Field(default_factory=list)
    is_active: bool = True
    specialty_code: str | None = Field(default=None, max_length=80)
    specialty_codes: list[str] = Field(default_factory=list)
    credential_type: str | None = Field(default=None, max_length=40)
    credential_code_demo: str | None = Field(default=None, max_length=80)
    credential_region: str | None = Field(default=None, max_length=20)
    credential_expires_at: datetime | None = None
    institutional_policy: dict = Field(default_factory=dict)
    sensitive_data_segments: list[str] = Field(default_factory=list)
    crm_demo: str | None = Field(default=None, max_length=40)
    crm_uf: str | None = Field(default=None, min_length=2, max_length=2)
    rqe_demo: str | None = Field(default=None, max_length=40)
    credential_verification_status: str = "demo_unverified"
    institution_id: str = Field(default="demo", min_length=1, max_length=100)


class UserClinicalProfileUpdate(BaseModel):
    profession: Profession | None = None
    capabilities: list[str] | None = None
    specialty_code: str | None = Field(default=None, max_length=80)
    specialty_codes: list[str] | None = None
    credential_type: str | None = Field(default=None, max_length=40)
    credential_code_demo: str | None = Field(default=None, max_length=80)
    credential_region: str | None = Field(default=None, max_length=20)
    credential_expires_at: datetime | None = None
    institutional_policy: dict | None = None
    sensitive_data_segments: list[str] | None = None
    crm_demo: str | None = Field(default=None, max_length=40)
    crm_uf: str | None = Field(default=None, min_length=2, max_length=2)
    rqe_demo: str | None = Field(default=None, max_length=40)
    credential_verification_status: str = "demo_unverified"


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    is_active: bool
