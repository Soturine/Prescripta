from __future__ import annotations

from datetime import datetime
from typing import Any

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
        events = self.list()
        filtered = [
            event
            for event in events
            if self._matches(
                event,
                user=user,
                user_role=user_role,
                patient=patient,
                medication=medication,
                active_ingredient=active_ingredient,
                protocol=protocol,
                protocol_category=protocol_category,
                protocol_severity=protocol_severity,
                protocol_version=protocol_version,
                execution=execution,
                report_type=report_type,
                action=action,
                resource_type=resource_type,
                risk_level=risk_level,
                status=status,
                severity=severity,
                ai_provider=ai_provider,
                ai_model=ai_model,
                fallback_used=fallback_used,
                source=source,
                jurisdiction=jurisdiction,
                specialty=specialty,
                policy_type=policy_type,
                policy_strength=policy_strength,
                dose_rule_id=dose_rule_id,
                psychotropic_signal_code=psychotropic_signal_code,
                prescriber_policy_status=prescriber_policy_status,
                credential_verification_status=credential_verification_status,
                high_alert_category=high_alert_category,
                date_from=date_from,
                date_to=date_to,
                text=text,
            )
        ]
        reverse = sort.lower() != "asc"
        filtered.sort(key=lambda event: event.created_at, reverse=reverse)
        start = max(page - 1, 0) * page_size
        end = start + page_size
        return filtered[start:end]

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

    def _matches(self, event: AuditEventModel, **filters: Any) -> bool:
        if filters["date_from"] and event.created_at < filters["date_from"]:
            return False
        if filters["date_to"] and event.created_at > filters["date_to"]:
            return False
        direct = {
            "user_role": event.user_role,
            "action": event.action,
            "resource_type": event.resource_type,
            "risk_level": event.risk_level,
            "status": event.status,
        }
        for key, value in direct.items():
            expected = filters.get(key)
            if expected and str(expected).lower() not in str(value or "").lower():
                return False
        if filters["user"]:
            needle = str(filters["user"]).lower()
            haystack = (
                f"{event.user_name or ''} {event.user_email or ''} {event.user_id or ''}"
            ).lower()
            if needle not in haystack:
                return False
        detail_text = self._details_text(event.details or {})
        detail_filters = {
            "patient": filters["patient"],
            "medication": filters["medication"],
            "active_ingredient": filters["active_ingredient"],
            "protocol": filters["protocol"],
            "protocol_category": filters["protocol_category"],
            "protocol_severity": filters["protocol_severity"],
            "protocol_version": filters["protocol_version"],
            "execution": filters["execution"],
            "report_type": filters["report_type"],
            "severity": filters["severity"],
            "ai_provider": filters["ai_provider"],
            "ai_model": filters["ai_model"],
            "source": filters["source"],
            "jurisdiction": filters["jurisdiction"],
            "specialty": filters["specialty"],
            "policy_type": filters["policy_type"],
            "policy_strength": filters["policy_strength"],
            "dose_rule_id": filters["dose_rule_id"],
            "psychotropic_signal_code": filters["psychotropic_signal_code"],
            "prescriber_policy_status": filters["prescriber_policy_status"],
            "credential_verification_status": filters["credential_verification_status"],
            "high_alert_category": filters["high_alert_category"],
        }
        for expected in detail_filters.values():
            if expected and str(expected).lower() not in detail_text:
                return False
        if filters["fallback_used"] is not None:
            expected_bool = bool(filters["fallback_used"])
            fallback_text = str((event.details or {}).get("fallback_used", "")).lower()
            if fallback_text not in {str(expected_bool).lower(), str(int(expected_bool))}:
                return False
        if filters["text"]:
            needle = str(filters["text"]).lower()
            haystack = (
                f"{event.action} {event.resource_type} {event.resource_id or ''} "
                f"{event.user_name or ''} {event.user_email or ''} {detail_text}"
            ).lower()
            if needle not in haystack:
                return False
        return True

    def _details_text(self, value: Any) -> str:
        if isinstance(value, dict):
            return " ".join(
                f"{key} {self._details_text(item)}" for key, item in value.items()
            ).lower()
        if isinstance(value, list):
            return " ".join(self._details_text(item) for item in value).lower()
        return str(value or "").lower()
