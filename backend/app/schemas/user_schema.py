from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.user import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    specialty_code: str | None = None
    crm_demo: str | None = None
    crm_uf: str | None = None
    rqe_demo: str | None = None
    credential_verification_status: str = "demo_unverified"


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=220, pattern=r"^[^@\s]+@[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    is_active: bool = True
    specialty_code: str | None = Field(default=None, max_length=80)
    crm_demo: str | None = Field(default=None, max_length=40)
    crm_uf: str | None = Field(default=None, min_length=2, max_length=2)
    rqe_demo: str | None = Field(default=None, max_length=40)
    credential_verification_status: str = "demo_unverified"


class UserClinicalProfileUpdate(BaseModel):
    specialty_code: str | None = Field(default=None, max_length=80)
    crm_demo: str | None = Field(default=None, max_length=40)
    crm_uf: str | None = Field(default=None, min_length=2, max_length=2)
    rqe_demo: str | None = Field(default=None, max_length=40)
    credential_verification_status: str = "demo_unverified"


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    is_active: bool
