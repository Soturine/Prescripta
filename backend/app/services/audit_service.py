from sqlalchemy.orm import Session

from app.database.models import PrescriptionAuditModel
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
    ) -> PrescriptionAuditModel:
        return self.repository.create(
            patient_id=patient.id,
            medication_id=medication.id,
            patient_name=patient.name,
            medication_name=medication.brand_name,
            dose_mg=prescription.dose_mg,
            frequency_per_day=prescription.frequency_per_day,
            route=prescription.route,
            status=result.status.value,
            risk_level=result.risk_level.value,
            alerts=[alert.to_dict() for alert in result.alerts],
        )
