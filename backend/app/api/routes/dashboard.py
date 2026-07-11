from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import (
    ActiveIngredientModel,
    MedicationCounselingSummaryModel,
    MedicationModel,
    UserModel,
)
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
        catalog_quality={
            "active_ingredients_total": db.scalar(select(func.count(ActiveIngredientModel.id)))
            or 0,
            "active_ingredients_curated": db.scalar(
                select(func.count(ActiveIngredientModel.id)).where(
                    ActiveIngredientModel.validation_status.in_(["curated", "validated"])
                )
            )
            or 0,
            "active_ingredients_pending": db.scalar(
                select(func.count(ActiveIngredientModel.id)).where(
                    ActiveIngredientModel.validation_status == "pending_review"
                )
            )
            or 0,
            "medications_demo": db.scalar(
                select(func.count(MedicationModel.id)).where(
                    MedicationModel.evidence_source_type == "demo_seed"
                )
            )
            or 0,
            "medications_without_source": db.scalar(
                select(func.count(MedicationModel.id)).where(
                    MedicationModel.evidence_source_url.is_(None)
                )
            )
            or 0,
            "medications_without_dose_rule": db.scalar(
                select(func.count(MedicationModel.id)).where(
                    MedicationModel.dose_rule_validation_status == "pending_review"
                )
            )
            or 0,
            "medications_without_policy": db.scalar(
                select(func.count(MedicationModel.id)).where(
                    MedicationModel.policy_validation_status == "pending_review"
                )
            )
            or 0,
            "counseling_summaries": db.scalar(
                select(func.count(MedicationCounselingSummaryModel.id))
            )
            or 0,
        },
    )
