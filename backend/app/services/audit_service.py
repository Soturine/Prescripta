from sqlalchemy.orm import Session

from app.database.models import AuditEventModel, PrescriptionAuditModel, UserModel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput, PrescriptionResult
from app.repositories.audit_repository import AuditRepository
from app.services.clinical_snapshot import CLINICAL_SNAPSHOT_SCHEMA, clinical_snapshot_hash


class AuditService:
    def __init__(self, db: Session, *, auto_commit: bool = True) -> None:
        self.repository = AuditRepository(db)
        self.auto_commit = auto_commit

    def record_check(
        self,
        patient: Patient,
        medication: Medication,
        prescription: PrescriptionInput,
        result: PrescriptionResult,
        user: UserModel | None = None,
        *,
        clinical_snapshot: dict | None = None,
        clinical_decision: dict | None = None,
        dose_intelligence: dict | None = None,
        psychotropic_safety: list[dict] | None = None,
        prescribing_policy: dict | None = None,
    ) -> PrescriptionAuditModel:
        snapshot = clinical_snapshot or {}
        hash_algorithm, snapshot_hash = clinical_snapshot_hash(snapshot)
        effective_dose = prescription.effective_dose
        amount_mg = effective_dose.amount_mg
        prescription_audit = self.repository.create_prescription_check(
            commit=self.auto_commit,
            patient_id=patient.id,
            medication_id=medication.id,
            user_id=user.id if user else None,
            user_name=None,
            user_email=None,
            patient_name=f"Paciente #P-{patient.id:05d}" if patient.id else "Paciente externo",
            medication_name=medication.brand_name,
            dose_mg=float(amount_mg) if amount_mg is not None else None,
            frequency_per_day=effective_dose.frequency_per_day,
            route=prescription.route,
            duration_days=prescription.duration_days,
            indication=prescription.indication,
            status=result.status.value,
            risk_level=result.risk_level.value,
            alerts=[alert.to_dict() for alert in result.alerts],
            dose_input=effective_dose.to_dict(),
            clinical_decision=clinical_decision or {},
            clinical_snapshot=snapshot,
            snapshot_hash=snapshot_hash,
            hash_algorithm=hash_algorithm,
            snapshot_schema_version=snapshot.get("schema_version", CLINICAL_SNAPSHOT_SCHEMA),
            correlation_id=(clinical_decision or {}).get("correlation_id"),
            dose_intelligence=dose_intelligence or {},
            psychotropic_safety=psychotropic_safety or [],
            prescribing_policy=prescribing_policy or {},
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
                "medication_id": medication.id,
                "active_ingredient": medication.active_ingredient,
                "dose": effective_dose.to_dict(),
                "route": prescription.route,
                "duration_days": prescription.duration_days,
                "indication": prescription.indication,
                "alerts_count": len(result.alerts),
                "compatibility": result.compatibility.get("level"),
                "source": medication.evidence_source_type,
                "jurisdiction": medication.source_jurisdiction,
                "validation_status": medication.validation_status,
                "patient_data_considered": result.dose_summary.get("patient_data_considered", []),
                "secret_logged": False,
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
                    "active_ingredient": medication.active_ingredient,
                    "alert": alert.to_dict(),
                    "severity": alert.severity.value,
                    "rule_id": alert.code,
                    "source": medication.evidence_source_type,
                    "jurisdiction": medication.source_jurisdiction,
                    "validation_status": medication.validation_status,
                    "secret_logged": False,
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
            commit=self.auto_commit,
            user_id=user.id if user else None,
            user_name=None,
            user_email=None,
            user_role=user.role if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level=risk_level,
            status=status,
            details=self._sanitize_details(details),
        )

    def _sanitize_details(self, details: dict) -> dict:
        prohibited = {"cpf", "cns", "phone", "telefone", "email", "patient_name"}
        secret_fragments = {"password", "senha", "token", "secret", "api_key"}
        safe_security_flags = {"secret_logged"}
        sanitized = {}
        for key, value in details.items():
            lowered = str(key).lower()
            contains_secret = any(fragment in lowered for fragment in secret_fragments)
            if lowered in prohibited or (
                contains_secret and lowered not in safe_security_flags
            ):
                sanitized[key] = "[redacted]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_details(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized
