from sqlalchemy.orm import Session

from app.repositories.audit_repository import AuditRepository


class PrescriptionRepository:
    def __init__(self, db: Session) -> None:
        self.audit_repository = AuditRepository(db)

    def count_analyzed(self) -> int:
        return self.audit_repository.count()
