"""Cenários adversariais derivados de alertas públicos de tecnovigilância (Anvisa) sobre CPOE.

Não reproduzem software de terceiros; usam as CLASSES de falha descritas publicamente:
- Alerta 4612 (2024): erro de conversão de unidade gerando cálculo errado;
- Alerta 5063 (2025): ausência de alerta para concentração de eletrólito acima do máximo.
Prescripta deve converter exatamente o que entende e falhar fechado no que não entende.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.alert import RiskLevel
from app.domain.dose_units import convert_value, parse_unit
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.services.clinical_decision_orchestrator import ClinicalDecisionOrchestrator
from app.services.dose_calculator import check_max_daily_dose

MASS = ["g", "mg", "mcg", "ng"]
VALUES = st.decimals(min_value=Decimal("0.001"), max_value=Decimal("100000"), places=3)


@given(VALUES, st.sampled_from(MASS), st.sampled_from(MASS))
def test_mass_conversion_round_trips_exactly(value, source, target) -> None:
    converted = convert_value(value, source, target)
    assert convert_value(converted, target, source) == value


@pytest.mark.parametrize("alias", ["mcg", "ug", "µg", "μg", "MCG"])
def test_microgram_aliases_are_one_thousandth_of_mg(alias: str) -> None:
    assert convert_value(Decimal("1000"), alias, "mg") == Decimal("1")


@pytest.mark.parametrize(
    ("source", "target"),
    [("mg", "ml"), ("mg/kg", "mg"), ("mg/h", "mg"), ("mg/ml", "mg"), ("mg", "meq"), ("ui", "mg")],
)
def test_incompatible_or_unknown_units_never_convert(source: str, target: str) -> None:
    assert convert_value(Decimal("1"), source, target) is None


@pytest.mark.parametrize("unit", ["meq", "mEq", "mmol", "UI", "%"])
def test_unknown_units_are_not_parsed(unit: str) -> None:
    assert parse_unit(unit) is None


def _kcl(limit_unit: str) -> Medication:
    return Medication(
        id=99,
        brand_name="Cloreto de potássio sintético",
        active_ingredient="cloreto de potassio",
        therapeutic_class="eletrólito",
        max_daily_dose_mg=40,
        max_daily_dose_unit=limit_unit,
        allowed_routes=["intravenosa"],
        contraindications=[],
        validation_status="validated",
        knowledge_source="fonte sintética",
        dose_rule_validation_status="validated",
        dose_source_refs=["dose:synthetic:v1"],
        policy_validation_status="validated",
        policy_source_refs=["policy:synthetic:v1"],
        policy_version="policy:synthetic:v1",
    )


def test_limit_in_unsupported_unit_raises_alert_instead_of_silence() -> None:
    """Classe do alerta 5063: limite em mEq não pode virar 'sem alerta'."""
    alerts = check_max_daily_dose(
        _kcl("meq"), PrescriptionInput(dose_mg=3000, frequency_per_day=4, route="intravenosa")
    )
    assert [alert.code for alert in alerts] == ["DAILY_DOSE_DIMENSION_UNPROVEN"]
    assert alerts[0].severity == RiskLevel.HIGH


def test_unsupported_limit_unit_never_yields_favorable_decision() -> None:
    evaluation = ClinicalDecisionOrchestrator().evaluate(
        patient=Patient(
            id=1,
            name="Paciente fictício",
            birth_date=None,
            age=50,
            weight_kg=70,
            height_cm=170,
            allergies=[],
            comorbidities=[],
            current_medications=[],
        ),
        medication=_kcl("meq"),
        prescription=PrescriptionInput(dose_mg=3000, frequency_per_day=4, route="intravenosa"),
        user=SimpleNamespace(
            role="medico",
            specialty_code="medicina_geral",
            credential_verification_status="verified",
        ),
        missing_context=[],
        rag_evidence=[],
    )
    assert evaluation.envelope.decision_status.value != "evaluated_no_issue"
    assert evaluation.envelope.human_review_required is True


def _validated_patient_eval(prescription: PrescriptionInput, medication: Medication):
    return ClinicalDecisionOrchestrator().evaluate(
        patient=Patient(
            id=1,
            name="Paciente fictício",
            birth_date=None,
            age=50,
            weight_kg=70,
            height_cm=170,
            allergies=[],
            comorbidities=[],
            current_medications=[],
        ),
        medication=medication,
        prescription=prescription,
        user=SimpleNamespace(
            role="medico",
            specialty_code="medicina_geral",
            credential_verification_status="verified",
        ),
        missing_context=[],
        rag_evidence=[],
    )


def test_concentration_without_ceiling_rule_is_declared_not_evaluated() -> None:
    """NEW-15: concentração informada sem regra de teto não pode resultar em 'sem problema'."""
    from app.domain.dose import MedicationDoseInput

    drug = _kcl("mg")
    drug = Medication(**{**drug.__dict__, "max_daily_dose_mg": 100000})
    plain = PrescriptionInput(dose_mg=10, frequency_per_day=1, route="intravenosa")
    assert _validated_patient_eval(plain, drug).envelope.decision_status.value == (
        "evaluated_no_issue"
    )  # controle positivo: mesma droga, sem concentração

    concentrated = PrescriptionInput(
        dose_mg=None,
        frequency_per_day=None,
        route="intravenosa",
        dose=MedicationDoseInput(
            amount=Decimal("10"),
            amount_unit="ml",
            concentration_value=Decimal("200"),
            concentration_unit="mg/ml",
            volume=Decimal("10"),
            volume_unit="ml",
            frequency_per_day=1,
            route="intravenosa",
        ),
    )
    envelope = _validated_patient_eval(concentrated, drug).envelope
    assert envelope.decision_status.value != "evaluated_no_issue"
    assert {"module": "concentration_limit", "reason": "recebido e não avaliado"} in (
        envelope.coverage.not_evaluated
    )
