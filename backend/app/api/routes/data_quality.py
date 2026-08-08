from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require_any_capability
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import Capability
from app.schemas.research_schema import DataQualityFindingRead, DataQualityRunRead
from app.services.data_quality_service import DataQualityService

router = APIRouter(prefix="/data-quality", tags=["data-quality"])
DbSession = Annotated[Session, Depends(get_db)]
DQReader = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.DATA_QUALITY_READ, Capability.DATA_QUALITY_RUN)),
]
DQRunner = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.DATA_QUALITY_RUN)),
]


@router.post("/runs", response_model=DataQualityRunRead)
def run_data_quality(db: DbSession, current_user: DQRunner) -> DataQualityRunRead:
    return DataQualityRunRead.model_validate(DataQualityService(db).run(current_user))


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
