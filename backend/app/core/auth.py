from collections.abc import Callable
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import Capability, UserRole
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]
BearerToken = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_current_user(
    credentials: BearerToken,
    db: DbSession,
    session_cookie: Annotated[str | None, Cookie(alias="prescripta_session")] = None,
) -> UserModel:
    token = credentials.credentials if credentials is not None else session_cookie
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais ausentes.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", "0"))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = UserRepository(db).get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo.",
        )
    db.info["current_user"] = user
    return user


CurrentUser = Annotated[UserModel, Depends(get_current_user)]


def require_roles(*allowed_roles: UserRole) -> Callable[[CurrentUser], UserModel]:
    def dependency(current_user: CurrentUser) -> UserModel:
        if current_user.role not in {role.value for role in allowed_roles}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil sem permissao para esta acao.",
            )
        return current_user

    return dependency


def require_capabilities(
    *required_capabilities: Capability | str,
) -> Callable[[CurrentUser], UserModel]:
    required = {
        capability.value if isinstance(capability, Capability) else capability
        for capability in required_capabilities
    }

    def dependency(current_user: CurrentUser) -> UserModel:
        available = set(current_user.capabilities or [])
        if not required.issubset(available):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Capacidade profissional ou institucional ausente.",
            )
        return current_user

    return dependency


def require_any_capability(
    *accepted_capabilities: Capability | str,
) -> Callable[[CurrentUser], UserModel]:
    accepted = {
        capability.value if isinstance(capability, Capability) else capability
        for capability in accepted_capabilities
    }

    def dependency(current_user: CurrentUser) -> UserModel:
        if not accepted.intersection(set(current_user.capabilities or [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Capacidade profissional ou institucional ausente.",
            )
        return current_user

    return dependency
