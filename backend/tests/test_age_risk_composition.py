"""PRE-01: composição única e monotônica do risco agregado por idade.

Contrato (docs/clinical-rules/risk-engine.md): idade >= 65 eleva o risco agregado em um nível.
A elevação por idade, isolada, não cria bloqueio (teto ALTO): CRITICAL/BLOCKED exige um achado
crítico próprio. RiskEngine (usado por alternativas) e o orquestrador (checagem e CDS) devem
produzir o mesmo nível para o mesmo paciente.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.alert import RiskLevel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.services.clinical_decision_orchestrator import ClinicalDecisionOrchestrator
from app.services.risk_engine import RISK_ORDER, RiskEngine, compose_risk_level


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


def user() -> SimpleNamespace:
    return SimpleNamespace(
        role="medico",
        specialty_code="medicina_geral",
        credential_verification_status="verified",
    )


def evaluate(*, patient, medication, prescription, user):
    return ClinicalDecisionOrchestrator().evaluate(
        patient=patient,
        medication=medication,
        prescription=prescription,
        user=user,
        missing_context=[],
        rag_evidence=[],
    )


def _rank(level: RiskLevel) -> int:
    return RISK_ORDER.index(level)


def _patient(age: int, current_medications: list[str] | None = None) -> Patient:
    return Patient(
        id=1,
        name="Paciente fictício",
        birth_date=None,
        age=age,
        weight_kg=70,
        height_cm=170,
        allergies=[],
        comorbidities=[],
        current_medications=current_medications or [],
    )


SEVERITIES = st.lists(st.sampled_from(RISK_ORDER), max_size=6)


@given(SEVERITIES, st.sampled_from(RISK_ORDER), st.booleans())
def test_adding_a_finding_never_lowers_the_aggregate(severities, extra, elderly) -> None:
    before = compose_risk_level(severities, elderly=elderly)
    after = compose_risk_level([*severities, extra], elderly=elderly)
    assert _rank(after) >= _rank(before)


@given(SEVERITIES)
def test_age_elevates_one_level_never_lowers_and_never_blocks_alone(severities) -> None:
    young = compose_risk_level(severities, elderly=False)
    old = compose_risk_level(severities, elderly=True)
    assert _rank(old) >= _rank(young)
    assert _rank(old) - _rank(young) <= 1
    if young != RiskLevel.CRITICAL:
        assert old != RiskLevel.CRITICAL
        assert _rank(old) == min(_rank(young) + 1, _rank(RiskLevel.HIGH))


@pytest.mark.parametrize(
    ("age", "current_medications", "elderly_caution", "expected"),
    [
        (64, [], False, RiskLevel.LOW),
        (65, [], False, RiskLevel.MODERATE),
        (70, [], False, RiskLevel.MODERATE),
        (64, ["a", "b", "c", "d", "e"], False, RiskLevel.MODERATE),
        (70, ["a", "b", "c", "d", "e"], False, RiskLevel.HIGH),
        (70, [], True, RiskLevel.HIGH),
        (70, ["a", "b", "c", "d", "e"], True, RiskLevel.HIGH),
    ],
)
def test_risk_engine_and_orchestrator_agree_on_age_composition(
    age: int,
    current_medications: list[str],
    elderly_caution: bool,
    expected: RiskLevel,
) -> None:
    patient = _patient(age, current_medications)
    drug = medication(elderly_caution=elderly_caution)
    prescription = PrescriptionInput(dose_mg=100, frequency_per_day=1, route="oral")

    base = RiskEngine().evaluate(patient, drug, prescription)
    orchestrated = evaluate(
        patient=patient, medication=drug, prescription=prescription, user=user()
    )

    assert base.risk_level == expected
    assert orchestrated.envelope.highest_severity == expected
    assert orchestrated.legacy_result.risk_level == expected


def test_elderly_caution_never_lowers_an_age_elevated_high_risk() -> None:
    """Antes: base ALTO + idade -> CRÍTICO, mas + cautela em idoso -> ALTO (não monotônico)."""
    patient = _patient(70)
    prescription = PrescriptionInput(dose_mg=100, frequency_per_day=1, route="intravenosa")
    without_caution = RiskEngine().evaluate(patient, _engine_med(False), prescription)
    with_caution = RiskEngine().evaluate(patient, _engine_med(True), prescription)
    assert _rank(with_caution.risk_level) >= _rank(without_caution.risk_level)


def _engine_med(elderly_caution: bool) -> Medication:
    return Medication(
        id=1,
        brand_name="Seguro",
        active_ingredient="seguridina",
        therapeutic_class="teste",
        max_daily_dose_mg=1000,
        allowed_routes=["oral"],
        contraindications=[],
        elderly_caution=elderly_caution,
    )
