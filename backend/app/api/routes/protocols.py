from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.reports.pdf_renderer import SimplePDFRenderer
from app.schemas.protocol_schema import (
    EmergencyProtocolRead,
    ProtocolEvidenceRead,
    ProtocolExplainRequest,
    ProtocolExplainResponse,
    ProtocolReportPreview,
    ProtocolRunRequest,
    ProtocolRunResponse,
)
from app.services.emergency_protocol_service import (
    EmergencyProtocolService,
    ProtocolNotFoundError,
    ProtocolValidationError,
)

router = APIRouter(prefix="/protocols", tags=["protocols"])
DbSession = Annotated[Session, Depends(get_db)]
ProtocolReader = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM, UserRole.AUDITOR)),
]
ProtocolRunner = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM)),
]


@router.get("", response_model=list[EmergencyProtocolRead])
def list_protocols(
    db: DbSession,
    _current_user: ProtocolReader,
    category: str | None = None,
) -> list[EmergencyProtocolRead]:
    return EmergencyProtocolService(db).list_protocols(category=category)


@router.get("/{protocol_id}", response_model=EmergencyProtocolRead)
def get_protocol(
    protocol_id: str,
    db: DbSession,
    _current_user: ProtocolReader,
) -> EmergencyProtocolRead:
    try:
        return EmergencyProtocolService(db).get_protocol(protocol_id)
    except ProtocolNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{protocol_id}/run", response_model=ProtocolRunResponse)
def run_protocol(
    protocol_id: str,
    payload: ProtocolRunRequest,
    db: DbSession,
    current_user: ProtocolRunner,
) -> ProtocolRunResponse:
    try:
        return EmergencyProtocolService(db).run(protocol_id, payload, current_user)
    except ProtocolNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProtocolValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/{protocol_id}/explain", response_model=ProtocolExplainResponse)
def explain_protocol(
    protocol_id: str,
    payload: ProtocolExplainRequest,
    db: DbSession,
    current_user: ProtocolRunner,
) -> ProtocolExplainResponse:
    try:
        return EmergencyProtocolService(db).explain(
            protocol_id,
            payload.context,
            user=current_user,
            run_id=payload.run_id,
            question=payload.question,
        )
    except ProtocolNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{protocol_id}/report", response_model=ProtocolReportPreview)
def protocol_report(
    protocol_id: str,
    db: DbSession,
    _current_user: ProtocolReader,
    run_id: int | None = Query(default=None, gt=0),
) -> ProtocolReportPreview:
    try:
        return EmergencyProtocolService(db).report(protocol_id, run_id=run_id)
    except ProtocolNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProtocolValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("/{protocol_id}/report.pdf")
def protocol_report_pdf(
    protocol_id: str,
    db: DbSession,
    _current_user: ProtocolReader,
    run_id: int | None = Query(default=None, gt=0),
) -> Response:
    try:
        preview = EmergencyProtocolService(db).report(protocol_id, run_id=run_id)
    except ProtocolNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProtocolValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    pdf = SimplePDFRenderer().render(preview.report_lines)
    return _download(pdf, "application/pdf", f"prescripta-protocolo-{protocol_id}.pdf")


@router.get("/{protocol_id}/evidence", response_model=list[ProtocolEvidenceRead])
def protocol_evidence(
    protocol_id: str,
    db: DbSession,
    _current_user: ProtocolReader,
) -> list[ProtocolEvidenceRead]:
    try:
        return EmergencyProtocolService(db).evidence(protocol_id)
    except ProtocolNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{protocol_id}/events/{run_id}.json")
def protocol_event_json(
    protocol_id: str,
    run_id: int,
    db: DbSession,
    _current_user: ProtocolReader,
) -> Response:
    try:
        content = EmergencyProtocolService(db).export_event_json(protocol_id, run_id)
    except ProtocolNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProtocolValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return _download(content, "application/json", f"protocolo-{protocol_id}-{run_id}.json")


@router.get("/{protocol_id}/events/{run_id}.csv")
def protocol_event_csv(
    protocol_id: str,
    run_id: int,
    db: DbSession,
    _current_user: ProtocolReader,
) -> Response:
    try:
        content = EmergencyProtocolService(db).export_event_csv(protocol_id, run_id)
    except ProtocolNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProtocolValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return _download(content, "text/csv; charset=utf-8", f"protocolo-{protocol_id}-{run_id}.csv")


def _download(content: bytes, media_type: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
