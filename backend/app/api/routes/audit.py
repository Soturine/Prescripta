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
from app.schemas.audit_schema import AuditRead

router = APIRouter(prefix="/audit", tags=["audit"])
DbSession = Annotated[Session, Depends(get_db)]
AuditReader = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.AUDITOR))]


@router.get("", response_model=list[AuditRead])
def list_audit(
    db: DbSession,
    _current_user: AuditReader,
    user: str | None = None,
    user_role: str | None = None,
    patient: str | None = None,
    medication: str | None = None,
    active_ingredient: str | None = None,
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
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    text: str | None = None,
    sort: str = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
) -> list[AuditRead]:
    return AuditRepository(db).list_filtered(
        user=user,
        user_role=user_role,
        patient=patient,
        medication=medication,
        active_ingredient=active_ingredient,
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
        date_from=date_from,
        date_to=date_to,
        text=text,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/{event_id}", response_model=AuditRead)
def get_audit_event(event_id: int, db: DbSession, _current_user: AuditReader) -> AuditRead:
    event = AuditRepository(db).get_event(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento nao encontrado.")
    return event


@router.get("/{event_id}/timeline")
def get_audit_timeline(event_id: int, db: DbSession, _current_user: AuditReader) -> list[dict]:
    event = AuditRepository(db).get_event(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento nao encontrado.")
    if event.resource_type == "prescription" and event.resource_id:
        try:
            bundle = ReportService(db).prescription_bundle(int(event.resource_id))
            return decision_timeline(bundle)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento nao encontrado.")
    if event.resource_type == "prescription" and event.resource_id:
        try:
            bundle = ReportService(db).prescription_bundle(int(event.resource_id))
            return evidence_view(bundle)
        except (ValueError, ReportNotFoundError):
            pass
    return []
