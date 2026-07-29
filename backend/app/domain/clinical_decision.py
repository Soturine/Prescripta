from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from app.core.version import CLINICAL_DECISION_SCHEMA_VERSION
from app.domain.alert import Alert, PrescriptionStatus, RiskLevel


class DecisionStatus(StrEnum):
    NOT_EVALUATED = "not_evaluated"
    INSUFFICIENT_DATA = "insufficient_data"
    INSUFFICIENT_COVERAGE = "insufficient_coverage"
    REVIEW_REQUIRED = "review_required"
    BLOCKED = "blocked"
    EVALUATED_NO_ISSUE = "evaluated_no_issue"


class CoverageStatus(StrEnum):
    COVERED = "covered"
    PARTIALLY_COVERED = "partially_covered"
    NOT_COVERED = "not_covered"
    UNKNOWN_MEDICATION = "unknown_medication"
    RULE_PENDING_REVIEW = "rule_pending_review"
    SOURCE_EXPIRED = "source_expired"
    REQUIRED_CONTEXT_MISSING = "required_context_missing"
    UNSUPPORTED_DOSE_DIMENSION = "unsupported_dose_dimension"
    TERMINOLOGY_UNRESOLVED = "terminology_unresolved"


@dataclass(frozen=True)
class ClinicalFinding:
    code: str
    title: str
    description: str
    severity: RiskLevel
    module: str
    recommendation: str
    source_ids: list[str] = field(default_factory=list)
    rule_version: str | None = None
    validation_status: str = "demo"
    hard_block: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["severity"] = self.severity.value
        return payload

    def to_legacy_alert(self) -> Alert:
        return Alert(
            code=self.code,
            title=self.title,
            description=self.description,
            severity=self.severity,
            recommendation=self.recommendation,
        )


@dataclass(frozen=True)
class ClinicalCoverage:
    status: CoverageStatus
    evaluated: list[str]
    not_evaluated: list[dict[str, str]] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)

    @property
    def sufficient(self) -> bool:
        return self.status == CoverageStatus.COVERED

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["sufficient"] = self.sufficient
        return payload


@dataclass(frozen=True)
class ClinicalDecisionEnvelope:
    decision_status: DecisionStatus
    legacy_status: PrescriptionStatus
    highest_severity: RiskLevel
    coverage: ClinicalCoverage
    findings: list[ClinicalFinding]
    required_actions: list[str]
    missing_data: list[str]
    rule_versions: list[str]
    source_snapshot: list[dict[str, Any]]
    override_policy: dict[str, Any]
    human_review_required: bool
    correlation_id: str
    recommendation: str
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    schema_version: str = CLINICAL_DECISION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        favorable = self.decision_status == DecisionStatus.EVALUATED_NO_ISSUE
        if favorable and self.highest_severity == RiskLevel.CRITICAL:
            raise ValueError("Decisão favorável não pode conter severidade crítica.")
        if favorable and any(finding.hard_block for finding in self.findings):
            raise ValueError("Decisão favorável não pode conter hard block.")
        if favorable and not self.coverage.sufficient:
            raise ValueError("Decisão favorável exige cobertura suficiente.")
        if favorable and self.human_review_required:
            raise ValueError("Decisão favorável não pode exigir revisão humana.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision_status": self.decision_status.value,
            "legacy_status": self.legacy_status.value,
            "highest_severity": self.highest_severity.value,
            "coverage": self.coverage.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
            "required_actions": self.required_actions,
            "missing_data": self.missing_data,
            "rule_versions": self.rule_versions,
            "source_snapshot": self.source_snapshot,
            "override_policy": self.override_policy,
            "human_review_required": self.human_review_required,
            "evaluated_at": self.evaluated_at.isoformat(),
            "correlation_id": self.correlation_id,
            "recommendation": self.recommendation,
        }
