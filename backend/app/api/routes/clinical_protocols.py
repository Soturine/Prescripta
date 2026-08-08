from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_any_capability
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import Capability
from app.schemas.clinical_protocol_schema import (
    InstitutionalClinicalProtocolCreate,
    InstitutionalClinicalProtocolRead,
    InstitutionalClinicalProtocolVersionCreate,
    InstitutionalClinicalProtocolVersionRead,
    ProtocolVersionDetailRead,
    ProtocolVersionReviewRequest,
)
from app.services.institutional_protocol_service import (
    InstitutionalClinicalProtocolService,
    InstitutionalProtocolError,
)

router = APIRouter(prefix="/clinical-protocols", tags=["clinical-protocols"])
DbSession = Annotated[Session, Depends(get_db)]
ProtocolReader = Annotated[
    UserModel,
    Depends(
        require_any_capability(
            Capability.CLINICAL_PROTOCOL_READ,
            Capability.CLINICAL_PROTOCOL_MANAGE,
            Capability.CLINICAL_PROTOCOL_REVIEW,
        )
    ),
]
ProtocolManager = Annotated[
    UserModel, Depends(require_any_capability(Capability.CLINICAL_PROTOCOL_MANAGE))
]
ProtocolReviewer = Annotated[
    UserModel, Depends(require_any_capability(Capability.CLINICAL_PROTOCOL_REVIEW))
]


def _unprocessable(exc: InstitutionalProtocolError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))


@router.post(
    "",
    response_model=InstitutionalClinicalProtocolRead,
    status_code=status.HTTP_201_CREATED,
)
def create_protocol(
    payload: InstitutionalClinicalProtocolCreate,
    db: DbSession,
    current_user: ProtocolManager,
) -> InstitutionalClinicalProtocolRead:
    try:
        return InstitutionalClinicalProtocolService(db).create_protocol(
            payload, current_user
        )
    except InstitutionalProtocolError as exc:
        raise _unprocessable(exc) from exc


@router.get("", response_model=list[InstitutionalClinicalProtocolRead])
def list_protocols(
    db: DbSession,
    current_user: ProtocolReader,
) -> list[InstitutionalClinicalProtocolRead]:
    return InstitutionalClinicalProtocolService(db).list_protocols(current_user)


@router.post(
    "/{protocol_id}/versions",
    response_model=InstitutionalClinicalProtocolVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_version(
    protocol_id: int,
    payload: InstitutionalClinicalProtocolVersionCreate,
    db: DbSession,
    current_user: ProtocolManager,
) -> InstitutionalClinicalProtocolVersionRead:
    try:
        return InstitutionalClinicalProtocolService(db).create_version(
            protocol_id, payload, current_user
        )
    except InstitutionalProtocolError as exc:
        raise _unprocessable(exc) from exc


@router.get("/versions/{version_id}", response_model=ProtocolVersionDetailRead)
def version_detail(
    version_id: int,
    db: DbSession,
    current_user: ProtocolReader,
) -> ProtocolVersionDetailRead:
    try:
        detail = InstitutionalClinicalProtocolService(db).version_detail(
            version_id, current_user
        )
        return ProtocolVersionDetailRead.model_validate(detail)
    except InstitutionalProtocolError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/versions/{version_id}/review",
    response_model=InstitutionalClinicalProtocolVersionRead,
)
def review_version(
    version_id: int,
    payload: ProtocolVersionReviewRequest,
    db: DbSession,
    current_user: ProtocolReviewer,
) -> InstitutionalClinicalProtocolVersionRead:
    try:
        return InstitutionalClinicalProtocolService(db).review_version(
            version_id, payload, current_user
        )
    except InstitutionalProtocolError as exc:
        raise _unprocessable(exc) from exc
