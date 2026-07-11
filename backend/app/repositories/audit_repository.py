from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.database.models import AuditEventModel, PrescriptionAuditModel


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[AuditEventModel]:
        return list(
            self.db.scalars(select(AuditEventModel).order_by(AuditEventModel.created_at.desc()))
        )

    def get_event(self, event_id: int) -> AuditEventModel | None:
        return self.db.get(AuditEventModel, event_id)

    def list_filtered(
        self,
        *,
        user: str | None = None,
        user_role: str | None = None,
        patient: str | None = None,
        medication: str | None = None,
        active_ingredient: str | None = None,
        protocol: str | None = None,
        protocol_category: str | None = None,
        protocol_severity: str | None = None,
        protocol_version: str | None = None,
        execution: str | None = None,
        report_type: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        risk_level: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        ai_provider: str | None = None,
        ai_model: str | None = None,
        fallback_used: bool | None = None,
        source: str | None = None,
        jurisdiction: str | None = None,
        specialty: str | None = None,
        policy_type: str | None = None,
        policy_strength: str | None = None,
        dose_rule_id: str | None = None,
        psychotropic_signal_code: str | None = None,
        prescriber_policy_status: str | None = None,
        credential_verification_status: str | None = None,
        high_alert_category: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        text: str | None = None,
        sort: str = "desc",
        page: int = 1,
        page_size: int = 100,
    ) -> list[AuditEventModel]:
        statement = select(AuditEventModel)
        direct_filters = {
            AuditEventModel.user_role: user_role,
            AuditEventModel.action: action,
            AuditEventModel.resource_type: resource_type,
            AuditEventModel.risk_level: risk_level,
            AuditEventModel.status: status,
        }
        for column, expected in direct_filters.items():
            if expected:
                statement = statement.where(column.ilike(f"%{expected}%"))
        if user:
            needle = f"%{user}%"
            statement = statement.where(
                or_(
                    AuditEventModel.user_name.ilike(needle),
                    AuditEventModel.user_email.ilike(needle),
                    cast(AuditEventModel.user_id, String).ilike(needle),
                )
            )
        if date_from:
            statement = statement.where(AuditEventModel.created_at >= date_from)
        if date_to:
            statement = statement.where(AuditEventModel.created_at <= date_to)

        details_text = cast(AuditEventModel.details, String)
        detail_values = (
            patient,
            medication,
            active_ingredient,
            protocol,
            protocol_category,
            protocol_severity,
            protocol_version,
            execution,
            report_type,
            severity,
            ai_provider,
            ai_model,
            source,
            jurisdiction,
            specialty,
            policy_type,
            policy_strength,
            dose_rule_id,
            psychotropic_signal_code,
            prescriber_policy_status,
            credential_verification_status,
            high_alert_category,
        )
        for expected in detail_values:
            if expected:
                statement = statement.where(details_text.ilike(f"%{expected}%"))
        if fallback_used is not None:
            statement = statement.where(
                AuditEventModel.details["fallback_used"].as_boolean() == fallback_used
            )
        if text:
            needle = f"%{text}%"
            statement = statement.where(
                or_(
                    AuditEventModel.action.ilike(needle),
                    AuditEventModel.resource_type.ilike(needle),
                    AuditEventModel.resource_id.ilike(needle),
                    AuditEventModel.user_name.ilike(needle),
                    AuditEventModel.user_email.ilike(needle),
                    details_text.ilike(needle),
                )
            )
        order = (
            AuditEventModel.created_at.asc()
            if sort.lower() == "asc"
            else AuditEventModel.created_at.desc()
        )
        statement = statement.order_by(order).offset((page - 1) * page_size).limit(page_size)
        return list(self.db.scalars(statement))

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
