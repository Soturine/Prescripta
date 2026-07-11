from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.reports.service import ReportNotFoundError, ReportService
from app.repositories.audit_repository import AuditRepository

router = APIRouter(prefix="/exports", tags=["exports"])
DbSession = Annotated[Session, Depends(get_db)]
ClinicalExporter = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.AUDITOR)),
]
AuditExporter = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.AUDITOR))]


@router.get("/prescriptions/{audit_id}.json")
def export_prescription_json(
    audit_id: int,
    db: DbSession,
    current_user: ClinicalExporter,
    anonymized: bool = False,
) -> Response:
    try:
        content = ReportService(db).export_prescription_json(
            audit_id,
            user=current_user,
            anonymized=anonymized,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _download(content, "application/json", f"prescricao-{audit_id}.json")


@router.get("/prescriptions/{audit_id}.csv")
def export_prescription_csv(
    audit_id: int,
    db: DbSession,
    current_user: ClinicalExporter,
    anonymized: bool = False,
) -> Response:
    try:
        content = ReportService(db).export_prescription_csv(
            audit_id,
            user=current_user,
            anonymized=anonymized,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _download(content, "text/csv; charset=utf-8", f"prescricao-{audit_id}.csv")


@router.get("/imports/{import_id}.json")
def export_import_json(
    import_id: int,
    db: DbSession,
    current_user: ClinicalExporter,
    anonymized: bool = False,
) -> Response:
    try:
        content = ReportService(db).export_import_json(
            import_id,
            user=current_user,
            anonymized=anonymized,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _download(content, "application/json", f"importacao-{import_id}.json")


@router.get("/imports/{import_id}.csv")
def export_import_csv(
    import_id: int,
    db: DbSession,
    current_user: ClinicalExporter,
    anonymized: bool = False,
) -> Response:
    try:
        content = ReportService(db).export_import_csv(
            import_id,
            user=current_user,
            anonymized=anonymized,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _download(content, "text/csv; charset=utf-8", f"importacao-{import_id}.csv")


@router.get("/audit-events.json")
def export_audit_json(
    db: DbSession,
    current_user: AuditExporter,
    user: str | None = None,
    patient: str | None = None,
    medication: str | None = None,
    protocol: str | None = None,
    protocol_category: str | None = None,
    protocol_severity: str | None = None,
    protocol_version: str | None = None,
    execution: str | None = None,
    report_type: str | None = None,
    risk_level: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    ai_provider: str | None = None,
    ai_model: str | None = None,
    action: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    text: str | None = None,
) -> Response:
    filters = _audit_filters(
        user=user,
        patient=patient,
        medication=medication,
        protocol=protocol,
        protocol_category=protocol_category,
        protocol_severity=protocol_severity,
        protocol_version=protocol_version,
        execution=execution,
        report_type=report_type,
        risk_level=risk_level,
        status=status_filter,
        ai_provider=ai_provider,
        ai_model=ai_model,
        action=action,
        date_from=date_from,
        date_to=date_to,
        text=text,
    )
    events = AuditRepository(db).list_filtered(**filters, page_size=500)
    content = ReportService(db).export_audit_json(events, filters=filters, user=current_user)
    return _download(content, "application/json", "audit-events.json")


@router.get("/audit-events.csv")
def export_audit_csv(
    db: DbSession,
    current_user: AuditExporter,
    user: str | None = None,
    patient: str | None = None,
    medication: str | None = None,
    protocol: str | None = None,
    protocol_category: str | None = None,
    protocol_severity: str | None = None,
    protocol_version: str | None = None,
    execution: str | None = None,
    report_type: str | None = None,
    risk_level: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    ai_provider: str | None = None,
    ai_model: str | None = None,
    action: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    text: str | None = None,
) -> Response:
    filters = _audit_filters(
        user=user,
        patient=patient,
        medication=medication,
        protocol=protocol,
        protocol_category=protocol_category,
        protocol_severity=protocol_severity,
        protocol_version=protocol_version,
        execution=execution,
        report_type=report_type,
        risk_level=risk_level,
        status=status_filter,
        ai_provider=ai_provider,
        ai_model=ai_model,
        action=action,
        date_from=date_from,
        date_to=date_to,
        text=text,
    )
    events = AuditRepository(db).list_filtered(**filters, page_size=500)
    content = ReportService(db).export_audit_csv(events, filters=filters, user=current_user)
    return _download(content, "text/csv; charset=utf-8", "audit-events.csv")


@router.get("/reports/{report_id}.json")
def export_generated_report_json(
    report_id: int,
    db: DbSession,
    current_user: ClinicalExporter,
) -> Response:
    try:
        content = ReportService(db).export_report_json(report_id, user=current_user)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _download(content, "application/json", f"relatorio-{report_id}.json")


def _download(content: bytes, media_type: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _audit_filters(**kwargs) -> dict:
    return {key: value for key, value in kwargs.items() if value is not None}
