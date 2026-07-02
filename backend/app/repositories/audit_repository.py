from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import AuditEventModel, PrescriptionAuditModel


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[AuditEventModel]:
        return list(
            self.db.scalars(select(AuditEventModel).order_by(AuditEventModel.created_at.desc()))
        )

    def list_prescription_checks(self) -> list[PrescriptionAuditModel]:
        return list(
            self.db.scalars(
                select(PrescriptionAuditModel).order_by(PrescriptionAuditModel.checked_at.desc())
            )
        )

    def count(self) -> int:
        return self.db.scalar(select(func.count(PrescriptionAuditModel.id))) or 0

    def create_prescription_check(self, **values: object) -> PrescriptionAuditModel:
        audit = PrescriptionAuditModel(**values)
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def create_event(self, **values: object) -> AuditEventModel:
        event = AuditEventModel(**values)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def alerts_by_severity(self) -> dict[str, int]:
        counters = {"baixo": 0, "moderado": 0, "alto": 0, "critico": 0}
        for audit in self.list_prescription_checks():
            for alert in audit.alerts or []:
                severity = alert.get("severity")
                if severity in counters:
                    counters[severity] += 1
        return counters
