from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    CohortCriterionModel,
    CohortDefinitionVersionModel,
    CohortRunModel,
    ConceptSetVersionModel,
    DataQualityFindingModel,
    DataQualityRunModel,
    PatientClinicalTimelineEventModel,
    ResearchSnapshotModel,
    ResearchStudyModel,
    UserModel,
)
from app.domain.dose import parse_unit
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256


class DataQualityService:
    """Executa checks determinísticos e persiste apenas metadados sem PII."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(
        self,
        actor: UserModel,
        study_id: str | None = None,
        cohort_run_id: str | None = None,
    ) -> dict:
        now = datetime.now(UTC)
        if study_id:
            study = self.db.get(ResearchStudyModel, study_id)
            if study is None or study.institution_id != actor.institution_id:
                raise ValueError("Estudo não encontrado no escopo institucional.")
        cohort_run = self._resolve_cohort_run(actor, study_id, cohort_run_id)
        snapshot = self.db.scalar(
            select(ResearchSnapshotModel).where(
                ResearchSnapshotModel.cohort_run_id == cohort_run.id
            )
        )
        if snapshot is None:
            raise ValueError("Snapshot da coorte não encontrado.")
        ruleset_version = "prescripta-data-quality-v3"
        terminology_snapshot = {
            "source_version_refs": sorted(cohort_run.source_version_refs or [])
        }
        run = DataQualityRunModel(
            institution_id=actor.institution_id,
            study_id=cohort_run.study_id,
            cohort_run_id=cohort_run.id,
            data_snapshot_marker=cohort_run.data_snapshot_marker,
            data_snapshot_hash=snapshot.snapshot_hash,
            terminology_snapshot=terminology_snapshot,
            ruleset_version=ruleset_version,
            scope_status="scoped",
            status="running",
            summary={},
            content_hash=canonical_sha256({"status": "running"}),
            executed_by_user_id=actor.id,
            executed_at=now,
        )
        self.db.add(run)
        self.db.flush()
        candidates: list[dict] = []
        events = list(
            self.db.scalars(
                select(PatientClinicalTimelineEventModel)
                .where(PatientClinicalTimelineEventModel.institution_id == actor.institution_id)
                .order_by(
                    PatientClinicalTimelineEventModel.patient_id,
                    PatientClinicalTimelineEventModel.event_date,
                    PatientClinicalTimelineEventModel.created_at,
                )
            )
        )
        medication_starts: dict[tuple[int, str], datetime] = {}
        for item in events:
            occurred = self._aware(item.event_date or item.created_at)
            payload = item.payload or {}
            if occurred > now + timedelta(days=1):
                candidates.append(
                    self._candidate(
                        "impossible_future_date",
                        "high",
                        "patient_timeline_event",
                        item.id,
                        "event_date",
                        "Evento possui data futura impossível para o snapshot atual.",
                    )
                )
            start = self._date(payload.get("start"))
            end = self._date(payload.get("end"))
            if start and end and end < start:
                candidates.append(
                    self._candidate(
                        "end_before_start",
                        "high",
                        "patient_timeline_event",
                        item.id,
                        "payload.end",
                        "Data final ocorre antes da data inicial.",
                    )
                )
            for field in ("dose", "quantity", "amount"):
                value = payload.get(field)
                if isinstance(value, (int, float)) and value <= 0:
                    candidates.append(
                        self._candidate(
                            "non_positive_quantity",
                            "high",
                            "patient_timeline_event",
                            item.id,
                            f"payload.{field}",
                            "Dose ou quantidade deve ser maior que zero.",
                        )
                    )
            unit = payload.get("unit")
            if unit and parse_unit(str(unit)) is None:
                candidates.append(
                    self._candidate(
                        "unknown_unit",
                        "high",
                        "patient_timeline_event",
                        item.id,
                        "payload.unit",
                        "Unidade não reconhecida pelo contrato dimensional.",
                    )
                )
            if item.concept_code and not item.concept_system:
                candidates.append(
                    self._candidate(
                        "orphan_concept",
                        "moderate",
                        "patient_timeline_event",
                        item.id,
                        "concept_system",
                        "Código clínico sem sistema terminológico explícito.",
                    )
                )
            medication_key = (item.patient_id, (item.concept_code or item.concept_label or ""))
            if item.event_type == "medication_start":
                medication_starts[medication_key] = occurred
            if item.event_type == "medication_stop":
                known_start = medication_starts.get(medication_key)
                if known_start is None or occurred < known_start:
                    candidates.append(
                        self._candidate(
                            "medication_end_before_start",
                            "high",
                            "patient_timeline_event",
                            item.id,
                            "event_date",
                            "Término de medicamento ocorre antes ou sem início rastreável.",
                        )
                    )
        criteria = list(
            self.db.scalars(
                select(CohortCriterionModel)
                .join(
                    CohortDefinitionVersionModel,
                    CohortCriterionModel.cohort_version_id == CohortDefinitionVersionModel.id,
                )
                .where(CohortDefinitionVersionModel.institution_id == actor.institution_id)
                .where(CohortDefinitionVersionModel.id == cohort_run.cohort_version_id)
            )
        )
        for criterion in criteria:
            if criterion.criterion in {
                "condition",
                "medication_exposure",
                "measurement_exists",
                "procedure",
            }:
                concept = (
                    self.db.get(ConceptSetVersionModel, criterion.concept_set_version_id)
                    if criterion.concept_set_version_id
                    else None
                )
                if concept is None or concept.institution_id != actor.institution_id:
                    candidates.append(
                        self._candidate(
                            "criterion_without_concept_version",
                            "critical",
                            "cohort_criterion",
                            criterion.id,
                            "concept_set_version_id",
                            "Critério de estudo sem concept set/version institucional válido.",
                        )
                    )
        created = 0
        for candidate in candidates:
            existing = self.db.scalar(
                select(DataQualityFindingModel).where(
                    DataQualityFindingModel.run_id == run.id,
                    DataQualityFindingModel.rule == candidate["rule"],
                    DataQualityFindingModel.resource_type == candidate["resource_type"],
                    DataQualityFindingModel.resource_id == candidate["resource_id"],
                    DataQualityFindingModel.field == candidate["field"],
                )
            )
            if existing is None:
                self.db.add(
                    DataQualityFindingModel(
                        run_id=run.id,
                        institution_id=actor.institution_id,
                        detected_at=now,
                        status="open",
                        **candidate,
                    )
                )
                created += 1
        self.db.flush()
        open_findings = self.list(actor, status="open", run_id=run.id, limit=10_000)
        by_rule = Counter(item.rule for item in open_findings)
        by_severity = Counter(item.severity for item in open_findings)
        summary = {
            "findings_created": created,
            "findings_open": len(open_findings),
            "by_rule": dict(by_rule),
            "by_severity": dict(by_severity),
            "dimensions": {
                "completeness": by_rule.get("orphan_concept", 0),
                "validity": sum(
                    by_rule[name]
                    for name in (
                        "impossible_future_date",
                        "end_before_start",
                        "non_positive_quantity",
                        "unknown_unit",
                    )
                ),
                "consistency": by_rule.get("medication_end_before_start", 0),
                "conformance": by_rule.get("criterion_without_concept_version", 0),
            },
            "analysis_blocked": bool(by_severity.get("critical")),
        }
        run.status = "completed"
        run.summary = summary
        run.content_hash = canonical_sha256(
            {
                "institution_id": actor.institution_id,
                "study_id": cohort_run.study_id,
                "cohort_run_id": cohort_run.id,
                "data_snapshot_marker": cohort_run.data_snapshot_marker,
                "data_snapshot_hash": snapshot.snapshot_hash,
                "terminology_snapshot": terminology_snapshot,
                "summary": summary,
                "ruleset": ruleset_version,
            }
        )
        self.db.flush()
        AuditService(self.db).record_action(
            user=actor,
            action="data_quality.run",
            resource_type="institution",
            resource_id=actor.institution_id,
            status="completed",
            details={
                "study_id": cohort_run.study_id,
                "cohort_run_id": cohort_run.id,
                "data_snapshot_hash": snapshot.snapshot_hash,
                "ruleset_version": ruleset_version,
                "findings_created": created,
                "findings_open": len(open_findings),
            },
        )
        return {
            "id": run.id,
            "institution_id": run.institution_id,
            "study_id": run.study_id,
            "cohort_run_id": run.cohort_run_id,
            "data_snapshot_marker": run.data_snapshot_marker,
            "data_snapshot_hash": run.data_snapshot_hash,
            "terminology_snapshot": run.terminology_snapshot,
            "ruleset_version": run.ruleset_version,
            "scope_status": run.scope_status,
            "status": run.status,
            "summary": summary,
            "content_hash": run.content_hash,
            "executed_by_user_id": run.executed_by_user_id,
            "executed_at": run.executed_at,
            **{key: summary[key] for key in ("findings_created", "findings_open", "by_rule")},
        }

    def run_legacy_timeline(self, actor: UserModel) -> dict:
        """Compatibility-only timeline checks; never eligible as an analysis gate."""
        now = datetime.now(UTC)
        ruleset_version = "prescripta-data-quality-v2-legacy"
        run = DataQualityRunModel(
            institution_id=actor.institution_id,
            study_id=None,
            cohort_run_id=None,
            data_snapshot_marker=None,
            data_snapshot_hash=None,
            terminology_snapshot={},
            ruleset_version=ruleset_version,
            scope_status="legacy_unscoped",
            status="running",
            summary={},
            content_hash=canonical_sha256({"status": "running", "scope": "legacy_unscoped"}),
            executed_by_user_id=actor.id,
            executed_at=now,
        )
        self.db.add(run)
        self.db.flush()
        candidates: list[dict] = []
        events = list(
            self.db.scalars(
                select(PatientClinicalTimelineEventModel).where(
                    PatientClinicalTimelineEventModel.institution_id == actor.institution_id
                )
            )
        )
        for item in events:
            occurred = self._aware(item.event_date or item.created_at)
            payload = item.payload or {}
            if occurred > now + timedelta(days=1):
                candidates.append(
                    self._candidate(
                        "impossible_future_date", "high", "patient_timeline_event",
                        item.id, "event_date", "Evento possui data futura impossível.",
                    )
                )
            for field in ("dose", "quantity", "amount"):
                value = payload.get(field)
                if isinstance(value, (int, float)) and value <= 0:
                    candidates.append(
                        self._candidate(
                            "non_positive_quantity", "high", "patient_timeline_event",
                            item.id,
                            f"payload.{field}",
                            "Dose ou quantidade deve ser maior que zero.",
                        )
                    )
            unit = payload.get("unit")
            if unit and parse_unit(str(unit)) is None:
                candidates.append(
                    self._candidate(
                        "unknown_unit", "high", "patient_timeline_event",
                        item.id, "payload.unit", "Unidade não reconhecida.",
                    )
                )
            if item.concept_code and not item.concept_system:
                candidates.append(
                    self._candidate(
                        "orphan_concept", "moderate", "patient_timeline_event",
                        item.id, "concept_system", "Código sem sistema terminológico explícito.",
                    )
                )
        for candidate in candidates:
            self.db.add(
                DataQualityFindingModel(
                    run_id=run.id,
                    institution_id=actor.institution_id,
                    detected_at=now,
                    status="open",
                    **candidate,
                )
            )
        self.db.flush()
        by_rule = dict(Counter(item["rule"] for item in candidates))
        summary = {
            "findings_created": len(candidates),
            "findings_open": len(candidates),
            "by_rule": by_rule,
            "by_severity": dict(Counter(item["severity"] for item in candidates)),
            "dimensions": {},
            "analysis_blocked": False,
            "analysis_eligible": False,
            "legacy_unscoped": True,
        }
        run.status = "completed"
        run.summary = summary
        run.content_hash = canonical_sha256(
            {"institution_id": actor.institution_id, "ruleset": ruleset_version, "summary": summary}
        )
        self.db.flush()
        AuditService(self.db).record_action(
            user=actor,
            action="data_quality.run_legacy",
            resource_type="institution",
            resource_id=actor.institution_id,
            status="completed",
            details={"scope_status": "legacy_unscoped", "findings_created": len(candidates)},
        )
        return {
            "id": run.id,
            "institution_id": run.institution_id,
            "study_id": None,
            "cohort_run_id": None,
            "data_snapshot_marker": None,
            "data_snapshot_hash": None,
            "terminology_snapshot": {},
            "ruleset_version": ruleset_version,
            "scope_status": "legacy_unscoped",
            "status": "completed",
            "summary": summary,
            "content_hash": run.content_hash,
            "executed_by_user_id": actor.id,
            "executed_at": now,
            **{key: summary[key] for key in ("findings_created", "findings_open", "by_rule")},
        }

    def acknowledge(
        self, finding_id: str, resolution: str, actor: UserModel
    ) -> DataQualityFindingModel:
        finding = self.db.get(DataQualityFindingModel, finding_id)
        if finding is None or finding.institution_id != actor.institution_id:
            raise ValueError("Finding não encontrado no escopo institucional.")
        if finding.status != "open":
            raise ValueError("Finding já foi tratado.")
        if finding.severity == "critical":
            raise ValueError("Finding crítico não pode ser liberado por acknowledgement.")
        finding.status = "acknowledged"
        finding.resolution = resolution
        finding.resolved_by_user_id = actor.id
        finding.resolved_at = datetime.now(UTC)
        self.db.flush()
        AuditService(self.db).record_action(
            user=actor,
            action="data_quality.acknowledge",
            resource_type="data_quality_finding",
            resource_id=finding.id,
            status=finding.status,
            details={"rule": finding.rule, "resolution": resolution},
        )
        return finding

    def list(
        self,
        actor: UserModel,
        *,
        status: str | None = None,
        run_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[DataQualityFindingModel]:
        statement = select(DataQualityFindingModel).where(
            DataQualityFindingModel.institution_id == actor.institution_id
        )
        if status:
            statement = statement.where(DataQualityFindingModel.status == status)
        if run_id:
            statement = statement.where(DataQualityFindingModel.run_id == run_id)
        statement = statement.order_by(DataQualityFindingModel.detected_at.desc())
        return list(self.db.scalars(statement.offset(offset).limit(limit)))

    def _resolve_cohort_run(
        self,
        actor: UserModel,
        study_id: str | None,
        cohort_run_id: str | None,
    ) -> CohortRunModel:
        if cohort_run_id:
            run = self.db.get(CohortRunModel, cohort_run_id)
            if run is None or run.institution_id != actor.institution_id:
                raise ValueError("Execução de coorte não encontrada no escopo institucional.")
            if study_id and run.study_id != study_id:
                raise ValueError("Execução de coorte não pertence ao estudo informado.")
            return run
        if not study_id:
            raise ValueError("Data Quality v0.9.1 exige study_id e cohort_run_id explícitos.")
        runs = list(
            self.db.scalars(
                select(CohortRunModel).where(
                    CohortRunModel.institution_id == actor.institution_id,
                    CohortRunModel.study_id == study_id,
                    CohortRunModel.status == "completed_demo",
                )
            )
        )
        if len(runs) != 1:
            raise ValueError(
                "Informe cohort_run_id explicitamente; o estudo não possui "
                "exatamente uma coorte executada."
            )
        return runs[0]

    @staticmethod
    def _candidate(
        rule: str,
        severity: str,
        resource_type: str,
        resource_id: str,
        field: str,
        message: str,
    ) -> dict:
        return {
            "rule": rule,
            "severity": severity,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "field": field,
            "message": message,
            "source": "prescripta-data-quality-v2",
        }

    @staticmethod
    def _date(value) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
        return DataQualityService._aware(parsed)

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
