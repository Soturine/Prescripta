from sqlalchemy.orm import Session

from app.database.models import AuditEventModel, PrescriptionAuditModel, UserModel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput, PrescriptionResult
from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, db: Session) -> None:
        self.repository = AuditRepository(db)

    def record_check(
        self,
        patient: Patient,
        medication: Medication,
        prescription: PrescriptionInput,
        result: PrescriptionResult,
        user: UserModel | None = None,
    ) -> PrescriptionAuditModel:
        prescription_audit = self.repository.create_prescription_check(
            patient_id=patient.id,
            medication_id=medication.id,
            user_id=user.id if user else None,
            user_name=user.name if user else None,
            user_email=user.email if user else None,
            patient_name=patient.name,
            medication_name=medication.brand_name,
            dose_mg=prescription.dose_mg,
            frequency_per_day=prescription.frequency_per_day,
            route=prescription.route,
            duration_days=prescription.duration_days,
            indication=prescription.indication,
            status=result.status.value,
            risk_level=result.risk_level.value,
            alerts=[alert.to_dict() for alert in result.alerts],
        )
        self.record_action(
            user=user,
            action="prescription.check",
            resource_type="prescription",
            resource_id=str(prescription_audit.id),
            status=result.status.value,
            risk_level=result.risk_level.value,
            details={
                "patient_id": patient.id,
                "patient_name": patient.name,
                "medication_id": medication.id,
                "medication_name": medication.brand_name,
                "active_ingredient": medication.active_ingredient,
                "dose_mg": prescription.dose_mg,
                "frequency_per_day": prescription.frequency_per_day,
                "route": prescription.route,
                "duration_days": prescription.duration_days,
                "indication": prescription.indication,
                "alerts_count": len(result.alerts),
                "compatibility": result.compatibility.get("level"),
                "source": medication.evidence_source_type,
                "jurisdiction": medication.source_jurisdiction,
                "validation_status": medication.validation_status,
            },
        )
        for alert in result.alerts:
            self.record_action(
                user=user,
                action="prescription.alert_fired",
                resource_type="prescription",
                resource_id=str(prescription_audit.id),
                status=result.status.value,
                risk_level=result.risk_level.value,
                details={
                    "patient_id": patient.id,
                    "medication_id": medication.id,
                    "medication_name": medication.brand_name,
                    "active_ingredient": medication.active_ingredient,
                    "alert": alert.to_dict(),
                    "severity": alert.severity.value,
                    "rule_id": alert.code,
                    "source": medication.evidence_source_type,
                    "jurisdiction": medication.source_jurisdiction,
                    "validation_status": medication.validation_status,
                },
            )
        return prescription_audit

    def record_action(
        self,
        *,
        user: UserModel | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        details: dict,
        risk_level: str | None = None,
        status: str | None = None,
    ) -> AuditEventModel:
        return self.repository.create_event(
            user_id=user.id if user else None,
            user_name=user.name if user else None,
            user_email=user.email if user else None,
            user_role=user.role if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level=risk_level,
            status=status,
            details=details,
        )
