from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.models import (
    AuditEventModel,
    ClinicalImportBatchModel,
    ConsentRecordModel,
    MedicationCounselingSummaryModel,
    MedicationModel,
    PatientFunctionalProfileModel,
    PatientModel,
    PrescriptionAuditModel,
)
from app.integrations.services.clinical_reconciliation_service import ClinicalReconciliationService
from app.reports.schemas import (
    ReportAIContext,
    ReportAlertEvidence,
    ReportEvidenceBundle,
    ReportPatientContext,
    ReportPrescriptionResult,
    ReportSource,
)
from app.services.ai_settings import AISettingsService


class ReportEvidenceBundleBuilder:
    def __init__(self, db: Session) -> None:
        self.db = db

    def prescription_bundle(
        self,
        audit: PrescriptionAuditModel,
        *,
        report_type: str = "prescription_analysis",
        report_mode: str = "complete_internal",
        anonymized: bool = False,
    ) -> ReportEvidenceBundle:
        patient = self.db.get(PatientModel, audit.patient_id) if audit.patient_id else None
        medication = (
            self.db.get(MedicationModel, audit.medication_id) if audit.medication_id else None
        )
        source = self._medication_source(medication)
        alerts = [
            self._alert_evidence(alert, source.source_id)
            for alert in list(audit.alerts or [])
            if isinstance(alert, dict)
        ]
        daily_dose = audit.dose_mg * audit.frequency_per_day
        accumulated = daily_dose * audit.duration_days if audit.duration_days else None
        counseling = self._latest_counseling(medication)
        sources = [source]
        if counseling is not None:
            sources.append(
                ReportSource(
                    source_id=counseling.source_id,
                    source_name=counseling.source_name,
                    jurisdiction=counseling.jurisdiction,
                    validation_status=counseling.validation_status,
                    evidence_type="medication_counseling_summary",
                    source_url=counseling.source_url,
                    confidence=counseling.confidence,
                )
            )
        patient_context = self._patient_context(patient, anonymized=anonymized)
        missing_data = patient_context.missing_data if patient_context else []
        metadata: dict[str, Any] = {
            "audit_id": audit.id,
            "checked_at": audit.checked_at.isoformat(),
            "user_id": audit.user_id,
            "user_name": audit.user_name,
            "user_email": None if anonymized else audit.user_email,
            "human_review_required": audit.status != "liberado" or audit.risk_level != "baixo",
            "missing_data": missing_data,
            "counseling_summary_available": counseling is not None,
        }
        if counseling is not None:
            metadata["patient_counseling"] = {
                "orientation_points": self._orientation_points(counseling),
                "red_flags": list(counseling.red_flags or []),
                "monitoring_required": list(counseling.monitoring_required or []),
                "generated_by": counseling.generated_by,
                "requires_review": counseling.requires_review,
            }

        return ReportEvidenceBundle(
            report_type=report_type,
            report_mode=report_mode,
            generated_at=datetime.now(UTC),
            patient_context=patient_context,
            prescription_result=ReportPrescriptionResult(
                risk_level=audit.risk_level,
                status=audit.status,
                medication_name=audit.medication_name,
                active_ingredient=medication.active_ingredient if medication else None,
                commercial_name=medication.brand_name if medication else audit.medication_name,
                dose_per_administration=f"{audit.dose_mg:g} mg",
                frequency=f"{audit.frequency_per_day}x ao dia",
                route=audit.route,
                daily_dose=f"{daily_dose:g} mg/dia",
                accumulated_dose=f"{accumulated:g} mg" if accumulated is not None else None,
                duration=f"{audit.duration_days} dias" if audit.duration_days else None,
                continuous_use=bool(getattr(medication, "continuous_use", False)),
                alerts=alerts,
            ),
            rules_fired=[alert.code for alert in alerts],
            sources=self._unique_sources(sources),
            ai_context=self._ai_context(),
            metadata=metadata,
        )

    def reconciliation_bundle(
        self,
        batch: ClinicalImportBatchModel,
        *,
        report_mode: str = "technical_audit",
        anonymized: bool = False,
    ) -> ReportEvidenceBundle:
        patient = self.db.get(PatientModel, batch.patient_id) if batch.patient_id else None
        consent = self.db.get(ConsentRecordModel, batch.consent_id) if batch.consent_id else None
        reconciliation = ClinicalReconciliationService(self.db).build(batch)
        result = reconciliation.model_dump(mode="json")
        result["source_system"] = batch.source_system
        result["source_type"] = batch.source_type
        result["imported_at"] = batch.imported_at.isoformat()
        result["finished_at"] = batch.finished_at.isoformat() if batch.finished_at else None
        authorized_by = None
        if consent is not None:
            authorized_by = "omitido" if anonymized else consent.authorized_by
        result["consent"] = {
            "consent_id": batch.consent_id,
            "authorized_by": authorized_by,
            "purpose": consent.purpose if consent else None,
            "valid_until": (
                consent.valid_until.isoformat() if consent and consent.valid_until else None
            ),
        }
        source = ReportSource(
            source_id=f"clinical_import_{batch.id}",
            source_name=batch.source_system,
            jurisdiction="BR",
            validation_status="pending_human_review"
            if batch.status == "pending_review"
            else "reviewed",
            evidence_type=batch.source_type,
        )
        return ReportEvidenceBundle(
            report_type="reconciliation",
            report_mode=report_mode,
            patient_context=self._patient_context(patient, anonymized=anonymized),
            reconciliation_result=result,
            sources=[source],
            ai_context=self._ai_context(),
            metadata={
                "batch_id": batch.id,
                "status": batch.status,
                "errors": list(batch.errors or []),
                "anonymized": anonymized,
            },
        )

    def audit_bundle(
        self,
        events: list[AuditEventModel],
        *,
        filters: dict[str, Any],
        report_mode: str = "technical_audit",
    ) -> ReportEvidenceBundle:
        event_payloads = [
            {
                "id": event.id,
                "created_at": event.created_at.isoformat(),
                "user_id": event.user_id,
                "user_name": event.user_name,
                "user_role": event.user_role,
                "action": event.action,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "risk_level": event.risk_level,
                "status": event.status,
                "details": self._redact_secrets(event.details or {}),
            }
            for event in events
        ]
        return ReportEvidenceBundle(
            report_type="audit",
            report_mode=report_mode,
            audit_result={
                "filters": filters,
                "total_events": len(events),
                "events": event_payloads,
                "critical_events": [
                    event for event in event_payloads if event.get("risk_level") == "critico"
                ],
                "ai_events": [
                    event
                    for event in event_payloads
                    if str(event.get("action", "")).startswith("ai_")
                ],
                "report_events": [
                    event for event in event_payloads if event.get("resource_type") == "report"
                ],
            },
            ai_context=self._ai_context(),
            metadata={"filters": filters, "total_events": len(events)},
        )

    def _patient_context(
        self,
        patient: PatientModel | None,
        *,
        anonymized: bool,
    ) -> ReportPatientContext | None:
        if patient is None:
            return None
        functional = self.db.scalar(
            select(PatientFunctionalProfileModel).where(
                PatientFunctionalProfileModel.patient_id == patient.id
            )
        )
        return ReportPatientContext(
            patient_reference=self._patient_reference(patient, anonymized=anonymized),
            age_group=self._age_group(patient.age),
            sex_or_reproductive_context=(
                "pregnancy_or_lactation"
                if patient.pregnancy_or_lactation
                else "not_informed"
                if patient.pregnancy_or_lactation is None
                else "not_applicable_or_negative"
            ),
            clinical_profile={
                "renal": patient.renal_condition or "unknown",
                "hepatic": patient.hepatic_condition or "unknown",
                "cardiac": patient.cardiac_condition or "unknown",
                "hypertension": patient.hypertension,
                "diabetes": patient.diabetes,
            },
            functional_profile=self._functional_profile(functional),
            missing_data=self._missing_patient_data(patient, functional),
        )

    def _patient_reference(self, patient: PatientModel, *, anonymized: bool) -> str:
        if anonymized:
            return f"Paciente #P-{patient.id:05d}"
        return f"{patient.name} (#P-{patient.id:05d})"

    def _age_group(self, age: int | None) -> str:
        if age is None:
            return "unknown"
        if age < 12:
            return "child"
        if age < 18:
            return "adolescent"
        if age >= 65:
            return "older_adult"
        return "adult"

    def _missing_patient_data(
        self,
        patient: PatientModel,
        functional: PatientFunctionalProfileModel | None,
    ) -> list[str]:
        missing = []
        checks = {
            "renal_condition": patient.renal_condition,
            "hepatic_condition": patient.hepatic_condition,
            "cardiac_condition": patient.cardiac_condition,
            "pregnancy_lactation": patient.pregnancy_or_lactation,
            "current_medications": patient.current_medications,
            "allergies": patient.allergies,
        }
        for key, value in checks.items():
            if value is None or value == "" or value == []:
                missing.append(key)
        if functional is None:
            missing.append("functional_profile")
        return missing

    def _functional_profile(
        self,
        functional: PatientFunctionalProfileModel | None,
    ) -> list[str]:
        if functional is None:
            return []
        labels = {
            "drives_regularly": functional.drives_regularly,
            "professional_driver": functional.professional_driver,
            "operates_machinery": functional.operates_machinery,
            "works_at_height": functional.works_at_height,
            "fall_risk_activity": functional.fall_risk_activity,
            "night_shift": functional.night_shift,
            "caregiver_responsibility": functional.caregiver_responsibility,
            "high_attention_activity": functional.high_attention_activity,
            "frequent_alcohol_use": functional.frequent_alcohol_use,
            "history_of_falls": functional.history_of_falls,
            "low_tolerance_to_sedation_or_dizziness": (
                functional.low_tolerance_to_sedation_or_dizziness
            ),
        }
        return [key for key, value in labels.items() if value is True]

    def _medication_source(self, medication: MedicationModel | None) -> ReportSource:
        if medication is None:
            return ReportSource(
                source_id="prescription_audit_record",
                source_name="Registro interno da checagem",
                jurisdiction="BR",
                validation_status="internal",
                evidence_type="audit_record",
            )
        return ReportSource(
            source_id=self._source_id(
                f"medication_{medication.id}_{medication.active_ingredient}"
            ),
            source_name=medication.knowledge_source
            or medication.evidence_source_type
            or "Cadastro interno Prescripta",
            jurisdiction=medication.source_jurisdiction or "BR",
            validation_status=medication.validation_status or "demo",
            evidence_type=medication.evidence_source_type or "medication_catalog",
            source_url=medication.evidence_source_url,
        )

    def _latest_counseling(
        self,
        medication: MedicationModel | None,
    ) -> MedicationCounselingSummaryModel | None:
        if medication is None:
            return None
        conditions = [MedicationCounselingSummaryModel.medication_id == medication.id]
        if medication.active_ingredient_id is not None:
            conditions.append(
                MedicationCounselingSummaryModel.active_ingredient_id
                == medication.active_ingredient_id
            )
        return self.db.scalar(
            select(MedicationCounselingSummaryModel)
            .where(or_(*conditions))
            .order_by(MedicationCounselingSummaryModel.updated_at.desc())
        )

    def _orientation_points(self, counseling: MedicationCounselingSummaryModel) -> list[str]:
        points = list(counseling.patient_relevant_effects or [])
        points.extend(counseling.activity_warnings or [])
        points.extend(counseling.monitoring_required or [])
        if counseling.patient_friendly_summary:
            points.insert(0, counseling.patient_friendly_summary)
        return [point for point in points if point][:8]

    def _alert_evidence(self, alert: dict[str, Any], source_id: str) -> ReportAlertEvidence:
        code = str(alert.get("code") or "ALERT")
        return ReportAlertEvidence(
            code=code,
            title=str(alert.get("title") or code),
            severity=str(alert.get("severity") or "unknown"),
            source_id=source_id,
            evidence_summary=str(alert.get("description") or alert.get("recommendation") or ""),
            rule_id=code,
            recommendation=str(alert.get("recommendation") or ""),
        )

    def _ai_context(self) -> ReportAIContext:
        config = AISettingsService(self.db).runtime_config()
        return ReportAIContext(
            allow_external_ai=bool(config.enable_external_calls and config.provider != "fallback"),
            provider=config.provider,
            model=config.model or "deterministic",
            send_identifiable_data=False,
        )

    def _unique_sources(self, sources: list[ReportSource]) -> list[ReportSource]:
        unique: dict[str, ReportSource] = {}
        for source in sources:
            unique[source.source_id] = source
        return list(unique.values())

    def _source_id(self, value: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
        return normalized or "source"

    def _redact_secrets(self, details: dict[str, Any]) -> dict[str, Any]:
        redacted = {}
        for key, value in details.items():
            key_lower = str(key).lower()
            if "key" in key_lower or "secret" in key_lower or "token" in key_lower:
                redacted[key] = "[redacted]"
            elif isinstance(value, dict):
                redacted[key] = self._redact_secrets(value)
            else:
                redacted[key] = value
        return redacted
