from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.models import IntegrationAuditLogModel, UserModel


class IntegrationAuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        user: UserModel | None,
        patient_id: int | None,
        batch_id: int | None,
        action: str,
        source_system: str,
        details: dict,
    ) -> IntegrationAuditLogModel:
        record = IntegrationAuditLogModel(
            user_id=user.id if user else None,
            patient_id=patient_id,
            batch_id=batch_id,
            action=action,
            source_system=source_system,
            details=details,
        )
        self.db.add(record)
        self.db.flush()
        return record

