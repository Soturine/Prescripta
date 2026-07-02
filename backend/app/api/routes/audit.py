from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit_schema import AuditRead

router = APIRouter(prefix="/audit", tags=["audit"])
DbSession = Annotated[Session, Depends(get_db)]
AuditReader = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.AUDITOR))]


@router.get("", response_model=list[AuditRead])
def list_audit(db: DbSession, _current_user: AuditReader) -> list[AuditRead]:
    return AuditRepository(db).list()
