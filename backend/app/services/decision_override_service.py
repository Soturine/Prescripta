from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import DecisionOverrideModel, PrescriptionAuditModel, UserModel


class DecisionOverrideError(ValueError):
    pass


class DecisionOverrideService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def request(
        self,
        *,
        audit: PrescriptionAuditModel,
        requester: UserModel,
        reason: str,
    ) -> DecisionOverrideModel:
        decision = dict(audit.clinical_decision or {})
        policy = dict(decision.get("override_policy") or {})
        findings = list(decision.get("findings") or [])
        if audit.user_id != requester.id:
            raise DecisionOverrideError("Somente o autor da decisão pode solicitar override.")
        if not policy.get("allowed"):
            raise DecisionOverrideError("A policy desta decisão não permite override.")
        if decision.get("highest_severity") == "critico" or any(
            finding.get("hard_block") for finding in findings
        ):
            raise DecisionOverrideError("Achado crítico ou hard block não admite override.")
        normalized_reason = reason.strip()
        if policy.get("reason_required", True) and len(normalized_reason) < 10:
            raise DecisionOverrideError("Justificativa clínica detalhada é obrigatória.")
        existing = self.db.scalar(
            select(DecisionOverrideModel).where(
                DecisionOverrideModel.prescription_audit_id == audit.id
            )
        )
        if existing is not None:
            raise DecisionOverrideError("Já existe solicitação de override para esta decisão.")
        row = DecisionOverrideModel(
            prescription_audit_id=audit.id,
            requested_by_user_id=requester.id,
            reason=normalized_reason,
            status="pending_second_review",
        )
        self.db.add(row)
        self.db.flush()
        return row

    def review(
        self,
        *,
        override: DecisionOverrideModel,
        reviewer: UserModel,
        decision: str,
        note: str,
        required_role: str | None,
    ) -> DecisionOverrideModel:
        if override.status != "pending_second_review":
            raise DecisionOverrideError("A solicitação já foi revisada.")
        if override.requested_by_user_id == reviewer.id:
            raise DecisionOverrideError("O solicitante não pode atuar como segundo revisor.")
        if required_role and reviewer.role != required_role:
            raise DecisionOverrideError("O perfil do segundo revisor não atende à policy.")
        normalized_decision = decision.strip().lower()
        if normalized_decision not in {"approved", "rejected"}:
            raise DecisionOverrideError("Decisão de revisão inválida.")
        if len(note.strip()) < 10:
            raise DecisionOverrideError("Nota do segundo revisor é obrigatória.")
        override.reviewed_by_user_id = reviewer.id
        override.review_decision = normalized_decision
        override.review_note = note.strip()
        override.reviewed_at = datetime.now(UTC)
        override.status = normalized_decision
        self.db.flush()
        return override
