from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    ClinicalImportBatchModel,
    ClinicalSourceRecordModel,
    UserModel,
)
from app.integrations.services.consent_service import ConsentService
from app.integrations.services.integration_audit_service import IntegrationAuditService


class IntegrationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.consent = ConsentService(db)
        self.audit = IntegrationAuditService(db)

    def create_import_batch(
        self,
        *,
        source_system: str,
        source_type: str,
        records: list[dict],
        user: UserModel,
        patient_id: int | None,
        consent_confirmed: bool,
        authorized_by: str,
        purpose: str,
    ) -> ClinicalImportBatchModel:
        consent = self.consent.create_import_consent(
            consent_confirmed=consent_confirmed,
            patient_id=patient_id,
            authorized_by=authorized_by,
            purpose=purpose,
            source_system=source_system,
        )
        batch = ClinicalImportBatchModel(
            source_system=source_system,
            source_type=source_type,
            imported_by=user.id,
            patient_id=patient_id,
            consent_id=consent.id,
            status="pending_review",
            errors=[] if records else ["Nenhum registro reconhecido no payload demonstrativo."],
        )
        self.db.add(batch)
        self.db.flush()
        for record in records:
            self.db.add(
                ClinicalSourceRecordModel(
                    batch_id=batch.id,
                    record_type=record["record_type"],
                    source_payload=record.get("source_payload") or {},
                    mapped_payload=record.get("mapped_payload") or {},
                    confidence=float(record.get("confidence") or 0),
                )
            )
        self.audit.record(
            user=user,
            patient_id=patient_id,
            batch_id=batch.id,
            action="clinical_import.created",
            source_system=source_system,
            details={
                "source_type": source_type,
                "records_count": len(records),
                "status": batch.status,
                "purpose": purpose,
            },
        )
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def list_batches(self) -> list[ClinicalImportBatchModel]:
        return list(
            self.db.scalars(
                select(ClinicalImportBatchModel).order_by(
                    ClinicalImportBatchModel.imported_at.desc()
                )
            )
        )

    def get_batch(self, batch_id: int) -> ClinicalImportBatchModel | None:
        return self.db.get(ClinicalImportBatchModel, batch_id)

    def list_records(self, batch_id: int) -> list[ClinicalSourceRecordModel]:
        return list(
            self.db.scalars(
                select(ClinicalSourceRecordModel)
                .where(ClinicalSourceRecordModel.batch_id == batch_id)
                .order_by(ClinicalSourceRecordModel.id)
            )
        )

    def accept_batch(
        self, batch: ClinicalImportBatchModel, user: UserModel
    ) -> ClinicalImportBatchModel:
        batch.status = "accepted"
        batch.finished_at = datetime.now(UTC)
        for record in self.list_records(batch.id):
            record.accepted_by_user = True
            record.rejected_reason = None
        self.audit.record(
            user=user,
            patient_id=batch.patient_id,
            batch_id=batch.id,
            action="clinical_import.accepted",
            source_system=batch.source_system,
            details={"status": batch.status, "human_review_required": True},
        )
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def reject_batch(
        self,
        batch: ClinicalImportBatchModel,
        user: UserModel,
        *,
        reason: str | None = None,
    ) -> ClinicalImportBatchModel:
        batch.status = "rejected"
        batch.finished_at = datetime.now(UTC)
        for record in self.list_records(batch.id):
            record.accepted_by_user = False
            record.rejected_reason = reason or "Rejeitado em revisao humana."
        self.audit.record(
            user=user,
            patient_id=batch.patient_id,
            batch_id=batch.id,
            action="clinical_import.rejected",
            source_system=batch.source_system,
            details={"status": batch.status, "reason": reason},
        )
        self.db.commit()
        self.db.refresh(batch)
        return batch
