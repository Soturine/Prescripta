from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.core.security import hash_password
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserRead, UserRoleUpdate, UserStatusUpdate
from app.services.audit_service import AuditService

router = APIRouter(prefix="/users", tags=["users"])
DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN))]


@router.get("", response_model=list[UserRead])
def list_users(db: DbSession, _current_user: AdminUser) -> list[UserRead]:
    return UserRepository(db).list()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DbSession, current_user: AdminUser) -> UserRead:
    repository = UserRepository(db)
    if repository.get_by_email(payload.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail ja cadastrado.",
        )
    user = repository.create(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role.value,
        is_active=payload.is_active,
    )
    AuditService(db).record_action(
        user=current_user,
        action="user.create",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email, "role": user.role, "is_active": user.is_active},
    )
    return user


@router.patch("/{user_id}/status", response_model=UserRead)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: DbSession,
    current_user: AdminUser,
) -> UserRead:
    repository = UserRepository(db)
    user = repository.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado.")
    updated = repository.set_status(user, payload.is_active)
    AuditService(db).record_action(
        user=current_user,
        action="user.status_update",
        resource_type="user",
        resource_id=str(updated.id),
        details={"email": updated.email, "is_active": updated.is_active},
    )
    return updated


@router.patch("/{user_id}/role", response_model=UserRead)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: DbSession,
    current_user: AdminUser,
) -> UserRead:
    repository = UserRepository(db)
    user = repository.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado.")
    updated = repository.set_role(user, payload.role.value)
    AuditService(db).record_action(
        user=current_user,
        action="user.role_update",
        resource_type="user",
        resource_id=str(updated.id),
        details={"email": updated.email, "role": updated.role},
    )
    return updated
