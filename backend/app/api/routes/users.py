from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_capabilities
from app.core.security import hash_password
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import ROLE_PROFESSION, Capability
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import (
    UserClinicalProfileUpdate,
    UserCreate,
    UserRead,
    UserRoleUpdate,
    UserStatusUpdate,
)
from app.services.audit_service import AuditService
from app.services.capability_policy import (
    InvalidProfessionalProfile,
    validate_professional_profile,
)

router = APIRouter(prefix="/users", tags=["users"])
DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[
    UserModel, Depends(require_capabilities(Capability.USER_MANAGE))
]


@router.get("", response_model=list[UserRead])
def list_users(db: DbSession, _current_user: AdminUser) -> list[UserRead]:
    return UserRepository(db).list()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DbSession, current_user: AdminUser) -> UserRead:
    repository = UserRepository(db)
    if repository.get_by_email(payload.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado.",
        )
    profession = payload.profession or ROLE_PROFESSION[payload.role]
    try:
        validate_professional_profile(
            role=payload.role,
            profession=profession,
            capabilities=payload.capabilities,
            specialty_codes=payload.specialty_codes,
        )
    except InvalidProfessionalProfile as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    user = repository.create(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role.value,
        profession=profession.value,
        capabilities=payload.capabilities,
        is_active=payload.is_active,
        specialty_code=payload.specialty_code,
        specialty_codes=payload.specialty_codes,
        credential_type=payload.credential_type,
        credential_code_demo=payload.credential_code_demo,
        credential_region=payload.credential_region,
        credential_expires_at=payload.credential_expires_at,
        institutional_policy=payload.institutional_policy,
        sensitive_data_segments=payload.sensitive_data_segments,
        crm_demo=payload.crm_demo,
        crm_uf=payload.crm_uf.upper() if payload.crm_uf else None,
        rqe_demo=payload.rqe_demo,
        credential_verification_status="demo_unverified",
        institution_id=payload.institution_id,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    updated = repository.set_status(user, payload.is_active)
    AuditService(db).record_action(
        user=current_user,
        action="user.status_update",
        resource_type="user",
        resource_id=str(updated.id),
        details={"email": updated.email, "is_active": updated.is_active},
    )
    return updated


@router.patch("/{user_id}/clinical-profile", response_model=UserRead)
def update_user_clinical_profile(
    user_id: int,
    payload: UserClinicalProfileUpdate,
    db: DbSession,
    current_user: AdminUser,
) -> UserRead:
    user = UserRepository(db).get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    values = payload.model_dump(exclude_unset=True)
    profession = values.get("profession", user.profession)
    capabilities = values.get("capabilities", list(user.capabilities or []))
    specialty_codes = values.get("specialty_codes", list(user.specialty_codes or []))
    try:
        validate_professional_profile(
            role=user.role,
            profession=profession,
            capabilities=capabilities,
            specialty_codes=specialty_codes,
        )
    except InvalidProfessionalProfile as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    for field, value in values.items():
        setattr(user, field, value.value if hasattr(value, "value") else value)
    user.credential_verification_status = "demo_unverified"
    db.commit()
    db.refresh(user)
    AuditService(db).record_action(
        user=current_user,
        action="user.clinical_profile_update",
        resource_type="user",
        resource_id=str(user.id),
        details={
            "specialty": user.specialty_code,
            "credential_verification_status": "demo_unverified",
        },
    )
    return user


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    user.role = payload.role.value
    user.profession = ROLE_PROFESSION[payload.role].value
    user.capabilities = []
    user.capability_policy_version = "explicit-v1"
    db.commit()
    db.refresh(user)
    updated = user
    AuditService(db).record_action(
        user=current_user,
        action="user.role_update",
        resource_type="user",
        resource_id=str(updated.id),
        details={"email": updated.email, "role": updated.role},
    )
    return updated
