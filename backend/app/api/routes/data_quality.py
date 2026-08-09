from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import require_any_capability
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import Capability
from app.schemas.research_schema import (
    DataQualityAcknowledgeRequest,
    DataQualityFindingRead,
    DataQualityRunRead,
    DataQualityRunRequest,
)
from app.services.data_quality_service import DataQualityService

router = APIRouter(prefix="/data-quality", tags=["data-quality"])
EMPTY_DQ_RUN_REQUEST = DataQualityRunRequest()
DbSession = Annotated[Session, Depends(get_db)]
DQReader = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.DATA_QUALITY_READ, Capability.DATA_QUALITY_RUN)),
]
DQRunner = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.DATA_QUALITY_RUN)),
]
DQAcknowledger = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.DATA_QUALITY_ACKNOWLEDGE)),
]


@router.post("/runs", response_model=DataQualityRunRead)
def run_data_quality(
    db: DbSession,
    current_user: DQRunner,
    payload: Annotated[DataQualityRunRequest, Body()] = EMPTY_DQ_RUN_REQUEST,
) -> DataQualityRunRead:
    try:
        return DataQualityRunRead.model_validate(
            DataQualityService(db).run(current_user, payload.study_id)
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/findings", response_model=list[DataQualityFindingRead])
def list_findings(
    db: DbSession,
    current_user: DQReader,
    finding_status: str | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[DataQualityFindingRead]:
    return DataQualityService(db).list(
        current_user,
        status=finding_status,
        offset=offset,
        limit=limit,
    )


@router.post("/findings/{finding_id}/acknowledge", response_model=DataQualityFindingRead)
def acknowledge_finding(
    finding_id: str,
    payload: DataQualityAcknowledgeRequest,
    db: DbSession,
    current_user: DQAcknowledger,
) -> DataQualityFindingRead:
    try:
        return DataQualityFindingRead.model_validate(
            DataQualityService(db).acknowledge(finding_id, payload.resolution, current_user)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
