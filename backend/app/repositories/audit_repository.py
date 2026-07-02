from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import PrescriptionAuditModel


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[PrescriptionAuditModel]:
        return list(
            self.db.scalars(
                select(PrescriptionAuditModel).order_by(PrescriptionAuditModel.checked_at.desc())
            )
        )

    def count(self) -> int:
        return self.db.scalar(select(func.count(PrescriptionAuditModel.id))) or 0

    def create(self, **values: object) -> PrescriptionAuditModel:
        audit = PrescriptionAuditModel(**values)
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def alerts_by_severity(self) -> dict[str, int]:
        counters = {"baixo": 0, "moderado": 0, "alto": 0, "critico": 0}
        for audit in self.list():
            for alert in audit.alerts or []:
                severity = alert.get("severity")
                if severity in counters:
                    counters[severity] += 1
        return counters
