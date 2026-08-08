from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_any_capability
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import Capability
from app.schemas.research_schema import (
    CohortDefinitionCreate,
    CohortReviewRequest,
    CohortRunRead,
    CohortRunRequest,
    CohortVersionRead,
    ConceptSetCreate,
    ConceptSetRead,
    ConceptSetReviewRequest,
    ConceptSetVersionRead,
    OutcomeDefinitionCreate,
    OutcomeDefinitionRead,
    ResearchReviewRequest,
    ResearchSnapshotRead,
    ResearchStudyCreate,
    ResearchStudyRead,
    ResearchWorkspaceRead,
    StudyProtocolVersionCreate,
    StudyProtocolVersionRead,
)
from app.services.research_service import (
    ResearchConflict,
    ResearchError,
    ResearchNotFound,
    ResearchService,
)

router = APIRouter(prefix="/research", tags=["research"])
DbSession = Annotated[Session, Depends(get_db)]
StudyReader = Annotated[
    UserModel,
    Depends(
        require_any_capability(
            Capability.RESEARCH_STUDY_READ,
            Capability.RESEARCH_STUDY_WRITE,
            Capability.RESEARCH_STUDY_REVIEW,
        )
    ),
]
StudyCreator = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.RESEARCH_STUDY_CREATE)),
]
StudyWriter = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.RESEARCH_STUDY_WRITE)),
]
StudyReviewer = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.RESEARCH_STUDY_REVIEW)),
]
ConceptReader = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.RESEARCH_CONCEPT_SET_READ)),
]
ConceptWriter = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.RESEARCH_CONCEPT_SET_WRITE)),
]
CohortReader = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.RESEARCH_COHORT_READ)),
]
CohortWriter = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.RESEARCH_COHORT_WRITE)),
]
CohortExecutor = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.RESEARCH_COHORT_EXECUTE)),
]


def _research_http_error(exc: ResearchError) -> HTTPException:
    if isinstance(exc, ResearchNotFound):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ResearchConflict):
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_422_UNPROCESSABLE_CONTENT
    return HTTPException(status_code=code, detail=str(exc))


@router.get("/workspace", response_model=ResearchWorkspaceRead)
def workspace(db: DbSession, current_user: StudyReader) -> ResearchWorkspaceRead:
    return ResearchWorkspaceRead.model_validate(ResearchService(db).workspace(current_user))


@router.post(
    "/studies",
    response_model=ResearchStudyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_study(
    payload: ResearchStudyCreate,
    db: DbSession,
    current_user: StudyCreator,
) -> ResearchStudyRead:
    try:
        return ResearchService(db).create_study(payload, current_user)
    except ResearchError as exc:
        raise _research_http_error(exc) from exc


@router.get("/studies", response_model=list[ResearchStudyRead])
def list_studies(
    db: DbSession,
    current_user: StudyReader,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ResearchStudyRead]:
    return ResearchService(db).list_studies(
        current_user,
        offset=offset,
        limit=limit,
    )


@router.get("/studies/{study_id}", response_model=ResearchStudyRead)
def study_detail(
    study_id: str,
    db: DbSession,
    current_user: StudyReader,
) -> ResearchStudyRead:
    try:
        return ResearchService(db).study(study_id, current_user)
    except ResearchError as exc:
        raise _research_http_error(exc) from exc


@router.post(
    "/studies/{study_id}/protocol-versions",
    response_model=StudyProtocolVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_protocol_version(
    study_id: str,
    payload: StudyProtocolVersionCreate,
    db: DbSession,
    current_user: StudyWriter,
) -> StudyProtocolVersionRead:
    try:
        return ResearchService(db).create_protocol_version(study_id, payload, current_user)
    except ResearchError as exc:
        raise _research_http_error(exc) from exc


@router.post(
    "/protocol-versions/{version_id}/review",
    response_model=StudyProtocolVersionRead,
)
def review_protocol_version(
    version_id: str,
    payload: ResearchReviewRequest,
    db: DbSession,
    current_user: StudyReviewer,
) -> StudyProtocolVersionRead:
    try:
        return ResearchService(db).review_protocol(version_id, payload, current_user)
    except ResearchError as exc:
        raise _research_http_error(exc) from exc


@router.post(
    "/concept-sets",
    response_model=ConceptSetRead,
    status_code=status.HTTP_201_CREATED,
)
def create_concept_set(
    payload: ConceptSetCreate,
    db: DbSession,
    current_user: ConceptWriter,
) -> ConceptSetRead:
    try:
        return ConceptSetRead.model_validate(
            ResearchService(db).create_concept_set(payload, current_user)
        )
    except ResearchError as exc:
        raise _research_http_error(exc) from exc


@router.get("/concept-sets", response_model=list[ConceptSetRead])
def list_concept_sets(
    db: DbSession,
    current_user: ConceptReader,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ConceptSetRead]:
    return [
        ConceptSetRead.model_validate(item)
        for item in ResearchService(db).list_concept_sets(
            current_user,
            offset=offset,
            limit=limit,
        )
    ]


@router.post(
    "/concept-set-versions/{version_id}/review",
    response_model=ConceptSetVersionRead,
)
def review_concept_set(
    version_id: str,
    payload: ConceptSetReviewRequest,
    db: DbSession,
    current_user: StudyReviewer,
) -> ConceptSetVersionRead:
    try:
        return ResearchService(db).review_concept_set(version_id, payload, current_user)
    except ResearchError as exc:
        raise _research_http_error(exc) from exc


@router.post(
    "/studies/{study_id}/cohorts",
    response_model=CohortVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_cohort_version(
    study_id: str,
    payload: CohortDefinitionCreate,
    db: DbSession,
    current_user: CohortWriter,
) -> CohortVersionRead:
    try:
        return ResearchService(db).create_cohort_version(study_id, payload, current_user)
    except ResearchError as exc:
        raise _research_http_error(exc) from exc


@router.post(
    "/cohort-versions/{version_id}/review",
    response_model=CohortVersionRead,
)
def review_cohort_version(
    version_id: str,
    payload: CohortReviewRequest,
    db: DbSession,
    current_user: StudyReviewer,
) -> CohortVersionRead:
    try:
        return ResearchService(db).review_cohort(version_id, payload, current_user)
    except ResearchError as exc:
        raise _research_http_error(exc) from exc


@router.post(
    "/studies/{study_id}/outcomes",
    response_model=OutcomeDefinitionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_outcome(
    study_id: str,
    payload: OutcomeDefinitionCreate,
    db: DbSession,
    current_user: StudyWriter,
) -> OutcomeDefinitionRead:
    try:
        return ResearchService(db).create_outcome(study_id, payload, current_user)
    except ResearchError as exc:
        raise _research_http_error(exc) from exc


@router.post(
    "/cohort-versions/{version_id}/runs",
    response_model=CohortRunRead,
    status_code=status.HTTP_201_CREATED,
)
def execute_cohort(
    version_id: str,
    payload: CohortRunRequest,
    db: DbSession,
    current_user: CohortExecutor,
) -> CohortRunRead:
    try:
        return ResearchService(db).execute_cohort(version_id, payload, current_user)
    except ResearchError as exc:
        raise _research_http_error(exc) from exc


@router.get("/runs", response_model=list[CohortRunRead])
def list_runs(
    db: DbSession,
    current_user: CohortReader,
    study_id: Annotated[str | None, Query(max_length=36)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[CohortRunRead]:
    try:
        return ResearchService(db).list_runs(
            current_user,
            study_id,
            offset=offset,
            limit=limit,
        )
    except ResearchError as exc:
        raise _research_http_error(exc) from exc


@router.get("/runs/{run_id}", response_model=CohortRunRead)
def run_detail(
    run_id: str,
    db: DbSession,
    current_user: CohortReader,
) -> CohortRunRead:
    try:
        return ResearchService(db).run(run_id, current_user)
    except ResearchError as exc:
        raise _research_http_error(exc) from exc


@router.get("/runs/{run_id}/snapshot", response_model=ResearchSnapshotRead)
def run_snapshot(
    run_id: str,
    db: DbSession,
    current_user: CohortReader,
) -> ResearchSnapshotRead:
    try:
        return ResearchService(db).run_snapshot(run_id, current_user)
    except ResearchError as exc:
        raise _research_http_error(exc) from exc
