from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.domain.alert import PrescriptionStatus, RiskLevel
from app.domain.clinical_decision import (
    ClinicalCoverage,
    ClinicalDecisionEnvelope,
    ClinicalFinding,
    CoverageStatus,
    DecisionStatus,
)
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput, PrescriptionResult
from app.services.dose_intelligence import DoseIntelligenceService
from app.services.prescribing_policy import PrescribingPolicyService
from app.services.psychotropic_safety import PsychotropicSafetyService
from app.services.risk_engine import RiskEngine

RISK_ORDER = {
    RiskLevel.LOW: 0,
    RiskLevel.MODERATE: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}
PENDING_STATUSES = {"demo", "demo_seed", "pending_review", "demo_curated"}
DOSE_BLOCKING_STATUSES = {
    "above_maximum",
    "above_procedure_maximum",
    "above_cumulative_maximum",
}
POLICY_BLOCKING_STATUSES = {"blocked_by_policy"}


@dataclass(frozen=True)
class ClinicalDecisionEvaluation:
    envelope: ClinicalDecisionEnvelope
    legacy_result: PrescriptionResult
    dose_intelligence: dict[str, Any]
    psychotropic_safety: list[dict[str, Any]]
    prescribing_policy: dict[str, Any]


class ClinicalDecisionOrchestrator:
    """Executa os módulos determinísticos e produz uma única decisão segura."""

    def __init__(self) -> None:
        self.risk_engine = RiskEngine()
        self.dose_service = DoseIntelligenceService()
        self.psychotropic_service = PsychotropicSafetyService()
        self.policy_service = PrescribingPolicyService()

    def evaluate(
        self,
        *,
        patient: Patient,
        medication: Medication,
        prescription: PrescriptionInput,
        user: Any,
        functional_profile: Any | None = None,
        rag_evidence: list[dict[str, Any]] | None = None,
        missing_context: list[str] | None = None,
        correlation_id: str | None = None,
    ) -> ClinicalDecisionEvaluation:
        base = self.risk_engine.evaluate(patient, medication, prescription)
        dose = self.dose_service.evaluate(
            self._dose_rule(medication), patient, prescription
        ).to_dict()
        psychotropic = [
            signal.to_dict()
            for signal in self.psychotropic_service.evaluate(
                medication,
                patient,
                functional_profile=functional_profile,
            )
        ]
        policy = self.policy_service.evaluate(user, medication, prescription, patient).to_dict()
        findings = self._findings(base, dose, psychotropic, policy, medication)
        missing = self._unique([*(missing_context or []), *dose.get("missing_data", [])])
        coverage = self._coverage(
            medication=medication,
            dose=dose,
            policy=policy,
            missing=missing,
            rag_evidence=rag_evidence or [],
        )
        decision_status = self._decision_status(findings, dose, policy, coverage, missing)
        highest_severity = self._highest_severity(findings)
        legacy_status = self._legacy_status(decision_status)
        required_actions = self._required_actions(findings, coverage, missing)
        human_review = decision_status != DecisionStatus.EVALUATED_NO_ISSUE
        envelope = ClinicalDecisionEnvelope(
            decision_status=decision_status,
            legacy_status=legacy_status,
            highest_severity=highest_severity,
            coverage=coverage,
            findings=findings,
            required_actions=required_actions,
            missing_data=missing,
            rule_versions=self._rule_versions(medication, findings),
            source_snapshot=self._source_snapshot(medication, rag_evidence or []),
            override_policy=self._override_policy(medication, policy),
            human_review_required=human_review,
            correlation_id=correlation_id or str(uuid4()),
            recommendation=self._recommendation(decision_status, coverage),
            evaluated_at=datetime.now(UTC),
        )
        legacy_result = PrescriptionResult(
            status=envelope.legacy_status,
            risk_level=envelope.highest_severity,
            alerts=[finding.to_legacy_alert() for finding in findings],
            recommendation=envelope.recommendation,
            human_review_required=envelope.human_review_required,
            dose_summary=base.dose_summary,
            compatibility={
                **base.compatibility,
                "review_required": envelope.human_review_required,
                "coverage_status": envelope.coverage.status.value,
            },
            clinical_context_graph=base.clinical_context_graph,
        )
        return ClinicalDecisionEvaluation(
            envelope=envelope,
            legacy_result=legacy_result,
            dose_intelligence=dose,
            psychotropic_safety=psychotropic,
            prescribing_policy=policy,
        )

    def _dose_rule(self, medication: Medication) -> dict[str, Any]:
        return {
            "calculation_basis": medication.dose_calculation_basis,
            "dose_unit": medication.dose_unit,
            "dose_per_basis": medication.dose_mg_per_kg,
            "usual_low": medication.usual_dose_low,
            "usual_high": medication.usual_dose_high,
            "max_daily": medication.max_daily_dose_mg,
            "dose_dimension": medication.dose_dimension,
            "max_daily_unit": medication.max_daily_dose_unit,
            "max_per_procedure": medication.max_per_procedure,
            "max_per_procedure_unit": medication.max_per_procedure_unit,
            "max_rate": medication.max_rate,
            "rate_unit": medication.rate_unit,
            "max_cumulative": medication.max_cumulative_dose_mg,
            "allowed_routes": medication.allowed_routes,
            "validation_status": medication.dose_rule_validation_status,
            "source_refs": medication.dose_source_refs or [],
        }

    def _findings(
        self,
        base: PrescriptionResult,
        dose: dict[str, Any],
        psychotropic: list[dict[str, Any]],
        policy: dict[str, Any],
        medication: Medication,
    ) -> list[ClinicalFinding]:
        findings = [
            ClinicalFinding(
                code=alert.code,
                title=alert.title,
                description=alert.description,
                severity=alert.severity,
                module="risk_engine",
                recommendation=alert.recommendation,
                source_ids=list(medication.dose_source_refs or []),
                validation_status=medication.validation_status,
                hard_block=alert.severity == RiskLevel.CRITICAL,
            )
            for alert in base.alerts
        ]
        for item in dose.get("alerts", []):
            code = str(item.get("code") or "DOSE_REVIEW")
            severity = self._risk_level(item.get("severity"))
            findings.append(
                ClinicalFinding(
                    code=code,
                    title="Resultado de dose a revisar",
                    description=f"Dose Intelligence retornou {dose.get('status')}.",
                    severity=severity,
                    module="dose_intelligence",
                    recommendation="Revisar dimensão, regra, fonte e cálculo da dose.",
                    source_ids=list(dose.get("source_refs") or []),
                    validation_status=str(dose.get("validation_status") or "unknown"),
                    hard_block=dose.get("status") in DOSE_BLOCKING_STATUSES,
                )
            )
        for signal in psychotropic:
            findings.append(
                ClinicalFinding(
                    code=str(signal["code"]),
                    title=str(signal["title"]),
                    description=str(signal["description"]),
                    severity=self._risk_level(signal.get("severity")),
                    module="psychotropic_safety",
                    recommendation=str(signal.get("recommendation") or "Revisar clinicamente."),
                    source_ids=list(signal.get("source_ids") or []),
                    validation_status=str(signal.get("policy_status") or "demo_seed"),
                    hard_block=str(signal.get("severity")) == RiskLevel.CRITICAL.value,
                )
            )
        if policy.get("status") != "allowed":
            blocked = policy.get("status") in POLICY_BLOCKING_STATUSES
            findings.append(
                ClinicalFinding(
                    code=f"POLICY_{str(policy.get('status')).upper()}",
                    title="Política do prescritor exige revisão",
                    description="; ".join(policy.get("warnings") or [str(policy.get("status"))]),
                    severity=RiskLevel.CRITICAL if blocked else RiskLevel.MODERATE,
                    module="prescribing_policy",
                    recommendation="Atender às ações da policy antes de prosseguir.",
                    source_ids=list(policy.get("source_refs") or []),
                    rule_version=self._policy_version(policy),
                    validation_status=self._policy_validation(policy),
                    hard_block=blocked,
                )
            )
        unique: dict[tuple[str, str], ClinicalFinding] = {}
        for finding in findings:
            key = (finding.module, finding.code)
            current = unique.get(key)
            if current is None or RISK_ORDER[finding.severity] > RISK_ORDER[current.severity]:
                unique[key] = finding
        return list(unique.values())

    def _coverage(
        self,
        *,
        medication: Medication,
        dose: dict[str, Any],
        policy: dict[str, Any],
        missing: list[str],
        rag_evidence: list[dict[str, Any]],
    ) -> ClinicalCoverage:
        evaluated = [
            "risk_engine",
            "allergies",
            "interactions",
            "dose",
            "psychotropic_safety",
            "prescribing_policy",
            "functional_context",
        ]
        not_evaluated: list[dict[str, str]] = []
        reasons: list[str] = []
        source_ids = self._source_ids(medication, rag_evidence)
        if medication.id is None:
            return ClinicalCoverage(
                status=CoverageStatus.UNKNOWN_MEDICATION,
                evaluated=[],
                not_evaluated=[{"module": "medication", "reason": "medicamento desconhecido"}],
                reasons=["O medicamento não foi resolvido no catálogo canônico."],
            )
        if dose.get("status") == "unsupported_dimension":
            return ClinicalCoverage(
                status=CoverageStatus.UNSUPPORTED_DOSE_DIMENSION,
                evaluated=evaluated,
                not_evaluated=[{"module": "dose", "reason": "dimensão não suportada"}],
                reasons=["A dose não pode ser comparada com segurança à regra cadastrada."],
                source_ids=source_ids,
            )
        if missing:
            reasons.append("Contexto obrigatório ausente: " + ", ".join(missing))
            not_evaluated.append({"module": "context", "reason": "dados obrigatórios ausentes"})
            return ClinicalCoverage(
                status=CoverageStatus.REQUIRED_CONTEXT_MISSING,
                evaluated=evaluated,
                not_evaluated=not_evaluated,
                reasons=reasons,
                source_ids=source_ids,
            )
        validation_statuses = {
            medication.validation_status,
            str(dose.get("validation_status") or "unknown"),
            self._policy_validation(policy),
        }
        if validation_statuses & PENDING_STATUSES:
            reasons.append("Uma ou mais regras/fontes permanecem demonstrativas ou pendentes.")
            return ClinicalCoverage(
                status=CoverageStatus.RULE_PENDING_REVIEW,
                evaluated=evaluated,
                reasons=reasons,
                source_ids=source_ids,
            )
        if not source_ids:
            return ClinicalCoverage(
                status=CoverageStatus.NOT_COVERED,
                evaluated=evaluated,
                not_evaluated=[{"module": "sources", "reason": "fonte ausente"}],
                reasons=["Nenhuma fonte rastreável foi associada à avaliação."],
            )
        return ClinicalCoverage(
            status=CoverageStatus.COVERED,
            evaluated=evaluated,
            source_ids=source_ids,
        )

    def _decision_status(
        self,
        findings: list[ClinicalFinding],
        dose: dict[str, Any],
        policy: dict[str, Any],
        coverage: ClinicalCoverage,
        missing: list[str],
    ) -> DecisionStatus:
        if (
            any(
                finding.hard_block or finding.severity == RiskLevel.CRITICAL
                for finding in findings
            )
            or dose.get("status") in DOSE_BLOCKING_STATUSES
            or policy.get("status") in POLICY_BLOCKING_STATUSES
        ):
            return DecisionStatus.BLOCKED
        if missing or coverage.status == CoverageStatus.REQUIRED_CONTEXT_MISSING:
            return DecisionStatus.INSUFFICIENT_DATA
        if coverage.status in {
            CoverageStatus.NOT_COVERED,
            CoverageStatus.UNKNOWN_MEDICATION,
            CoverageStatus.SOURCE_EXPIRED,
            CoverageStatus.UNSUPPORTED_DOSE_DIMENSION,
            CoverageStatus.TERMINOLOGY_UNRESOLVED,
        }:
            return DecisionStatus.INSUFFICIENT_COVERAGE
        if findings or coverage.status != CoverageStatus.COVERED:
            return DecisionStatus.REVIEW_REQUIRED
        return DecisionStatus.EVALUATED_NO_ISSUE

    def _required_actions(
        self,
        findings: list[ClinicalFinding],
        coverage: ClinicalCoverage,
        missing: list[str],
    ) -> list[str]:
        actions = [finding.recommendation for finding in findings if finding.recommendation]
        if missing:
            actions.append("Completar os dados obrigatórios antes de interpretar a decisão.")
        if not coverage.sufficient:
            actions.append("Revisar cobertura, fontes e versões com profissional habilitado.")
        return self._unique(actions)

    def _recommendation(
        self,
        status: DecisionStatus,
        coverage: ClinicalCoverage,
    ) -> str:
        if status == DecisionStatus.BLOCKED:
            return "Não prosseguir sem resolver os bloqueios e registrar revisão humana."
        if status == DecisionStatus.INSUFFICIENT_DATA:
            return "Dados insuficientes para uma conclusão; completar o contexto e reavaliar."
        if status == DecisionStatus.INSUFFICIENT_COVERAGE:
            return (
                "Cobertura insuficiente para uma conclusão; não interpretar ausência de alerta "
                "como segurança."
            )
        if status == DecisionStatus.REVIEW_REQUIRED:
            return "Revisão humana obrigatória antes de qualquer decisão clínica."
        if coverage.sufficient:
            return (
                "Nenhum problema foi identificado dentro da cobertura disponível e dos dados "
                "informados."
            )
        raise ValueError("Recomendação favorável exige cobertura suficiente.")

    def _highest_severity(self, findings: list[ClinicalFinding]) -> RiskLevel:
        if not findings:
            return RiskLevel.LOW
        return max((finding.severity for finding in findings), key=RISK_ORDER.__getitem__)

    def _legacy_status(self, status: DecisionStatus) -> PrescriptionStatus:
        if status == DecisionStatus.BLOCKED:
            return PrescriptionStatus.BLOCKED
        if status == DecisionStatus.EVALUATED_NO_ISSUE:
            return PrescriptionStatus.RELEASED
        return PrescriptionStatus.ATTENTION

    def _rule_versions(
        self,
        medication: Medication,
        findings: list[ClinicalFinding],
    ) -> list[str]:
        versions = [
            "risk_engine:1",
            f"dose:{medication.id}:{medication.source_version or 'unversioned'}",
            f"policy:{medication.policy_version}",
            "psychotropic_safety:demo-v0.8.4",
        ]
        versions.extend(
            f"{finding.module}:{finding.rule_version}"
            for finding in findings
            if finding.rule_version
        )
        return self._unique(versions)

    def _source_snapshot(
        self,
        medication: Medication,
        rag_evidence: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        sources = [
            {
                "source_id": f"medication:{medication.id or 'unknown'}",
                "source_type": medication.evidence_source_type,
                "source_url": medication.evidence_source_url,
                "jurisdiction": medication.source_jurisdiction,
                "validation_status": medication.validation_status,
                "source_version": medication.source_version,
            }
        ]
        for item in rag_evidence:
            source_id = str(item.get("source_id") or item.get("source") or "").strip()
            if source_id:
                sources.append(
                    {
                        "source_id": source_id,
                        "source_type": "lexical_demo",
                        "source_url": None,
                        "jurisdiction": item.get("jurisdiction") or "unknown",
                        "validation_status": item.get("validation_status") or "educational",
                        "source_version": item.get("version"),
                    }
                )
        return sources

    def _source_ids(
        self,
        medication: Medication,
        rag_evidence: list[dict[str, Any]],
    ) -> list[str]:
        sources = list(medication.dose_source_refs or []) + list(
            medication.policy_source_refs or []
        )
        if medication.evidence_source_url or medication.knowledge_source:
            sources.append(f"medication:{medication.id}")
        sources.extend(
            str(item.get("source_id") or item.get("source"))
            for item in rag_evidence
            if item.get("source_id") or item.get("source")
        )
        return self._unique(sources)

    def _override_policy(
        self,
        medication: Medication,
        policy: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "allowed": bool(medication.override_allowed),
            "reason_required": bool(medication.override_reason_required),
            "second_reviewer_role": medication.second_reviewer_role,
            "policy_status": policy.get("status"),
            "note": "Override nunca reduz severidade nem apaga o achado original.",
        }

    def _policy_version(self, policy: dict[str, Any]) -> str | None:
        rules = policy.get("rules_applied") or []
        return str(rules[0].get("policy_version")) if rules else None

    def _policy_validation(self, policy: dict[str, Any]) -> str:
        rules = policy.get("rules_applied") or []
        return str(rules[0].get("validation_status") or "unknown") if rules else "unknown"

    def _risk_level(self, value: Any) -> RiskLevel:
        normalized = str(getattr(value, "value", value) or "baixo")
        return next((level for level in RiskLevel if level.value == normalized), RiskLevel.LOW)

    def _unique(self, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value for value in values if value))
