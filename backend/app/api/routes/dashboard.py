from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.audit_repository import AuditRepository
from app.repositories.medication_repository import MedicationRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.dashboard_schema import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=DashboardSummary)
def get_dashboard(db: DbSession) -> DashboardSummary:
    audit_repository = AuditRepository(db)
    return DashboardSummary(
        patient_count=PatientRepository(db).count(),
        medication_count=MedicationRepository(db).count(),
        prescription_checks=audit_repository.count(),
        alerts_by_severity=audit_repository.alerts_by_severity(),
    )
