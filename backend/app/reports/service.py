from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    AuditEventModel,
    ClinicalImportBatchModel,
    EmergencyProtocolRunModel,
    EmergencyProtocolRunReportModel,
    GeneratedReportModel,
    PrescriptionAuditModel,
    UserModel,
)
from app.reports.ai_report_composer import AIReportComposer
from app.reports.audit import decision_timeline, evidence_view
from app.reports.csv_exporter import export_csv_bytes
from app.reports.evidence_bundle import ReportEvidenceBundleBuilder
from app.reports.json_exporter import export_json_bytes
from app.reports.pdf_renderer import SimplePDFRenderer
from app.reports.renderer import render_report_html, render_report_lines
from app.reports.schemas import (
    PRESCRIPTA_VERSION,
    REPORT_TEMPLATE_VERSION,
    GeneratedReportRead,
    ReportEvidenceBundle,
    ReportMode,
    ReportNarrativeComposition,
    ReportPreview,
)
from app.reports.templates import REPORT_TITLES
from app.services.audit_service import AuditService


class ReportNotFoundError(ValueError):
    pass


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.builder = ReportEvidenceBundleBuilder(db)

    def list_reports(
        self,
        *,
        report_type: str | None = None,
        target_type: str | None = None,
    ) -> list[GeneratedReportModel]:
        stmt = select(GeneratedReportModel)
        if report_type:
            stmt = stmt.where(GeneratedReportModel.report_type == report_type)
        if target_type:
            stmt = stmt.where(GeneratedReportModel.target_type == target_type)
        stmt = stmt.order_by(GeneratedReportModel.generated_at.desc())
        return list(self.db.scalars(stmt))

    def get_report(self, report_id: int) -> GeneratedReportModel | None:
        return self.db.get(GeneratedReportModel, report_id)

    def prescription_preview(
        self,
        audit_id: int,
        *,
        mode: ReportMode = "complete_internal",
    ) -> ReportPreview:
        bundle = self.prescription_bundle(audit_id, mode=mode)
        title = REPORT_TITLES["prescription_analysis"]
        return self._preview(title=title, bundle=bundle)

    def patient_guidance_preview(self, audit_id: int) -> ReportPreview:
        bundle = self.prescription_bundle(
            audit_id,
            mode="patient_friendly",
            report_type="patient_guidance",
            anonymized=True,
        )
        return self._preview(title=REPORT_TITLES["patient_guidance"], bundle=bundle)

    def reconciliation_preview(
        self,
        import_id: int,
        *,
        anonymized: bool = False,
    ) -> ReportPreview:
        batch = self._batch_or_error(import_id)
        bundle = self.builder.reconciliation_bundle(batch, anonymized=anonymized)
        return self._preview(title=REPORT_TITLES["reconciliation"], bundle=bundle)

    def audit_preview(
        self,
        events: list[AuditEventModel],
        *,
        filters: dict[str, Any],
    ) -> ReportPreview:
        bundle = self.builder.audit_bundle(events, filters=filters)
        return self._preview(title=REPORT_TITLES["audit"], bundle=bundle)

    def protocol_run_preview(self, run_id: int) -> ReportPreview:
        run = self._protocol_run_or_error(run_id)
        bundle = self.builder.protocol_run_bundle(run)
        return self._preview(title=f"Relat?rio de Protocolo - {run.protocol_title}", bundle=bundle)

    def prescription_bundle(
        self,
        audit_id: int,
        *,
        mode: ReportMode = "complete_internal",
        report_type: str = "prescription_analysis",
        anonymized: bool | None = None,
    ) -> ReportEvidenceBundle:
        audit = self._prescription_audit_or_error(audit_id)
        should_anonymize = anonymized if anonymized is not None else mode == "anonymized"
        return self.builder.prescription_bundle(
            audit,
            report_type=report_type,
            report_mode=mode,
            anonymized=should_anonymize,
        )

    def generate_prescription_pdf(
        self,
        audit_id: int,
        *,
        user: UserModel,
        mode: ReportMode = "complete_internal",
    ) -> tuple[bytes, GeneratedReportModel]:
        preview = self.prescription_preview(audit_id, mode=mode)
        pdf = self._pdf_from_preview(preview)
        report = self._persist_generated_report(
            report_type="prescription_technical",
            target_type="prescription_audit",
            target_id=str(audit_id),
            user=user,
            preview=preview,
            file_bytes=pdf,
            anonymized=mode == "anonymized",
        )
        self._record_action(
            user=user,
            action="report.pdf_downloaded",
            report=report,
            details={"report_kind": "prescription_technical"},
        )
        return pdf, report

    def generate_patient_guidance_pdf(
        self,
        audit_id: int,
        *,
        user: UserModel,
    ) -> tuple[bytes, GeneratedReportModel]:
        preview = self.patient_guidance_preview(audit_id)
        pdf = self._pdf_from_preview(preview)
        report = self._persist_generated_report(
            report_type="patient_guidance",
            target_type="prescription_audit",
            target_id=str(audit_id),
            user=user,
            preview=preview,
            file_bytes=pdf,
            anonymized=True,
        )
        self._record_action(
            user=user,
            action="report.pdf_downloaded",
            report=report,
            details={"report_kind": "patient_guidance"},
        )
        return pdf, report

    def generate_reconciliation_pdf(
        self,
        import_id: int,
        *,
        user: UserModel,
        anonymized: bool = False,
    ) -> tuple[bytes, GeneratedReportModel]:
        preview = self.reconciliation_preview(import_id, anonymized=anonymized)
        pdf = self._pdf_from_preview(preview)
        report = self._persist_generated_report(
            report_type="reconciliation",
            target_type="clinical_import",
            target_id=str(import_id),
            user=user,
            preview=preview,
            file_bytes=pdf,
            anonymized=anonymized,
        )
        self._record_action(
            user=user,
            action="report.pdf_downloaded",
            report=report,
            details={"report_kind": "reconciliation"},
        )
        return pdf, report

    def generate_audit_pdf(
        self,
        events: list[AuditEventModel],
        *,
        filters: dict[str, Any],
        user: UserModel,
    ) -> tuple[bytes, GeneratedReportModel]:
        preview = self.audit_preview(events, filters=filters)
        pdf = self._pdf_from_preview(preview)
        report = self._persist_generated_report(
            report_type="audit",
            target_type="audit_events",
            target_id="filtered",
            user=user,
            preview=preview,
            file_bytes=pdf,
            anonymized=False,
        )
        self._record_action(
            user=user,
            action="report.pdf_downloaded",
            report=report,
            details={"report_kind": "audit"},
        )
        return pdf, report

    def generate_protocol_run_pdf(
        self,
        run_id: int,
        *,
        user: UserModel,
    ) -> tuple[bytes, GeneratedReportModel]:
        run = self._protocol_run_or_error(run_id)
        preview = self.protocol_run_preview(run_id)
        pdf = self._pdf_from_preview(preview)
        report = self._persist_generated_report(
            report_type="protocol_run_report",
            target_type="protocol_run",
            target_id=str(run_id),
            user=user,
            preview=preview,
            file_bytes=pdf,
            anonymized=False,
        )
        self.db.add(
            EmergencyProtocolRunReportModel(
                run_id=run.id,
                generated_report_id=report.id,
                report_type="protocol_run_report",
            )
        )
        self.db.commit()
        self._record_action(
            user=user,
            action="protocol.report_generated",
            report=report,
            details={
                "report_kind": "protocol_run_report",
                "run_id": run.id,
                "protocol_id": run.protocol_id,
                "protocol_version": run.protocol_version,
                "patient_id": run.patient_id,
            },
        )
        self._record_action(
            user=user,
            action="protocol.report_downloaded",
            report=report,
            details={
                "report_kind": "protocol_run_report",
                "run_id": run.id,
                "protocol_id": run.protocol_id,
                "protocol_version": run.protocol_version,
                "patient_id": run.patient_id,
            },
        )
        return pdf, report

    def export_prescription_json(
        self,
        audit_id: int,
        *,
        user: UserModel,
        anonymized: bool = False,
    ) -> bytes:
        bundle = self.prescription_bundle(
            audit_id,
            mode="anonymized" if anonymized else "complete_internal",
            anonymized=anonymized,
        )
        data = self._bundle_export_payload(bundle)
        content = export_json_bytes("prescription_analysis", data)
        self._record_export(
            user=user,
            action="export.json",
            target_type="prescription_audit",
            target_id=str(audit_id),
            details={"anonymized": anonymized, "bundle_hash": bundle.hash()},
        )
        return content

    def export_prescription_csv(
        self,
        audit_id: int,
        *,
        user: UserModel,
        anonymized: bool = False,
    ) -> bytes:
        bundle = self.prescription_bundle(
            audit_id,
            mode="anonymized" if anonymized else "complete_internal",
            anonymized=anonymized,
        )
        rows = self._prescription_csv_rows(bundle)
        content = export_csv_bytes(rows)
        self._record_export(
            user=user,
            action="export.csv",
            target_type="prescription_audit",
            target_id=str(audit_id),
            details={"anonymized": anonymized, "bundle_hash": bundle.hash()},
        )
        return content

    def export_import_json(
        self,
        import_id: int,
        *,
        user: UserModel,
        anonymized: bool = False,
    ) -> bytes:
        batch = self._batch_or_error(import_id)
        bundle = self.builder.reconciliation_bundle(batch, anonymized=anonymized)
        content = export_json_bytes("clinical_reconciliation", self._bundle_export_payload(bundle))
        self._record_export(
            user=user,
            action="export.json",
            target_type="clinical_import",
            target_id=str(import_id),
            details={"anonymized": anonymized, "bundle_hash": bundle.hash()},
        )
        return content

    def export_import_csv(
        self,
        import_id: int,
        *,
        user: UserModel,
        anonymized: bool = False,
    ) -> bytes:
        batch = self._batch_or_error(import_id)
        bundle = self.builder.reconciliation_bundle(batch, anonymized=anonymized)
        rows = (
            list(bundle.reconciliation_result.get("items", []))
            if bundle.reconciliation_result
            else []
        )
        content = export_csv_bytes(rows or [self._bundle_export_payload(bundle)])
        self._record_export(
            user=user,
            action="export.csv",
            target_type="clinical_import",
            target_id=str(import_id),
            details={"anonymized": anonymized, "bundle_hash": bundle.hash()},
        )
        return content

    def export_audit_json(
        self,
        events: list[AuditEventModel],
        *,
        filters: dict[str, Any],
        user: UserModel,
    ) -> bytes:
        bundle = self.builder.audit_bundle(events, filters=filters)
        content = export_json_bytes("audit_events", self._bundle_export_payload(bundle))
        self._record_export(
            user=user,
            action="export.json",
            target_type="audit_events",
            target_id="filtered",
            details={"filters": filters, "bundle_hash": bundle.hash()},
        )
        return content

    def export_audit_csv(
        self,
        events: list[AuditEventModel],
        *,
        filters: dict[str, Any],
        user: UserModel,
    ) -> bytes:
        bundle = self.builder.audit_bundle(events, filters=filters)
        rows = list(bundle.audit_result.get("events", [])) if bundle.audit_result else []
        content = export_csv_bytes(rows)
        self._record_export(
            user=user,
            action="export.csv",
            target_type="audit_events",
            target_id="filtered",
            details={"filters": filters, "bundle_hash": bundle.hash()},
        )
        return content

    def export_protocol_run_json(self, run_id: int, *, user: UserModel) -> bytes:
        run = self._protocol_run_or_error(run_id)
        bundle = self.builder.protocol_run_bundle(run)
        content = export_json_bytes("protocol_run_report", self._bundle_export_payload(bundle))
        self._record_export(
            user=user,
            action="protocol.exported_json",
            target_type="protocol_run",
            target_id=str(run_id),
            details={
                "run_id": run.id,
                "protocol_id": run.protocol_id,
                "protocol_version": run.protocol_version,
                "patient_id": run.patient_id,
                "bundle_hash": bundle.hash(),
            },
        )
        return content

    def export_protocol_run_csv(self, run_id: int, *, user: UserModel) -> bytes:
        run = self._protocol_run_or_error(run_id)
        bundle = self.builder.protocol_run_bundle(run)
        rows = [
            {
                "run_id": run.id,
                "protocol_id": run.protocol_id,
                "protocol_title": run.protocol_title,
                "protocol_version": run.protocol_version,
                "patient_id": run.patient_id,
                "status": run.status,
                "triage_flags": "; ".join(run.triage_flags or []),
                "evidence_refs": "; ".join(run.evidence_refs or []),
                "bundle_hash": bundle.hash(),
            }
        ]
        content = export_csv_bytes(rows)
        self._record_export(
            user=user,
            action="protocol.exported_csv",
            target_type="protocol_run",
            target_id=str(run_id),
            details={
                "run_id": run.id,
                "protocol_id": run.protocol_id,
                "protocol_version": run.protocol_version,
                "patient_id": run.patient_id,
                "bundle_hash": bundle.hash(),
            },
        )
        return content

    def export_report_json(self, report_id: int, *, user: UserModel) -> bytes:
        report = self.get_report(report_id)
        if report is None:
            raise ReportNotFoundError("Relatorio nao encontrado.")
        report_payload = GeneratedReportRead.model_validate(report).model_dump(mode="json")
        content = export_json_bytes("generated_report", report_payload)
        self._record_export(
            user=user,
            action="export.json",
            target_type="report",
            target_id=str(report_id),
            details={"evidence_bundle_hash": report.evidence_bundle_hash},
        )
        return content

    def _preview(self, *, title: str, bundle: ReportEvidenceBundle) -> ReportPreview:
        narrative = AIReportComposer(self.db).compose(bundle)
        timeline = decision_timeline(bundle)
        evidence = evidence_view(bundle)
        html = render_report_html(
            title=title,
            bundle=bundle,
            narrative=narrative,
            timeline=timeline,
            evidence=evidence,
        )
        return ReportPreview(
            title=title,
            report_type=bundle.report_type,
            report_mode=bundle.report_mode,
            evidence_bundle_hash=bundle.hash(),
            evidence_bundle=bundle.model_dump(mode="json"),
            narrative=narrative.narrative,
            narrative_metadata=narrative.model_dump(exclude={"narrative"}),
            timeline=timeline,
            evidence=evidence,
            html=html,
        )

    def _pdf_from_preview(self, preview: ReportPreview) -> bytes:
        bundle = ReportEvidenceBundle.model_validate(preview.evidence_bundle)
        narrative = ReportNarrativeComposition(
            narrative=preview.narrative,
            **preview.narrative_metadata,
        )
        lines = render_report_lines(
            title=preview.title,
            bundle=bundle,
            narrative=narrative,
            timeline=preview.timeline,
            evidence=preview.evidence,
        )
        return SimplePDFRenderer().render(lines)

    def _persist_generated_report(
        self,
        *,
        report_type: str,
        target_type: str,
        target_id: str,
        user: UserModel,
        preview: ReportPreview,
        file_bytes: bytes,
        anonymized: bool,
    ) -> GeneratedReportModel:
        report = GeneratedReportModel(
            report_type=report_type,
            target_type=target_type,
            target_id=target_id,
            generated_by_user_id=user.id,
            template_version=REPORT_TEMPLATE_VERSION,
            prescripta_version=PRESCRIPTA_VERSION,
            evidence_bundle_hash=preview.evidence_bundle_hash,
            ai_provider=preview.narrative_metadata.get("provider"),
            ai_model=preview.narrative_metadata.get("model"),
            ai_prompt_version=preview.narrative_metadata.get("prompt_version"),
            ai_used=bool(preview.narrative_metadata.get("ai_used")),
            fallback_used=bool(preview.narrative_metadata.get("fallback_used")),
            anonymized=anonymized,
            file_hash=hashlib.sha256(file_bytes).hexdigest(),
            status="generated",
            metadata_json={
                "title": preview.title,
                "report_mode": preview.report_mode,
                "narrative_status": preview.narrative_metadata.get("status"),
                "response_time_ms": preview.narrative_metadata.get("response_time_ms"),
                "error_summary": preview.narrative_metadata.get("error_summary"),
            },
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        self._record_action(
            user=user,
            action="report.generated",
            report=report,
            details={"report_type": report_type, "anonymized": anonymized},
        )
        return report

    def _record_action(
        self,
        *,
        user: UserModel,
        action: str,
        report: GeneratedReportModel,
        details: dict[str, Any],
    ) -> None:
        AuditService(self.db).record_action(
            user=user,
            action=action,
            resource_type="report",
            resource_id=str(report.id),
            status=report.status,
            details={
                **details,
                "report_id": report.id,
                "report_type": report.report_type,
                "target_type": report.target_type,
                "target_id": report.target_id,
                "evidence_bundle_hash": report.evidence_bundle_hash,
                "file_hash": report.file_hash,
                "ai_provider": report.ai_provider,
                "ai_model": report.ai_model,
                "ai_used": report.ai_used,
                "fallback_used": report.fallback_used,
                "secret_logged": False,
            },
        )

    def _record_export(
        self,
        *,
        user: UserModel,
        action: str,
        target_type: str,
        target_id: str,
        details: dict[str, Any],
    ) -> None:
        AuditService(self.db).record_action(
            user=user,
            action=action,
            resource_type=target_type,
            resource_id=target_id,
            status="exported",
            details={**details, "secret_logged": False},
        )

    def _bundle_export_payload(self, bundle: ReportEvidenceBundle) -> dict[str, Any]:
        return {
            "evidence_bundle_hash": bundle.hash(),
            "evidence_bundle": bundle.model_dump(mode="json"),
            "timeline": decision_timeline(bundle),
            "evidence": evidence_view(bundle),
        }

    def _prescription_csv_rows(self, bundle: ReportEvidenceBundle) -> list[dict[str, Any]]:
        prescription = bundle.prescription_result
        if prescription is None:
            return []
        rows = []
        for alert in prescription.alerts or []:
            rows.append(
                {
                    "audit_id": bundle.metadata.get("audit_id"),
                    "patient_reference": (
                        bundle.patient_context.patient_reference if bundle.patient_context else None
                    ),
                    "medication": prescription.medication_name,
                    "active_ingredient": prescription.active_ingredient,
                    "status": prescription.status,
                    "risk_level": prescription.risk_level,
                    "daily_dose": prescription.daily_dose,
                    "alert_code": alert.code,
                    "alert_severity": alert.severity,
                    "rule_id": alert.rule_id,
                    "source_id": alert.source_id,
                    "evidence_summary": alert.evidence_summary,
                }
            )
        if not rows:
            rows.append(
                {
                    "audit_id": bundle.metadata.get("audit_id"),
                    "patient_reference": (
                        bundle.patient_context.patient_reference if bundle.patient_context else None
                    ),
                    "medication": prescription.medication_name,
                    "active_ingredient": prescription.active_ingredient,
                    "status": prescription.status,
                    "risk_level": prescription.risk_level,
                    "daily_dose": prescription.daily_dose,
                    "alert_code": None,
                }
            )
        return rows

    def _prescription_audit_or_error(self, audit_id: int) -> PrescriptionAuditModel:
        audit = self.db.get(PrescriptionAuditModel, audit_id)
        if audit is None:
            raise ReportNotFoundError("Checagem de prescricao nao encontrada.")
        return audit

    def _batch_or_error(self, import_id: int) -> ClinicalImportBatchModel:
        batch = self.db.get(ClinicalImportBatchModel, import_id)
        if batch is None:
            raise ReportNotFoundError("Importacao clinica nao encontrada.")
        return batch

    def _protocol_run_or_error(self, run_id: int) -> EmergencyProtocolRunModel:
        run = self.db.get(EmergencyProtocolRunModel, run_id)
        if run is None:
            raise ReportNotFoundError("Execucao de protocolo nao encontrada.")
        return run
