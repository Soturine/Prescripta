from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    user_name: str | None
    user_email: str | None
    user_role: str | None
    action: str
    resource_type: str
    resource_id: str | None
    created_at: datetime
    risk_level: str | None
    status: str | None
    details: dict
