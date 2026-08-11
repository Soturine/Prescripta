from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_any_capability
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import Capability
from app.schemas.terminology_schema import (
    TerminologyConceptPage,
    TerminologyDriftRead,
    TerminologyImportRead,
    TerminologyImportRequest,
    TerminologyMappingCreate,
    TerminologyMappingRead,
    TerminologyMappingReview,
    TerminologyReleaseCreate,
    TerminologyReleaseRead,
    TerminologySourceCreate,
    TerminologySourceRead,
)
from app.services.terminology_registry_service import (
    TerminologyError,
    TerminologyRegistryService,
)

router = APIRouter(prefix="/terminology", tags=["terminology"])
DbSession = Annotated[Session, Depends(get_db)]
Reader = Annotated[
    UserModel, Depends(require_any_capability(Capability.TERMINOLOGY_READ))
]
Manager = Annotated[
    UserModel, Depends(require_any_capability(Capability.TERMINOLOGY_MANAGE))
]
Proposer = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.TERMINOLOGY_MAPPING_PROPOSE)),
]
Reviewer = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.TERMINOLOGY_MAPPING_REVIEW)),
]


def _error(exc: TerminologyError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))


@router.post("/sources", response_model=TerminologySourceRead, status_code=201)
def create_source(
    payload: TerminologySourceCreate, db: DbSession, current_user: Manager
) -> TerminologySourceRead:
    try:
        return TerminologyRegistryService(db).create_source(payload, current_user)
    except TerminologyError as exc:
        raise _error(exc) from exc


@router.get("/sources", response_model=list[TerminologySourceRead])
def list_sources(db: DbSession, current_user: Reader) -> list[TerminologySourceRead]:
    return TerminologyRegistryService(db).list_sources(current_user)


@router.post(
    "/sources/{source_id}/releases",
    response_model=TerminologyReleaseRead,
    status_code=201,
)
def create_release(
    source_id: str,
    payload: TerminologyReleaseCreate,
    db: DbSession,
    current_user: Manager,
) -> TerminologyReleaseRead:
    try:
        return TerminologyRegistryService(db).create_release(source_id, payload, current_user)
    except TerminologyError as exc:
        raise _error(exc) from exc


@router.get("/releases", response_model=list[TerminologyReleaseRead])
def list_releases(
    db: DbSession, current_user: Reader, source_id: str | None = None
) -> list[TerminologyReleaseRead]:
    return TerminologyRegistryService(db).list_releases(current_user, source_id)


@router.post("/releases/{release_id}/import", response_model=TerminologyImportRead)
def import_release(
    release_id: str,
    payload: TerminologyImportRequest,
    db: DbSession,
    current_user: Manager,
) -> TerminologyImportRead:
    try:
        return TerminologyRegistryService(db).import_bundle(release_id, payload, current_user)
    except TerminologyError as exc:
        raise _error(exc) from exc


@router.get("/concepts", response_model=TerminologyConceptPage)
def search_concepts(
    db: DbSession,
    current_user: Reader,
    query: Annotated[str, Query(max_length=160)] = "",
    release_id: str | None = None,
    domain: Annotated[str | None, Query(max_length=80)] = None,
    standard_status: Annotated[str | None, Query(max_length=40)] = None,
    active_only: bool = False,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> TerminologyConceptPage:
    try:
        return TerminologyConceptPage.model_validate(
            TerminologyRegistryService(db).search(
                current_user,
                query=query,
                release_id=release_id,
                domain=domain,
                standard_status=standard_status,
                active_only=active_only,
                offset=offset,
                limit=limit,
            )
        )
    except TerminologyError as exc:
        raise _error(exc) from exc


@router.post("/mappings", response_model=TerminologyMappingRead, status_code=201)
def propose_mapping(
    payload: TerminologyMappingCreate, db: DbSession, current_user: Proposer
) -> TerminologyMappingRead:
    try:
        return TerminologyRegistryService(db).propose_mapping(payload, current_user)
    except TerminologyError as exc:
        raise _error(exc) from exc


@router.get("/mappings", response_model=list[TerminologyMappingRead])
def list_mappings(
    db: DbSession, current_user: Reader, mapping_status: str | None = None
) -> list[TerminologyMappingRead]:
    return TerminologyRegistryService(db).list_mappings(
        current_user, status=mapping_status
    )


@router.post("/mappings/{mapping_id}/review", response_model=TerminologyMappingRead)
def review_mapping(
    mapping_id: str,
    payload: TerminologyMappingReview,
    db: DbSession,
    current_user: Reviewer,
) -> TerminologyMappingRead:
    try:
        return TerminologyRegistryService(db).review_mapping(
            mapping_id, payload, current_user
        )
    except TerminologyError as exc:
        raise _error(exc) from exc


@router.get("/drift", response_model=TerminologyDriftRead)
def terminology_drift(
    source_release_id: str,
    target_release_id: str,
    db: DbSession,
    current_user: Reader,
) -> TerminologyDriftRead:
    try:
        return TerminologyDriftRead.model_validate(
            TerminologyRegistryService(db).drift(
                source_release_id, target_release_id, current_user
            )
        )
    except TerminologyError as exc:
        raise _error(exc) from exc
