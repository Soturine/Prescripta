from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_any_capability
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import Capability
from app.schemas.ai_task_schema import (
    AIInteractionRead,
    AIInteractionReviewRequest,
    AIRequestSchema,
)
from app.services.ai_task_router import AITaskError, AITaskRouter

router = APIRouter(prefix="/ai/tasks", tags=["ai-tasks"])
DbSession = Annotated[Session, Depends(get_db)]
ResearchAIUser = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.RESEARCH_AI_USE)),
]
ResearchReviewer = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.RESEARCH_STUDY_REVIEW)),
]


@router.post("", response_model=AIInteractionRead, status_code=201)
def execute_task(
    payload: AIRequestSchema,
    db: DbSession,
    current_user: ResearchAIUser,
) -> AIInteractionRead:
    try:
        return AITaskRouter(db).execute(payload, current_user)
    except AITaskError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{interaction_id}/review", response_model=AIInteractionRead)
def review_task(
    interaction_id: str,
    payload: AIInteractionReviewRequest,
    db: DbSession,
    current_user: ResearchReviewer,
) -> AIInteractionRead:
    try:
        return AITaskRouter(db).review(interaction_id, payload, current_user)
    except AITaskError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
