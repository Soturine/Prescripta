from types import SimpleNamespace

import pytest

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
from app.domain.prescription import PrescriptionInput
from app.services.clinical_decision_orchestrator import ClinicalDecisionOrchestrator


def patient(*, current_medications: list[str] | None = None) -> Patient:
    return Patient(
        id=1,
        name="Paciente fictício",
        birth_date=None,
        age=35,
        weight_kg=70,
        height_cm=170,
        allergies=[],
        comorbidities=[],
        current_medications=current_medications or [],
    )


def medication(**overrides: object) -> Medication:
    values: dict[str, object] = {
        "id": 1,
        "brand_name": "Medicamento fictício",
        "active_ingredient": "substancia teste",
        "therapeutic_class": "classe teste",
        "max_daily_dose_mg": 1000,
        "allowed_routes": ["oral"],
        "contraindications": [],
        "validation_status": "validated",
        "knowledge_source": "Fonte validada de teste",
        "dose_rule_validation_status": "validated",
        "dose_source_refs": ["dose:test:v1"],
        "policy_validation_status": "validated",
        "policy_source_refs": ["policy:test:v1"],
        "policy_version": "policy:test:v1",
    }
    values.update(overrides)
    return Medication(**values)


def user(*, role: str = "medico") -> SimpleNamespace:
    return SimpleNamespace(
        role=role,
        specialty_code="medicina_geral",
        credential_verification_status="verified",
    )


def prescription(*, dose_mg: float = 100) -> PrescriptionInput:
    return PrescriptionInput(
        dose_mg=dose_mg,
        frequency_per_day=1,
        route="oral",
        duration_days=1,
    )


def evaluate(**kwargs: object):
    return ClinicalDecisionOrchestrator().evaluate(
        patient=kwargs.get("patient", patient()),
        medication=kwargs.get("medication", medication()),
        prescription=kwargs.get("prescription", prescription()),
        user=kwargs.get("user", user()),
        missing_context=kwargs.get("missing_context", []),
    )


def test_evaluated_no_issue_requires_covered_sources_and_validated_rules() -> None:
    result = evaluate()

    assert result.envelope.decision_status == DecisionStatus.EVALUATED_NO_ISSUE
    assert result.envelope.coverage.status == CoverageStatus.COVERED
    assert result.envelope.legacy_status == PrescriptionStatus.RELEASED
    assert result.envelope.human_review_required is False
    assert "dentro da cobertura disponível" in result.envelope.recommendation


def test_pending_rule_never_produces_favorable_decision() -> None:
    result = evaluate(
        medication=medication(
            validation_status="demo",
            dose_rule_validation_status="pending_review",
            policy_validation_status="pending_review",
        )
    )

    assert result.envelope.coverage.status == CoverageStatus.RULE_PENDING_REVIEW
    assert result.envelope.decision_status == DecisionStatus.REVIEW_REQUIRED
    assert result.envelope.legacy_status == PrescriptionStatus.ATTENTION
    assert result.envelope.human_review_required is True


def test_missing_context_returns_abstention_instead_of_false_green() -> None:
    result = evaluate(missing_context=["alergias", "condição renal"])

    assert result.envelope.decision_status == DecisionStatus.INSUFFICIENT_DATA
    assert result.envelope.coverage.status == CoverageStatus.REQUIRED_CONTEXT_MISSING
    assert result.envelope.missing_data == ["alergias", "condição renal"]
    assert "Dados insuficientes" in result.envelope.recommendation


def test_critical_psychotropic_signal_blocks_aggregate_decision() -> None:
    result = evaluate(
        patient=patient(current_medications=["tranilcipromina"]),
        medication=medication(active_ingredient="sertralina"),
    )

    assert result.envelope.highest_severity == RiskLevel.CRITICAL
    assert result.envelope.decision_status == DecisionStatus.BLOCKED
    assert result.envelope.legacy_status == PrescriptionStatus.BLOCKED
    assert any(
        finding.code == "SEROTONERGIC_MAOI_COMBINATION"
        for finding in result.envelope.findings
    )


def test_policy_block_changes_aggregate_decision() -> None:
    result = evaluate(user=user(role="enfermagem"))

    assert result.prescribing_policy["status"] == "blocked_by_policy"
    assert result.envelope.decision_status == DecisionStatus.BLOCKED
    assert any(finding.module == "prescribing_policy" for finding in result.envelope.findings)


def test_dose_above_maximum_blocks_aggregate_decision() -> None:
    result = evaluate(prescription=prescription(dose_mg=1001))

    assert result.envelope.decision_status == DecisionStatus.BLOCKED
    assert any(finding.code == "MAX_DAILY_DOSE_EXCEEDED" for finding in result.envelope.findings)


def test_envelope_rejects_favorable_critical_contradiction() -> None:
    critical = ClinicalFinding(
        code="CRITICAL_TEST",
        title="Crítico",
        description="Teste",
        severity=RiskLevel.CRITICAL,
        module="test",
        recommendation="Revisar",
        hard_block=True,
    )

    with pytest.raises(ValueError, match="severidade crítica"):
        ClinicalDecisionEnvelope(
            decision_status=DecisionStatus.EVALUATED_NO_ISSUE,
            legacy_status=PrescriptionStatus.RELEASED,
            highest_severity=RiskLevel.CRITICAL,
            coverage=ClinicalCoverage(status=CoverageStatus.COVERED, evaluated=["test"]),
            findings=[critical],
            required_actions=[],
            missing_data=[],
            rule_versions=[],
            source_snapshot=[],
            override_policy={},
            human_review_required=False,
            correlation_id="test",
            recommendation="favorável",
        )
