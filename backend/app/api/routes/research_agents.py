from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_any_capability
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import Capability
from app.schemas.research_v093_schema import (
    AgentReviewRequest,
    AgentRunCreate,
    AgentRunRead,
    AgentStepRequest,
)
from app.services.agentic_research_service import AgenticResearchService
from app.services.research_service import ResearchConflict, ResearchNotFound

router = APIRouter(prefix="/research/agents", tags=["research-agents"])
DbSession = Annotated[Session, Depends(get_db)]
AgentUser = Annotated[
    UserModel,
    Depends(
        require_any_capability(
            Capability.RESEARCH_AI_USE,
            Capability.RESEARCH_STUDY_WRITE,
        )
    ),
]


def _error(exc: Exception) -> HTTPException:
    code = (
        status.HTTP_404_NOT_FOUND if isinstance(exc, ResearchNotFound) else status.HTTP_409_CONFLICT
    )
    return HTTPException(status_code=code, detail=str(exc))


@router.post("", response_model=AgentRunRead, status_code=status.HTTP_201_CREATED)
def create_agent_run(
    payload: AgentRunCreate, db: DbSession, current_user: AgentUser
) -> AgentRunRead:
    try:
        return AgenticResearchService(db).create(payload, current_user)
    except (ResearchNotFound, ResearchConflict) as exc:
        raise _error(exc) from exc


@router.post("/{run_id}/steps", response_model=AgentRunRead)
def advance_agent_run(
    run_id: str, payload: AgentStepRequest, db: DbSession, current_user: AgentUser
) -> AgentRunRead:
    try:
        return AgenticResearchService(db).step(run_id, payload, current_user)
    except (ResearchNotFound, ResearchConflict) as exc:
        raise _error(exc) from exc


@router.post("/{run_id}/review", response_model=AgentRunRead)
def review_agent_run(
    run_id: str, payload: AgentReviewRequest, db: DbSession, current_user: AgentUser
) -> AgentRunRead:
    try:
        return AgenticResearchService(db).review(run_id, payload, current_user)
    except (ResearchNotFound, ResearchConflict) as exc:
        raise _error(exc) from exc


@router.post("/{run_id}/cancel", response_model=AgentRunRead)
def cancel_agent_run(run_id: str, db: DbSession, current_user: AgentUser) -> AgentRunRead:
    try:
        return AgenticResearchService(db).cancel(run_id, current_user)
    except (ResearchNotFound, ResearchConflict) as exc:
        raise _error(exc) from exc
