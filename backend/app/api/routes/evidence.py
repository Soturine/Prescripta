from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_any_capability
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import Capability
from app.schemas.evidence_schema import (
    EvidenceLinkCreate,
    EvidenceLinkRead,
    EvidenceSourceCreate,
    EvidenceSourceRead,
)
from app.services.evidence_service import EvidenceError, EvidenceService

router = APIRouter(prefix="/evidence", tags=["evidence"])
DbSession = Annotated[Session, Depends(get_db)]
EvidenceReader = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.EVIDENCE_READ, Capability.EVIDENCE_WRITE)),
]
EvidenceWriter = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.EVIDENCE_WRITE)),
]


@router.post(
    "/sources",
    response_model=EvidenceSourceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_source(
    payload: EvidenceSourceCreate,
    db: DbSession,
    current_user: EvidenceWriter,
) -> EvidenceSourceRead:
    try:
        return EvidenceService(db).create_source(payload, current_user)
    except EvidenceError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/sources", response_model=list[EvidenceSourceRead])
def list_sources(
    db: DbSession,
    current_user: EvidenceReader,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[EvidenceSourceRead]:
    return EvidenceService(db).list_sources(current_user, offset=offset, limit=limit)


@router.post(
    "/links",
    response_model=EvidenceLinkRead,
    status_code=status.HTTP_201_CREATED,
)
def create_link(
    payload: EvidenceLinkCreate,
    db: DbSession,
    current_user: EvidenceWriter,
) -> EvidenceLinkRead:
    try:
        return EvidenceService(db).create_link(payload, current_user)
    except EvidenceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/links", response_model=list[EvidenceLinkRead])
def list_links(
    db: DbSession,
    current_user: EvidenceReader,
    target_type: str | None = None,
    target_id: str | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[EvidenceLinkRead]:
    return EvidenceService(db).links(
        current_user,
        target_type=target_type,
        target_id=target_id,
        offset=offset,
        limit=limit,
    )
