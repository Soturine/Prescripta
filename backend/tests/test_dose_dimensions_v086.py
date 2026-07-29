from decimal import Decimal

from app.domain.dose import AdministrationKind, MedicationDoseInput, convert_mass
from app.domain.prescription import PrescriptionInput
from app.services.dose_intelligence import DoseIntelligenceService


def _patient(**overrides):
    patient = {
        "weight_kg": 70,
        "height_cm": 170,
        "sex_for_dosing_calculation": None,
    }
    patient.update(overrides)
    return patient


def _rule(**overrides):
    rule = {
        "calculation_basis": "fixed",
        "dose_unit": "mg",
        "fixed_dose": 10,
        "max_daily": 100,
        "source_refs": ["demo:dose:v0.8.6"],
        "validation_status": "validated",
        "allowed_routes": ["oral", "intravenosa"],
    }
    rule.update(overrides)
    return rule


def test_mass_conversion_is_explicit_and_lossless_for_supported_units():
    assert convert_mass(Decimal("1"), "g", "mg") == Decimal("1000")
    assert convert_mass(Decimal("1000"), "mcg", "mg") == Decimal("1.000")
    assert convert_mass(Decimal("1"), "mg", "mcg") == Decimal("1E+3")
    assert convert_mass(Decimal("1"), "mL", "mg") is None


def test_structured_microgram_dose_is_compared_in_milligrams():
    prescription = PrescriptionInput(
        dose_mg=None,
        frequency_per_day=None,
        route="oral",
        dose=MedicationDoseInput(
            amount=Decimal("500"),
            amount_unit="mcg",
            frequency_per_day=2,
            route="oral",
        ),
    )
    result = DoseIntelligenceService().evaluate(_rule(max_daily=2), _patient(), prescription)
    assert result.status == "within_usual_range"
    assert result.inputs_used["prescribed_daily_dose"] == 1


def test_continuous_infusion_is_not_multiplied_by_frequency():
    prescription = PrescriptionInput(
        dose_mg=None,
        frequency_per_day=None,
        route="intravenosa",
        dose=MedicationDoseInput(
            amount=Decimal("100"),
            amount_unit="mg",
            administration_kind=AdministrationKind.CONTINUOUS,
            rate_value=Decimal("5"),
            rate_unit="mg/h",
            frequency_per_day=24,
            route="intravenosa",
        ),
    )
    result = DoseIntelligenceService().evaluate(
        _rule(max_daily=1, max_rate=6, rate_unit="mg/h"),
        _patient(),
        prescription,
    )
    assert result.status == "within_usual_range"
    assert result.inputs_used["prescribed_daily_dose"] is None
    assert result.inputs_used["prescribed_rate"] == 5


def test_rate_without_compatible_rule_abstains():
    prescription = PrescriptionInput(
        dose_mg=None,
        frequency_per_day=None,
        route="intravenosa",
        dose=MedicationDoseInput(
            amount=Decimal("1"),
            amount_unit="mg",
            administration_kind="continuous",
            rate_value=Decimal("2"),
            rate_unit="mcg/kg/min",
            route="intravenosa",
        ),
    )
    result = DoseIntelligenceService().evaluate(_rule(), _patient(), prescription)
    assert result.status == "unsupported_dimension"
    assert "regra de taxa com unidade compatível" in result.missing_data


def test_procedure_limit_is_separate_from_daily_limit():
    prescription = PrescriptionInput(
        dose_mg=None,
        frequency_per_day=None,
        route="intravenosa",
        dose=MedicationDoseInput(
            amount=Decimal("60"),
            amount_unit="mg",
            administration_kind="bolus",
            procedure_context="indução demo",
            route="intravenosa",
        ),
    )
    result = DoseIntelligenceService().evaluate(
        _rule(max_daily=10, max_per_procedure=50),
        _patient(),
        prescription,
    )
    assert result.status == "above_procedure_maximum"
    assert result.inputs_used["prescribed_daily_dose"] is None


def test_sex_dependent_formula_never_assumes_a_default():
    rule = _rule(
        calculation_basis="ideal_weight",
        dose_unit="mg/kg",
        dose_per_basis=1,
    )
    missing = DoseIntelligenceService().evaluate(rule, _patient())
    male = DoseIntelligenceService().evaluate(
        rule, _patient(sex_for_dosing_calculation="male")
    )
    female = DoseIntelligenceService().evaluate(
        rule, _patient(sex_for_dosing_calculation="female")
    )
    assert missing.status == "insufficient_data"
    assert "sexo para cálculo de dose" in missing.missing_data
    assert male.calculated_dose != female.calculated_dose
