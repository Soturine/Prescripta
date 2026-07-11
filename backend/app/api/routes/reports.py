from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.reports.audit import decision_timeline, evidence_view
from app.reports.schemas import GeneratedReportRead, ReportMode, ReportPreview
from app.reports.service import ReportNotFoundError, ReportService
from app.repositories.audit_repository import AuditRepository

router = APIRouter(prefix="/reports", tags=["reports"])
DbSession = Annotated[Session, Depends(get_db)]
ReportReader = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM, UserRole.AUDITOR)),
]
ReportManager = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO))]
PatientGuidanceManager = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM)),
]
AuditReportManager = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.AUDITOR))]


@router.get("", response_model=list[GeneratedReportRead])
def list_reports(
    db: DbSession,
    _current_user: ReportReader,
    report_type: str | None = None,
    target_type: str | None = None,
) -> list[GeneratedReportRead]:
    return ReportService(db).list_reports(report_type=report_type, target_type=target_type)


@router.get("/prescriptions/{audit_id}/preview", response_model=ReportPreview)
def prescription_report_preview(
    audit_id: int,
    db: DbSession,
    _current_user: ReportReader,
    mode: ReportMode = "complete_internal",
) -> ReportPreview:
    try:
        return ReportService(db).prescription_preview(audit_id, mode=mode)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/prescriptions/{audit_id}/pdf")
def prescription_report_pdf(
    audit_id: int,
    db: DbSession,
    current_user: ReportManager,
    mode: ReportMode = "complete_internal",
) -> Response:
    try:
        content, report = ReportService(db).generate_prescription_pdf(
            audit_id,
            user=current_user,
            mode=mode,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _pdf_response(content, f"prescripta-relatorio-tecnico-{report.id}.pdf")


@router.get("/prescriptions/{audit_id}/patient-guidance.pdf")
def patient_guidance_pdf(
    audit_id: int,
    db: DbSession,
    current_user: PatientGuidanceManager,
) -> Response:
    try:
        content, report = ReportService(db).generate_patient_guidance_pdf(
            audit_id,
            user=current_user,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _pdf_response(content, f"prescripta-orientacoes-paciente-{report.id}.pdf")


@router.get("/prescriptions/{audit_id}/timeline")
def prescription_timeline(audit_id: int, db: DbSession, _current_user: ReportReader) -> list[dict]:
    try:
        bundle = ReportService(db).prescription_bundle(audit_id)
        return decision_timeline(bundle)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/prescriptions/{audit_id}/evidence")
def prescription_evidence(audit_id: int, db: DbSession, _current_user: ReportReader) -> list[dict]:
    try:
        bundle = ReportService(db).prescription_bundle(audit_id)
        return evidence_view(bundle)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/protocol-runs/{run_id}/preview", response_model=ReportPreview)
def protocol_run_report_preview(
    run_id: int,
    db: DbSession,
    _current_user: ReportReader,
) -> ReportPreview:
    try:
        return ReportService(db).protocol_run_preview(run_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/protocol-runs/{run_id}/pdf")
def protocol_run_report_pdf(
    run_id: int,
    db: DbSession,
    current_user: ReportManager,
) -> Response:
    try:
        content, report = ReportService(db).generate_protocol_run_pdf(run_id, user=current_user)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _pdf_response(content, f"prescripta-protocolo-{run_id}-relatorio-{report.id}.pdf")


@router.get("/imports/{import_id}/reconciliation.pdf")
def reconciliation_report_pdf(
    import_id: int,
    db: DbSession,
    current_user: ReportManager,
    anonymized: bool = False,
) -> Response:
    try:
        content, report = ReportService(db).generate_reconciliation_pdf(
            import_id,
            user=current_user,
            anonymized=anonymized,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _pdf_response(content, f"prescripta-reconciliacao-{report.id}.pdf")


@router.get("/audit-events/pdf")
def audit_report_pdf(
    db: DbSession,
    current_user: AuditReportManager,
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
    source: str | None = None,
    jurisdiction: str | None = None,
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
        source=source,
        jurisdiction=jurisdiction,
        action=action,
        date_from=date_from,
        date_to=date_to,
        text=text,
    )
    events = AuditRepository(db).list_filtered(**filters, page_size=500)
    content, report = ReportService(db).generate_audit_pdf(
        events,
        filters=filters,
        user=current_user,
    )
    return _pdf_response(content, f"prescripta-auditoria-{report.id}.pdf")


@router.get("/{report_id}", response_model=GeneratedReportRead)
def get_report(report_id: int, db: DbSession, _current_user: ReportReader) -> GeneratedReportRead:
    report = ReportService(db).get_report(report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relatorio nao encontrado.",
        )
    return report


def _pdf_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _audit_filters(**kwargs) -> dict:
    return {key: value for key, value in kwargs.items() if value is not None}
