from __future__ import annotations

from math import sqrt
from typing import Any

from app.core.constants import DOSE_UNITS
from app.domain.clinical_intelligence import DoseIntelligenceResult
from app.domain.dose import DoseDimension, MedicationDoseInput, normalize_unit


class DoseIntelligenceService:
    """Calculadora determinística que só compara grandezas dimensionalmente compatíveis."""

    def evaluate(
        self,
        rule: Any,
        patient: Any,
        prescription: Any | None = None,
    ) -> DoseIntelligenceResult:
        get = self._get
        weight = get(patient, "weight_kg")
        height_cm = get(patient, "height_cm")
        sex_for_dosing = get(patient, "sex_for_dosing_calculation")
        basis = get(rule, "calculation_basis", "fixed")
        unit = str(get(rule, "dose_unit", get(rule, "unit", "mg")))
        validation = get(rule, "validation_status", "pending_review")
        source_refs = list(get(rule, "source_refs", []) or [])
        missing: list[str] = []
        inputs: dict[str, Any] = {
            "weight_kg": weight,
            "height_cm": height_cm,
            "sex_for_dosing_calculation": sex_for_dosing,
        }
        scalar = 1.0
        formula = "dose fixa"

        if not source_refs:
            missing.append("fonte da regra de dose")
        if validation not in {"demo_seed", "pending_review", "curated", "validated"}:
            missing.append("status válido da regra de dose")
        if unit not in DOSE_UNITS:
            missing.append("unidade de dose compatível")
        if weight is not None and not 1 <= float(weight) <= 400:
            missing.append("peso válido")
        if height_cm is not None and not 50 <= float(height_cm) <= 260:
            missing.append("altura válida")
        if basis in {
            "actual_weight",
            "real_weight",
            "weight",
            "ideal_weight",
            "adjusted_weight",
            "lean_body_mass",
        } and "/kg" not in unit:
            missing.append("unidade por kg")
        if basis in {"bsa", "body_surface_area"} and "m²" not in unit and "m2" not in unit:
            missing.append("unidade por superfície corporal")

        if basis in {"actual_weight", "real_weight", "weight"}:
            if not weight:
                missing.append("peso")
            else:
                scalar = float(weight)
                formula = "dose_por_kg × peso_real_kg"
        elif basis in {"ideal_weight", "adjusted_weight", "lean_body_mass"}:
            if not weight:
                missing.append("peso")
            if not height_cm:
                missing.append("altura")
            if sex_for_dosing not in {"male", "female"}:
                missing.append("sexo para cálculo de dose")
            if not missing:
                height_in = float(height_cm) / 2.54
                male = sex_for_dosing == "male"
                ideal = max(0.0, (50 if male else 45.5) + 2.3 * (height_in - 60))
                adjusted = ideal + 0.4 * (float(weight) - ideal)
                lean = (9270 * float(weight)) / (
                    (6680 if male else 8780)
                    + (216 if male else 244) * self._bmi(weight, height_cm)
                )
                scalar = {
                    "ideal_weight": ideal,
                    "adjusted_weight": adjusted,
                    "lean_body_mass": lean,
                }[basis]
                inputs.update(
                    {
                        "ideal_weight_kg": round(ideal, 2),
                        "adjusted_weight_kg": round(adjusted, 2),
                        "lean_body_mass_kg": round(lean, 2),
                    }
                )
                formula = f"dose_por_kg × {basis}"
        elif basis in {"bsa", "body_surface_area"} or "m²" in unit or "m2" in unit:
            if not weight:
                missing.append("peso")
            if not height_cm:
                missing.append("altura")
            if not missing:
                scalar = sqrt(float(height_cm) * float(weight) / 3600)
                inputs["bsa_m2"] = round(scalar, 3)
                formula = "dose_por_m² × √((altura_cm × peso_kg) / 3600)"

        per_basis = get(rule, "dose_per_basis", get(rule, "dose_mg_per_kg"))
        fixed = get(rule, "fixed_dose", get(rule, "usual_low"))
        calculated = (
            None
            if missing
            else round(float(per_basis) * scalar, 4)
            if per_basis is not None
            else fixed
        )

        dose_input = self._dose_input(prescription)
        dimension = dose_input.dimension if dose_input else None
        prescribed_single: float | None = None
        prescribed_daily: float | None = None
        prescribed_rate: float | None = None
        cumulative: float | None = None
        duration = get(prescription, "duration_days") if prescription is not None else None
        route = get(prescription, "route") if prescription is not None else None
        if dose_input is not None:
            inputs["dose_input"] = dose_input.to_dict()
            inputs["prescribed_dimension"] = dose_input.dimension.value
            if dimension == DoseDimension.UNSUPPORTED:
                missing.append("dimensão de dose suportada")
            elif dimension == DoseDimension.RATE:
                prescribed_rate = float(dose_input.rate_value) if dose_input.rate_value else None
            else:
                amount_mg = dose_input.amount_mg
                if amount_mg is None:
                    missing.append("unidade de massa compatível")
                else:
                    prescribed_single = float(amount_mg)
                    prescribed_daily_decimal = dose_input.daily_mass_mg
                    prescribed_daily = (
                        float(prescribed_daily_decimal)
                        if prescribed_daily_decimal is not None
                        else None
                    )
                    cumulative = (
                        prescribed_daily * int(duration)
                        if prescribed_daily is not None and duration
                        else None
                    )
            route = route or dose_input.route
            allowed_routes = list(get(rule, "allowed_routes", []) or [])
            if route and allowed_routes and route not in allowed_routes:
                missing.append("via compatível com a regra")

        low = get(rule, "usual_low")
        high = get(rule, "usual_high")
        maximum = get(rule, "max_daily", get(rule, "max_daily_dose_mg"))
        procedure_max = get(rule, "max_per_procedure")
        cumulative_max = get(rule, "max_cumulative")
        max_rate = get(rule, "max_rate")
        max_rate_unit = normalize_unit(get(rule, "rate_unit"))
        alerts: list[dict[str, Any]] = []
        status = "insufficient_data" if missing else "calculated"

        if dimension == DoseDimension.RATE:
            if max_rate is None or not max_rate_unit or max_rate_unit != dose_input.rate_unit:
                status = "unsupported_dimension"
                missing.append("regra de taxa com unidade compatível")
                calculated = None
            elif prescribed_rate is not None:
                status = (
                    "above_maximum"
                    if prescribed_rate > float(max_rate)
                    else "within_usual_range"
                )
        elif dimension == DoseDimension.PROCEDURE:
            if procedure_max is None:
                status = "unsupported_dimension"
                missing.append("limite por procedimento")
                calculated = None
            elif prescribed_single is not None:
                status = (
                    "above_procedure_maximum"
                    if prescribed_single > float(procedure_max)
                    else "within_usual_range"
                )
        elif prescribed_daily is not None:
            if low is not None and prescribed_daily < float(low) * scalar:
                status = "below_usual_range"
            elif maximum is not None and prescribed_daily > float(maximum) * (
                scalar if get(rule, "max_daily_is_per_basis", False) else 1
            ):
                status = "above_maximum"
            elif (
                procedure_max is not None
                and prescribed_single is not None
                and prescribed_single > float(procedure_max)
            ):
                status = "above_procedure_maximum"
            elif (
                cumulative_max is not None
                and cumulative is not None
                and cumulative > float(cumulative_max)
            ):
                status = "above_cumulative_maximum"
            elif high is not None and prescribed_daily > float(high) * scalar:
                status = "above_usual_range"
            else:
                status = "within_usual_range"

        if status not in {
            "within_usual_range",
            "calculated",
            "insufficient_data",
            "insufficient_rule",
            "unsupported_dimension",
        }:
            alerts.append(
                {
                    "code": status.upper(),
                    "severity": "alto" if "maximum" in status else "moderado",
                }
            )
        if missing and status != "unsupported_dimension":
            status = (
                "insufficient_rule"
                if any("regra" in item for item in missing)
                else "insufficient_data"
            )
            calculated = None

        return DoseIntelligenceResult(
            status=status,
            calculated_dose=calculated,
            calculated_unit=unit,
            calculation_formula=formula,
            calculation_basis=basis,
            inputs_used=inputs
            | {
                "prescribed_per_administration": prescribed_single,
                "prescribed_daily_dose": prescribed_daily,
                "prescribed_rate": prescribed_rate,
                "prescribed_cumulative_dose": cumulative,
            },
            usual_range={"low": low, "high": high},
            max_limits={
                "daily": maximum,
                "per_procedure": procedure_max,
                "rate": max_rate,
                "rate_unit": max_rate_unit or None,
                "cumulative": cumulative_max,
            },
            alerts=alerts,
            missing_data=self._unique(missing),
            source_refs=source_refs,
            validation_status=validation,
            requires_human_review=validation != "validated" or bool(alerts) or bool(missing),
            educational_notice=(
                "Cálculo demonstrativo; confirmar bula, fonte e protocolo institucional."
            ),
        )

    @staticmethod
    def _get(obj: Any, key: str, default: Any = None) -> Any:
        if obj is None:
            return default
        return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

    def _dose_input(self, prescription: Any | None) -> MedicationDoseInput | None:
        if prescription is None:
            return None
        effective = getattr(prescription, "effective_dose", None)
        if effective is not None:
            return effective
        structured = self._get(prescription, "dose")
        if isinstance(structured, MedicationDoseInput):
            return structured
        if isinstance(structured, dict):
            return MedicationDoseInput(**structured)
        dose_mg = self._get(prescription, "dose_mg")
        frequency = self._get(prescription, "frequency_per_day")
        if dose_mg is None or frequency is None:
            return None
        return MedicationDoseInput.legacy_mg(
            dose_mg=float(dose_mg),
            frequency_per_day=int(frequency),
            route=str(self._get(prescription, "route", "não informada")),
            duration_days=self._get(prescription, "duration_days"),
        )

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))

    @staticmethod
    def _bmi(weight: float, height_cm: float) -> float:
        return float(weight) / ((float(height_cm) / 100) ** 2)
