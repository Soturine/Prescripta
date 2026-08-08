from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.config import settings
from app.core.security import create_access_token, verify_password, verify_totp
from app.database.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import LoginRequest, TokenResponse
from app.schemas.user_schema import UserRead
from app.services.auth_throttle import LoginThrottle

router = APIRouter(prefix="/auth", tags=["auth"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession, response: Response) -> TokenResponse:
    throttle = LoginThrottle(db)
    if throttle.locked(payload.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas. Aguarde antes de tentar novamente.",
            headers={"Retry-After": "900"},
        )
    user = UserRepository(db).get_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.hashed_password):
        throttle.failure(payload.email, reason="invalid_credentials")
        # A tentativa negada é a operação inteira deste command e precisa ser
        # durável antes que o HTTPException encerre a dependency generator.
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha invalidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo.",
        )
    if user.mfa_enabled and not verify_totp(payload.mfa_code, user.mfa_secret_encrypted):
        throttle.failure(payload.email, reason="invalid_mfa")
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código MFA inválido.",
        )

    throttle.success(payload.email, user_id=user.id, user_role=user.role)
    token = create_access_token(str(user.id))
    response.set_cookie(
        key="prescripta_session",
        value=token,
        httponly=True,
        secure=settings.environment.lower() not in {"development", "dev", "local", "test"},
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    return TokenResponse(
        access_token=token,
        user=UserRead.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    response.delete_cookie("prescripta_session", path="/", httponly=True, samesite="lax")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
