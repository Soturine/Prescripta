from pydantic import BaseModel, Field

from app.schemas.user_schema import UserRead


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=220, pattern=r"^[^@\s]+@[^@\s]+$")
    password: str = Field(min_length=1)
    mfa_code: str | None = Field(default=None, pattern=r"^\d{6}$")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
