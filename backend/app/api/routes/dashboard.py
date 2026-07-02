from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import ALL_ROLES
from app.repositories.audit_repository import AuditRepository
from app.repositories.medication_repository import MedicationRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.dashboard_schema import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
DbSession = Annotated[Session, Depends(get_db)]
DashboardReader = Annotated[UserModel, Depends(require_roles(*ALL_ROLES))]


@router.get("", response_model=DashboardSummary)
def get_dashboard(db: DbSession, _current_user: DashboardReader) -> DashboardSummary:
    audit_repository = AuditRepository(db)
    return DashboardSummary(
        patient_count=PatientRepository(db).count(),
        medication_count=MedicationRepository(db).count(),
        prescription_checks=audit_repository.count(),
        alerts_by_severity=audit_repository.alerts_by_severity(),
    )
