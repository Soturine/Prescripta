from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.dose import MedicationDoseInput
from app.domain.dose_units import (
    Quantity,
    convert_value,
    multiply_concentration_by_volume,
    parse_unit,
)
from app.domain.prescription import PrescriptionInput
from app.services.dose_intelligence import DoseIntelligenceService


def _rule(**overrides):
    values = {
        "calculation_basis": "fixed",
        "dose_unit": "mg",
        "fixed_dose": Decimal("10"),
        "max_daily": Decimal("100"),
        "max_daily_unit": "mg",
        "source_refs": ["demo:dose:v0.8.7"],
        "validation_status": "validated",
        "allowed_routes": ["oral", "intravenosa"],
    }
    values.update(overrides)
    return values


def _patient(**overrides):
    values = {"weight_kg": 70, "height_cm": 170, "sex_for_dosing_calculation": None}
    values.update(overrides)
    return values


def _prescription(dose: MedicationDoseInput) -> PrescriptionInput:
    return PrescriptionInput(
        dose_mg=None,
        frequency_per_day=None,
        route=dose.route or "oral",
        dose=dose,
    )


@given(
    value=st.decimals(
        min_value=Decimal("0.000001"),
        max_value=Decimal("1000000"),
        places=6,
        allow_nan=False,
        allow_infinity=False,
    ),
    source=st.sampled_from(("g", "mg", "mcg", "ng")),
    target=st.sampled_from(("g", "mg", "mcg", "ng")),
)
def test_mass_conversion_is_reversible_without_float_authority(value, source, target):
    converted = convert_value(value, source, target)
    assert converted is not None
    assert convert_value(converted, target, source) == value


@given(
    value=st.decimals(
        min_value=Decimal("0.001"),
        max_value=Decimal("10000"),
        places=3,
        allow_nan=False,
        allow_infinity=False,
    )
)
def test_rate_conversion_round_trip_preserves_dimension(value):
    in_mg_hour = convert_value(value, "mcg/min", "mg/h")
    assert in_mg_hour is not None
    assert convert_value(in_mg_hour, "mg/h", "mcg/min") == value


def test_concentration_times_volume_produces_real_mass():
    result = multiply_concentration_by_volume(
        Quantity(Decimal("25"), "mg/ml"),
        Quantity(Decimal("2"), "ml"),
    )
    assert result == Quantity(Decimal("50"), "mg")
    micro_volume = multiply_concentration_by_volume(
        Quantity(Decimal("2"), "mg/ml"),
        Quantity(Decimal("500"), "ul"),
    )
    assert micro_volume == Quantity(Decimal("1.000"), "mg")


def test_volume_dose_requires_concentration_and_compares_derived_mass():
    dose = MedicationDoseInput(
        amount=Decimal("2"),
        amount_unit="ml",
        concentration_value=Decimal("25"),
        concentration_unit="mg/ml",
        volume=Decimal("2"),
        volume_unit="ml",
        frequency_per_day=2,
        route="oral",
    )
    result = DoseIntelligenceService().evaluate(
        _rule(max_daily=Decimal("90")), _patient(), _prescription(dose)
    )
    assert result.status == "above_maximum"
    assert result.inputs_used["prescribed_daily_dose"] == 100


def test_volume_amount_is_itself_the_administered_volume():
    dose = MedicationDoseInput(
        amount=Decimal("2"),
        amount_unit="ml",
        concentration_value=Decimal("25"),
        concentration_unit="mg/ml",
        frequency_per_day=2,
        route="oral",
    )
    assert dose.amount_mg == Decimal("50")
    assert dose.daily_mass_mg == Decimal("100")


def test_duplicate_volume_must_match_amount_before_mass_is_proven():
    dose = MedicationDoseInput(
        amount=Decimal("2"),
        amount_unit="ml",
        concentration_value=Decimal("25"),
        concentration_unit="mg/ml",
        volume=Decimal("3"),
        volume_unit="ml",
        frequency_per_day=2,
        route="oral",
    )
    assert dose.amount_mg is None
    assert dose.daily_mass_mg is None


def test_conflicting_declared_mass_and_concentration_abstains():
    dose = MedicationDoseInput(
        amount=Decimal("40"),
        amount_unit="mg",
        concentration_value=Decimal("25"),
        concentration_unit="mg/ml",
        volume=Decimal("2"),
        volume_unit="ml",
        frequency_per_day=1,
        route="oral",
    )
    result = DoseIntelligenceService().evaluate(_rule(), _patient(), _prescription(dose))
    assert result.status == "insufficient_data"
    assert "massa por administração comprovada" in result.missing_data


@pytest.mark.parametrize(
    ("interval_value", "interval_unit", "expected"),
    [("8", "h", "3"), ("90", "min", "16"), ("0.5", "day", "2")],
)
def test_regular_interval_is_converted_to_frequency(
    interval_value, interval_unit, expected
):
    dose = MedicationDoseInput(
        amount=Decimal("10"),
        amount_unit="mg",
        interval_value=Decimal(interval_value),
        interval_unit=interval_unit,
        route="oral",
    )
    assert dose.inferred_frequency_per_day == Decimal(expected)


def test_divergent_frequency_and_interval_are_rejected():
    with pytest.raises(ValueError, match="divergentes"):
        MedicationDoseInput(
            amount=Decimal("10"),
            amount_unit="mg",
            frequency_per_day=2,
            interval_value=Decimal("8"),
            interval_unit="h",
        )


def test_duration_is_normalized_before_cumulative_exposure():
    dose = MedicationDoseInput(
        amount=Decimal("10"),
        amount_unit="mg",
        interval_value=Decimal("12"),
        interval_unit="h",
        duration_value=Decimal("72"),
        duration_unit="h",
        route="oral",
    )
    assert dose.daily_mass_mg == Decimal("20")
    assert dose.duration_days == Decimal("3")
    assert dose.cumulative_mass_mg == Decimal("60")


def test_prn_without_daily_ceiling_never_becomes_scheduled_dose():
    dose = MedicationDoseInput(
        amount=Decimal("10"),
        amount_unit="mg",
        administration_kind="prn",
        route="oral",
    )
    result = DoseIntelligenceService().evaluate(_rule(), _patient(), _prescription(dose))
    assert dose.daily_mass_mg is None
    assert result.status == "insufficient_data"
    assert "teto de administrações PRN" in result.missing_data


def test_prn_ceiling_is_an_upper_bound_not_an_exact_daily_exposure():
    dose = MedicationDoseInput(
        amount=Decimal("30"),
        amount_unit="mg",
        administration_kind="prn",
        max_administrations_per_day=4,
        route="oral",
    )
    result = DoseIntelligenceService().evaluate(
        _rule(max_daily=Decimal("100")), _patient(), _prescription(dose)
    )
    assert result.status == "above_maximum"
    assert result.inputs_used["prescribed_daily_dose"] is None
    assert result.inputs_used["prescribed_daily_upper_bound"] == 120
    assert result.inputs_used["comparison_scope"] == "prn_upper_bound"


def test_prn_rejects_scheduled_frequency():
    with pytest.raises(ValueError, match="PRN não aceita frequência"):
        MedicationDoseInput(
            amount=Decimal("10"),
            amount_unit="mg",
            administration_kind="prn",
            frequency_per_day=2,
        )


def test_rate_is_converted_instead_of_compared_as_text():
    dose = MedicationDoseInput(
        amount=Decimal("1"),
        amount_unit="mg",
        administration_kind="continuous",
        rate_value=Decimal("500"),
        rate_unit="mcg/min",
        route="intravenosa",
    )
    result = DoseIntelligenceService().evaluate(
        _rule(max_rate=Decimal("29"), rate_unit="mg/h"),
        _patient(),
        _prescription(dose),
    )
    assert result.status == "above_maximum"
    assert result.inputs_used["prescribed_rate"] == 30


def test_weight_based_rate_requires_weight_and_becomes_absolute():
    dose = MedicationDoseInput(
        amount=Decimal("1"),
        amount_unit="mg",
        administration_kind="continuous",
        rate_value=Decimal("2"),
        rate_unit="mcg/kg/min",
        route="intravenosa",
    )
    known = DoseIntelligenceService().evaluate(
        _rule(max_rate=Decimal("9"), rate_unit="mg/h"),
        _patient(weight_kg=70),
        _prescription(dose),
    )
    missing = DoseIntelligenceService().evaluate(
        _rule(max_rate=Decimal("9"), rate_unit="mg/h"),
        _patient(weight_kg=None),
        _prescription(dose),
    )
    assert known.inputs_used["prescribed_rate"] == 8.4
    assert known.status == "within_usual_range"
    assert missing.status == "unsupported_dimension"


def test_volume_rate_uses_concentration_to_derive_mass_rate():
    dose = MedicationDoseInput(
        amount=Decimal("1"),
        amount_unit="ml",
        administration_kind="continuous",
        concentration_value=Decimal("2"),
        concentration_unit="mg/ml",
        rate_value=Decimal("5"),
        rate_unit="ml/h",
        route="intravenosa",
    )
    result = DoseIntelligenceService().evaluate(
        _rule(max_rate=Decimal("9"), rate_unit="mg/h"),
        _patient(),
        _prescription(dose),
    )
    assert result.status == "above_maximum"
    assert result.inputs_used["prescribed_rate"] == 10


def test_limit_units_are_converted_for_daily_and_procedure_scopes():
    daily = MedicationDoseInput(
        amount=Decimal("400"),
        amount_unit="mg",
        frequency_per_day=2,
        route="oral",
    )
    daily_result = DoseIntelligenceService().evaluate(
        _rule(max_daily=Decimal("750000"), max_daily_unit="mcg"),
        _patient(),
        _prescription(daily),
    )
    procedure = MedicationDoseInput(
        amount=Decimal("600"),
        amount_unit="mg",
        administration_kind="bolus",
        procedure_context="procedimento demo",
        route="intravenosa",
    )
    procedure_result = DoseIntelligenceService().evaluate(
        _rule(max_per_procedure=Decimal("0.5"), max_per_procedure_unit="g"),
        _patient(),
        _prescription(procedure),
    )
    assert daily_result.status == "above_maximum"
    assert procedure_result.status == "above_procedure_maximum"


def test_single_administration_limit_is_typed_and_converted():
    dose = MedicationDoseInput(
        amount=Decimal("600"),
        amount_unit="mg",
        frequency_per_day=1,
        route="oral",
    )
    result = DoseIntelligenceService().evaluate(
        _rule(max_single=Decimal("0.5"), max_single_unit="g"),
        _patient(),
        _prescription(dose),
    )
    assert result.status == "above_single_maximum"
    assert result.max_limits["single"]["unit"] == "g"


def test_body_based_formula_returns_absolute_unit_and_preserves_raw_rule():
    result = DoseIntelligenceService().evaluate(
        _rule(
            calculation_basis="actual_weight",
            dose_unit="mg/kg/day",
            dose_per_basis=Decimal("2"),
            fixed_dose=None,
        ),
        _patient(weight_kg=70),
    )
    assert result.calculated_dose == 140
    assert result.calculated_unit == "mg/day"
    assert result.inputs_used["rule_unit_raw"] == "mg/kg/day"
    assert result.inputs_used["calculated_value_unrounded"] == "140"


@pytest.mark.parametrize(
    "unit",
    ["mg//h", "mg@h", "tablet", "mEq", "mg/kg/week", "", "http://127.0.0.1"],
)
def test_unknown_or_malformed_units_are_not_silently_coerced(unit):
    assert parse_unit(unit) is None
