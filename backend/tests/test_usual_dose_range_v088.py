from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.dose import MedicationDoseInput
from app.domain.prescription import PrescriptionInput
from app.services.dose_intelligence import DoseIntelligenceService


def _rule(**overrides):
    values = {
        "calculation_basis": "fixed",
        "dose_unit": "mg",
        "usual_dose_unit": "mg",
        "usual_range_scope": "daily",
        "usual_low": Decimal("100"),
        "usual_high": Decimal("300"),
        "fixed_dose": Decimal("100"),
        "source_refs": ["demo:dose:v0.8.8"],
        "validation_status": "validated",
        "allowed_routes": ["oral", "intravenosa"],
    }
    values.update(overrides)
    return values


def _patient(**overrides):
    values = {"weight_kg": 70, "height_cm": 170, "sex_for_dosing_calculation": None}
    values.update(overrides)
    return values


def _scheduled_daily(value: Decimal, unit: str = "mg") -> PrescriptionInput:
    return PrescriptionInput(
        dose_mg=None,
        frequency_per_day=None,
        route="oral",
        dose=MedicationDoseInput(
            amount=value,
            amount_unit=unit,
            frequency_per_day=1,
            route="oral",
        ),
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("99.9999", "below_usual_range"),
        ("100", "within_usual_range"),
        ("200", "within_usual_range"),
        ("300", "within_usual_range"),
        ("300.0001", "above_usual_range"),
    ],
)
def test_usual_range_boundaries_are_inclusive_and_use_unrounded_decimal(value, expected):
    result = DoseIntelligenceService().evaluate(
        _rule(),
        _patient(),
        _scheduled_daily(Decimal(value)),
    )
    assert result.status == expected
    assert result.usual_range == {
        "low": 100.0,
        "high": 300.0,
        "unit": "mg",
        "source_unit": "mg",
        "scope": "daily",
    }


def test_hard_maximum_takes_precedence_over_usual_range():
    result = DoseIntelligenceService().evaluate(
        _rule(max_daily=Decimal("350"), max_daily_unit="mg"),
        _patient(),
        _scheduled_daily(Decimal("351")),
    )
    assert result.status == "above_maximum"


def test_usual_range_converts_distinct_mass_units_before_comparison():
    result = DoseIntelligenceService().evaluate(
        _rule(
            usual_low=Decimal("100000"),
            usual_high=Decimal("300000"),
            usual_dose_unit="mcg",
        ),
        _patient(),
        _scheduled_daily(Decimal("0.2"), "g"),
    )
    assert result.status == "within_usual_range"
    assert result.usual_range["unit"] == "mg"
    assert result.usual_range["low"] == 100
    assert result.usual_range["high"] == 300


def test_weight_based_usual_range_is_normalized_to_absolute_daily_mass():
    result = DoseIntelligenceService().evaluate(
        _rule(
            calculation_basis="actual_weight",
            dose_unit="mg/kg/day",
            usual_dose_unit="mg/kg/day",
            usual_low=Decimal("1"),
            usual_high=Decimal("2"),
            dose_per_basis=Decimal("1"),
            fixed_dose=None,
        ),
        _patient(weight_kg=70),
        _scheduled_daily(Decimal("140")),
    )
    assert result.status == "within_usual_range"
    assert result.usual_range["low"] == 70
    assert result.usual_range["high"] == 140
    assert result.usual_range["unit"] == "mg/day"


def test_surface_based_usual_range_uses_the_same_bsa_for_both_limits():
    result = DoseIntelligenceService().evaluate(
        _rule(
            calculation_basis="body_surface_area",
            dose_unit="mg/m2/day",
            usual_dose_unit="mg/m2/day",
            usual_low=Decimal("50"),
            usual_high=Decimal("100"),
            dose_per_basis=Decimal("50"),
            fixed_dose=None,
        ),
        _patient(weight_kg=72, height_cm=180),
        _scheduled_daily(Decimal("180")),
    )
    assert result.status == "within_usual_range"
    assert result.usual_range["unit"] == "mg/day"


def test_prn_upper_bound_is_compared_to_usual_range_without_becoming_exact_exposure():
    prescription = PrescriptionInput(
        dose_mg=None,
        frequency_per_day=None,
        route="oral",
        dose=MedicationDoseInput(
            amount=Decimal("50"),
            amount_unit="mg",
            administration_kind="prn",
            max_administrations_per_day=4,
            route="oral",
        ),
    )
    result = DoseIntelligenceService().evaluate(_rule(), _patient(), prescription)
    assert result.status == "within_prn_ceiling"
    assert result.inputs_used["prescribed_daily_dose"] is None
    assert result.inputs_used["prescribed_daily_upper_bound"] == 200


def test_continuous_rate_has_an_explicit_rate_range():
    prescription = PrescriptionInput(
        dose_mg=None,
        frequency_per_day=None,
        route="intravenosa",
        dose=MedicationDoseInput(
            amount=Decimal("1"),
            amount_unit="mg",
            administration_kind="continuous",
            rate_value=Decimal("10"),
            rate_unit="mg/h",
            route="intravenosa",
        ),
    )
    result = DoseIntelligenceService().evaluate(
        _rule(
            dose_unit="mg/h",
            usual_dose_unit="mg/h",
            usual_range_scope="rate",
            usual_low=Decimal("5"),
            usual_high=Decimal("9"),
            fixed_dose=Decimal("5"),
            max_rate=Decimal("20"),
            rate_unit="mg/h",
        ),
        _patient(),
        prescription,
    )
    assert result.status == "above_usual_range"


def test_concentration_derived_mass_uses_the_same_daily_range_contract():
    prescription = PrescriptionInput(
        dose_mg=None,
        frequency_per_day=None,
        route="oral",
        dose=MedicationDoseInput(
            amount=Decimal("2"),
            amount_unit="ml",
            concentration_value=Decimal("25"),
            concentration_unit="mg/ml",
            frequency_per_day=4,
            route="oral",
        ),
    )
    result = DoseIntelligenceService().evaluate(_rule(), _patient(), prescription)
    assert result.status == "within_usual_range"
    assert result.inputs_used["prescribed_daily_dose"] == 200


@pytest.mark.parametrize(
    "overrides",
    [
        {"usual_dose_unit": ""},
        {"usual_dose_unit": "ml"},
        {"usual_low": Decimal("400"), "usual_high": Decimal("300")},
    ],
)
def test_missing_incompatible_or_inverted_usual_range_abstains(overrides):
    result = DoseIntelligenceService().evaluate(
        _rule(**overrides),
        _patient(),
        _scheduled_daily(Decimal("200")),
    )
    assert result.status in {
        "insufficient_data",
        "insufficient_rule",
        "unsupported_dimension",
    }
    assert result.missing_data


@given(
    low=st.decimals(
        min_value=Decimal("0.0001"),
        max_value=Decimal("100000"),
        places=4,
        allow_nan=False,
        allow_infinity=False,
    ),
    width=st.decimals(
        min_value=Decimal("0.0001"),
        max_value=Decimal("100000"),
        places=4,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_any_decimal_inside_an_ordered_range_is_classified_inside(low, width):
    high = low + width
    midpoint = low + width / Decimal("2")
    result = DoseIntelligenceService().evaluate(
        _rule(usual_low=low, usual_high=high, fixed_dose=low),
        _patient(),
        _scheduled_daily(midpoint),
    )
    assert result.status == "within_usual_range"
