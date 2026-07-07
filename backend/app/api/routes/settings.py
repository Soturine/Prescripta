from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.schemas.ai_settings_schema import (
    AIConnectionTestRequest,
    AIConnectionTestResponse,
    AICredentialSaveRequest,
    AICredentialStatus,
    AIModelListResponse,
    AIModelSelectRequest,
    AIProviderInfo,
    AISettingsRead,
)
from app.services.ai_settings import AIConfigurationError, AISettingsService

router = APIRouter(prefix="/settings/ai", tags=["ai-settings"])
DbSession = Annotated[Session, Depends(get_db)]
AISettingsReader = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM, UserRole.AUDITOR)),
]
AISettingsManager = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN))]


@router.get("/providers", response_model=list[AIProviderInfo])
def list_ai_providers(
    db: DbSession,
    _current_user: AISettingsReader,
) -> list[AIProviderInfo]:
    return AISettingsService(db).providers()


@router.get("/current", response_model=AISettingsRead)
def get_current_ai_settings(
    db: DbSession,
    _current_user: AISettingsReader,
) -> AISettingsRead:
    return AISettingsService(db).current()


@router.get("/models", response_model=AIModelListResponse)
def list_ai_models(
    db: DbSession,
    current_user: AISettingsReader,
    provider: str = Query(default="fallback"),
    refresh: bool = Query(default=False),
) -> AIModelListResponse:
    try:
        return AISettingsService(db).list_models(
            provider,
            refresh=refresh,
            user=current_user if refresh else None,
        )
    except AIConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/credentials", response_model=AICredentialStatus)
def save_ai_credential(
    payload: AICredentialSaveRequest,
    db: DbSession,
    current_user: AISettingsManager,
) -> AICredentialStatus:
    try:
        return AISettingsService(db).save_credential(payload, current_user)
    except AIConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/credentials/{provider}", response_model=AICredentialStatus)
def delete_ai_credential(
    provider: str,
    db: DbSession,
    current_user: AISettingsManager,
) -> AICredentialStatus:
    try:
        return AISettingsService(db).delete_credential(provider, current_user)
    except AIConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/test", response_model=AIConnectionTestResponse)
def test_ai_connection(
    payload: AIConnectionTestRequest,
    db: DbSession,
    current_user: AISettingsManager,
) -> AIConnectionTestResponse:
    try:
        return AISettingsService(db).test_connection(payload, current_user)
    except AIConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/select-model", response_model=AISettingsRead)
def select_ai_model(
    payload: AIModelSelectRequest,
    db: DbSession,
    current_user: AISettingsManager,
) -> AISettingsRead:
    try:
        return AISettingsService(db).select_model(payload, current_user)
    except AIConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
