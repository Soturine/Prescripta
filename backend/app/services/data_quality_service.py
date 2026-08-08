from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    CohortCriterionModel,
    CohortDefinitionVersionModel,
    ConceptSetVersionModel,
    DataQualityFindingModel,
    PatientClinicalTimelineEventModel,
    UserModel,
)
from app.domain.dose import parse_unit
from app.services.audit_service import AuditService


class DataQualityService:
    """Executa checks determinísticos e persiste apenas metadados sem PII."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, actor: UserModel) -> dict:
        now = datetime.now(UTC)
        candidates: list[dict] = []
        events = list(
            self.db.scalars(
                select(PatientClinicalTimelineEventModel).where(
                    PatientClinicalTimelineEventModel.institution_id == actor.institution_id
                ).order_by(
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
                    CohortCriterionModel.cohort_version_id
                    == CohortDefinitionVersionModel.id,
                )
                .where(
                    CohortDefinitionVersionModel.institution_id == actor.institution_id
                )
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
                    DataQualityFindingModel.institution_id == actor.institution_id,
                    DataQualityFindingModel.rule == candidate["rule"],
                    DataQualityFindingModel.resource_type == candidate["resource_type"],
                    DataQualityFindingModel.resource_id == candidate["resource_id"],
                    DataQualityFindingModel.field == candidate["field"],
                )
            )
            if existing is None:
                self.db.add(
                    DataQualityFindingModel(
                        institution_id=actor.institution_id,
                        detected_at=now,
                        status="open",
                        **candidate,
                    )
                )
                created += 1
        self.db.flush()
        open_findings = self.list(actor, status="open", limit=10_000)
        by_rule = Counter(item.rule for item in open_findings)
        AuditService(self.db).record_action(
            user=actor,
            action="data_quality.run",
            resource_type="institution",
            resource_id=actor.institution_id,
            status="completed",
            details={"findings_created": created, "findings_open": len(open_findings)},
        )
        return {
            "findings_created": created,
            "findings_open": len(open_findings),
            "by_rule": dict(by_rule),
        }

    def list(
        self,
        actor: UserModel,
        *,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[DataQualityFindingModel]:
        statement = select(DataQualityFindingModel).where(
            DataQualityFindingModel.institution_id == actor.institution_id
        )
        if status:
            statement = statement.where(DataQualityFindingModel.status == status)
        statement = statement.order_by(DataQualityFindingModel.detected_at.desc())
        return list(self.db.scalars(statement.offset(offset).limit(limit)))

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
            "source": "prescripta-data-quality-v1",
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
