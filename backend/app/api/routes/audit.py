from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.reports.audit import decision_timeline, evidence_view
from app.reports.service import ReportNotFoundError, ReportService
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit_schema import AuditPage, AuditRead

router = APIRouter(prefix="/audit", tags=["audit"])
DbSession = Annotated[Session, Depends(get_db)]
AuditReader = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.AUDITOR))]


@router.get("", response_model=AuditPage)
def list_audit(
    db: DbSession,
    _current_user: AuditReader,
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
    status_filter: str | None = Query(default=None, alias="status"),
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
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
) -> AuditPage:
    items, total = AuditRepository(db).list_filtered(
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
        status=status_filter,
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
        sort=sort,
        page=page,
        page_size=page_size,
        include_total=True,
    )
    total_pages = (total + page_size - 1) // page_size
    return AuditPage(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.get("/{event_id}", response_model=AuditRead)
def get_audit_event(event_id: int, db: DbSession, _current_user: AuditReader) -> AuditRead:
    event = AuditRepository(db).get_event(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
    return event


@router.get("/{event_id}/timeline")
def get_audit_timeline(event_id: int, db: DbSession, _current_user: AuditReader) -> list[dict]:
    event = AuditRepository(db).get_event(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
    if event.resource_type == "prescription" and event.resource_id:
        try:
            bundle = ReportService(db).prescription_bundle(int(event.resource_id))
            return decision_timeline(bundle)
        except (ValueError, ReportNotFoundError):
            pass
    if event.resource_type == "protocol_run" and event.resource_id:
        try:
            preview = ReportService(db).protocol_run_preview(int(event.resource_id))
            return preview.timeline
        except (ValueError, ReportNotFoundError):
            pass
    return [
        {
            "order": 1,
            "title": "Evento registrado",
            "status": event.action,
            "at": event.created_at.isoformat(),
            "details": event.details,
        }
    ]


@router.get("/{event_id}/evidence")
def get_audit_evidence(event_id: int, db: DbSession, _current_user: AuditReader) -> list[dict]:
    event = AuditRepository(db).get_event(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
    if event.resource_type == "prescription" and event.resource_id:
        try:
            bundle = ReportService(db).prescription_bundle(int(event.resource_id))
            return evidence_view(bundle)
        except (ValueError, ReportNotFoundError):
            pass
    if event.resource_type == "protocol_run" and event.resource_id:
        try:
            preview = ReportService(db).protocol_run_preview(int(event.resource_id))
            return preview.evidence
        except (ValueError, ReportNotFoundError):
            pass
    return []
