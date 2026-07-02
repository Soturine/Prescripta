from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit_schema import AuditRead

router = APIRouter(prefix="/audit", tags=["audit"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[AuditRead])
def list_audit(db: DbSession) -> list[AuditRead]:
    return AuditRepository(db).list()
