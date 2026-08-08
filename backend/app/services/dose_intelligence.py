from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from app.domain.clinical_intelligence import DoseIntelligenceResult
from app.domain.dose import DoseDimension, MedicationDoseInput
from app.domain.dose_rounding import ROUNDING_POLICY_VERSION, present_decimal
from app.domain.dose_units import (
    Quantity,
    UnitDimension,
    canonical_target,
    normalize_unit,
    parse_unit,
    remove_body_basis,
)


@dataclass(frozen=True)
class NormalizedUsualDoseRange:
    low: Quantity | None
    high: Quantity | None
    source_unit: str
    normalized_unit: str | None
    scope: str


class DoseIntelligenceService:
    """Motor determinístico que abstém quando não consegue provar a dimensão."""

    def evaluate(
        self,
        rule: Any,
        patient: Any,
        prescription: Any | None = None,
    ) -> DoseIntelligenceResult:
        basis = str(self._get(rule, "calculation_basis", "fixed"))
        rule_unit = normalize_unit(self._get(rule, "dose_unit", self._get(rule, "unit", "mg")))
        validation = str(self._get(rule, "validation_status", "pending_review"))
        source_refs = list(self._get(rule, "source_refs", []) or [])
        weight = self._decimal(self._get(patient, "weight_kg"))
        height_cm = self._decimal(self._get(patient, "height_cm"))
        sex_for_dosing = self._get(patient, "sex_for_dosing_calculation")
        missing: list[str] = []
        inputs: dict[str, Any] = {
            "weight_kg": self._output(weight),
            "height_cm": self._output(height_cm),
            "sex_for_dosing_calculation": sex_for_dosing,
            "comparison_precision": "Decimal (sem arredondamento prévio)",
            "presentation_rounding": ROUNDING_POLICY_VERSION,
        }

        if not source_refs:
            missing.append("fonte da regra de dose")
        if validation not in {"demo_seed", "pending_review", "curated", "validated"}:
            missing.append("status válido da regra de dose")
        rule_definition = parse_unit(rule_unit)
        if rule_definition is None:
            missing.append("unidade de dose compatível")
        if weight is not None and not Decimal("1") <= weight <= Decimal("400"):
            missing.append("peso válido")
        if height_cm is not None and not Decimal("50") <= height_cm <= Decimal("260"):
            missing.append("altura válida")

        body_surface = self._body_surface(weight, height_cm)
        scalar, formula, body_inputs, body_missing = self._body_scalar(
            basis=basis,
            unit=rule_unit,
            weight=weight,
            height_cm=height_cm,
            sex_for_dosing=sex_for_dosing,
            body_surface=body_surface,
        )
        inputs.update(body_inputs)
        missing.extend(body_missing)
        basis_weight = scalar if basis in {
            "actual_weight",
            "real_weight",
            "weight",
            "ideal_weight",
            "adjusted_weight",
            "lean_body_mass",
        } else weight

        per_basis = self._decimal(
            self._get(rule, "dose_per_basis", self._get(rule, "dose_mg_per_kg"))
        )
        fixed = self._decimal(self._get(rule, "fixed_dose", self._get(rule, "usual_low")))
        raw_rule_value = per_basis if per_basis is not None else fixed
        calculated_quantity = None
        if not body_missing and raw_rule_value is not None and rule_definition is not None:
            calculated_quantity = self._absolute_quantity(
                Quantity(raw_rule_value, rule_unit),
                weight=basis_weight,
                body_surface=body_surface,
            )
            if calculated_quantity is None:
                missing.append("base corporal exigida pela unidade")
        calculated = calculated_quantity.value if calculated_quantity else None
        calculated_unit = calculated_quantity.unit if calculated_quantity else rule_unit

        dose_input = self._dose_input(prescription)
        dimension = dose_input.dimension if dose_input else None
        route = self._get(prescription, "route") if prescription is not None else None
        status = "insufficient_data" if missing else "calculated"
        prescribed_single = prescribed_daily = prescribed_rate = cumulative = None
        daily_upper = cumulative_upper = None
        scope = "calculation_only"

        if dose_input is not None:
            inputs["dose_input"] = dose_input.to_dict()
            inputs["prescribed_dimension"] = dose_input.dimension.value
            route = route or dose_input.route
            if dimension == DoseDimension.UNSUPPORTED:
                missing.append("dimensão de dose suportada")
            elif dimension == DoseDimension.RATE:
                status, prescribed_rate, rate_missing = self._evaluate_rate(
                    rule,
                    dose_input,
                    weight=basis_weight,
                    body_surface=body_surface,
                )
                missing.extend(rate_missing)
                scope = "rate"
            else:
                prescribed_single = dose_input.amount_mg
                if prescribed_single is None:
                    missing.append("massa por administração comprovada")
                prescribed_daily = dose_input.daily_mass_mg
                daily_upper = dose_input.daily_mass_upper_mg
                cumulative = dose_input.cumulative_mass_mg
                cumulative_upper = dose_input.cumulative_mass_upper_mg
                if dimension == DoseDimension.PROCEDURE:
                    status, procedure_missing = self._evaluate_procedure(
                        rule,
                        prescribed_single,
                        weight=basis_weight,
                        body_surface=body_surface,
                    )
                    missing.extend(procedure_missing)
                    scope = "procedure"
                elif dimension == DoseDimension.PRN_CEILING:
                    status, prn_missing = self._evaluate_single(
                        rule,
                        prescribed_single,
                        weight=basis_weight,
                        body_surface=body_surface,
                    )
                    if status == "within_single_limit":
                        status, prn_missing = self._evaluate_daily(
                            rule,
                            daily_upper,
                            cumulative_upper,
                            calculated_quantity,
                            weight=basis_weight,
                            body_surface=body_surface,
                            is_prn=True,
                        )
                    missing.extend(prn_missing)
                    scope = "prn_upper_bound"
                else:
                    status, daily_missing = self._evaluate_single(
                        rule,
                        prescribed_single,
                        weight=basis_weight,
                        body_surface=body_surface,
                    )
                    if status == "within_single_limit":
                        status, daily_missing = self._evaluate_daily(
                            rule,
                            prescribed_daily,
                            cumulative,
                            calculated_quantity,
                            weight=basis_weight,
                            body_surface=body_surface,
                            is_prn=False,
                        )
                    missing.extend(daily_missing)
                    scope = "scheduled_daily"

            allowed_routes = list(self._get(rule, "allowed_routes", []) or [])
            if route and allowed_routes and route not in allowed_routes:
                missing.append("via compatível com a regra")

        inputs.update(
            {
                "prescribed_per_administration": self._output(prescribed_single),
                "prescribed_daily_dose": self._output(prescribed_daily),
                "prescribed_daily_upper_bound": self._output(daily_upper),
                "prescribed_rate": self._output(prescribed_rate),
                "prescribed_cumulative_dose": self._output(cumulative),
                "prescribed_cumulative_upper_bound": self._output(cumulative_upper),
                "comparison_scope": scope,
            }
        )

        missing = self._unique(missing)
        if missing and status not in {"unsupported_dimension"}:
            status = (
                "insufficient_rule"
                if any("regra" in item or "limite" in item for item in missing)
                else "insufficient_data"
            )
            calculated = None

        alerts = self._alerts(status)
        usual_range, _ = self._normalized_usual_range(
            rule,
            weight=basis_weight,
            body_surface=body_surface,
        )
        usual_low = usual_range.low.value if usual_range.low else None
        usual_high = usual_range.high.value if usual_range.high else None
        return DoseIntelligenceResult(
            status=status,
            calculated_dose=present_decimal(calculated),
            calculated_unit=calculated_unit,
            calculation_formula=formula,
            calculation_basis=basis,
            inputs_used=inputs
            | {
                "rule_value_raw": self._output(raw_rule_value),
                "rule_unit_raw": rule_unit,
                "calculated_value_unrounded": self._decimal_text(calculated),
                "calculated_value_presented": present_decimal(calculated),
            },
            usual_range={
                "low": present_decimal(usual_low),
                "high": present_decimal(usual_high),
                "unit": usual_range.normalized_unit,
                "source_unit": usual_range.source_unit,
                "scope": usual_range.scope,
            },
            max_limits=self._limit_manifest(rule),
            alerts=alerts,
            missing_data=missing,
            source_refs=source_refs,
            validation_status=validation,
            requires_human_review=validation != "validated" or bool(alerts) or bool(missing),
            educational_notice=(
                "Cálculo demonstrativo; confirmar bula, fonte e protocolo institucional."
            ),
        )

    def _evaluate_rate(
        self,
        rule: Any,
        dose: MedicationDoseInput,
        *,
        weight: Decimal | None,
        body_surface: Decimal | None,
    ) -> tuple[str, Decimal | None, list[str]]:
        maximum = self._decimal(self._get(rule, "max_rate"))
        unit = normalize_unit(self._get(rule, "rate_unit"))
        if maximum is None or not unit or parse_unit(unit) is None:
            return "unsupported_dimension", None, ["regra de taxa com unidade compatível"]
        limit = self._absolute_quantity(
            Quantity(maximum, unit),
            weight=weight,
            body_surface=body_surface,
        )
        if limit is None:
            return "unsupported_dimension", None, ["contexto corporal para a regra de taxa"]
        prescribed = dose.rate_as(
            limit.unit,
            weight_kg=weight,
            body_surface_m2=body_surface,
        )
        if prescribed is None:
            return "unsupported_dimension", None, ["taxa prescrita dimensionalmente compatível"]
        if prescribed > limit.value:
            return "above_maximum", prescribed, []
        usual_range, range_missing = self._normalized_usual_range(
            rule,
            weight=weight,
            body_surface=body_surface,
            expected_scope="rate",
        )
        if range_missing:
            return "unsupported_dimension", prescribed, range_missing
        if usual_range.low is None and usual_range.high is None:
            return "within_usual_range", prescribed, []
        status = self._classify_usual_range(
            Quantity(prescribed, limit.unit),
            usual_range,
            within_status="within_usual_range",
        )
        return status, prescribed, []

    def _evaluate_procedure(
        self,
        rule: Any,
        prescribed_mg: Decimal | None,
        *,
        weight: Decimal | None,
        body_surface: Decimal | None,
    ) -> tuple[str, list[str]]:
        maximum = self._decimal(self._get(rule, "max_per_procedure"))
        unit = normalize_unit(
            self._get(rule, "max_per_procedure_unit")
            or self._get(rule, "max_daily_unit")
            or "mg"
        )
        if maximum is None:
            return "unsupported_dimension", ["limite por procedimento"]
        limit = self._absolute_quantity(
            Quantity(maximum, unit), weight=weight, body_surface=body_surface
        )
        if prescribed_mg is None or limit is None:
            return "unsupported_dimension", ["unidade do limite por procedimento"]
        prescribed = Quantity(prescribed_mg, "mg").converted_to(limit.unit)
        if prescribed is None:
            return "unsupported_dimension", ["dimensão do limite por procedimento"]
        return (
            "above_procedure_maximum"
            if prescribed.value > limit.value
            else "within_usual_range",
            [],
        )

    def _evaluate_single(
        self,
        rule: Any,
        prescribed_mg: Decimal | None,
        *,
        weight: Decimal | None,
        body_surface: Decimal | None,
    ) -> tuple[str, list[str]]:
        maximum = self._decimal(self._get(rule, "max_single"))
        if maximum is None:
            return "within_single_limit", []
        unit = normalize_unit(self._get(rule, "max_single_unit") or "mg")
        limit = self._absolute_quantity(
            Quantity(maximum, unit), weight=weight, body_surface=body_surface
        )
        prescribed = Quantity(prescribed_mg, "mg").converted_to(limit.unit) if (
            prescribed_mg is not None and limit is not None
        ) else None
        if prescribed is None or limit is None:
            return "unsupported_dimension", ["unidade do limite por administração"]
        return (
            "above_single_maximum" if prescribed.value > limit.value else "within_single_limit",
            [],
        )

    def _evaluate_daily(
        self,
        rule: Any,
        prescribed_mg: Decimal | None,
        cumulative_mg: Decimal | None,
        calculated: Quantity | None,
        *,
        weight: Decimal | None,
        body_surface: Decimal | None,
        is_prn: bool,
    ) -> tuple[str, list[str]]:
        if prescribed_mg is None:
            label = "teto de administrações PRN" if is_prn else "frequência ou intervalo regular"
            return "insufficient_data", [label]
        daily_maximum = self._decimal(
            self._get(rule, "max_daily", self._get(rule, "max_daily_dose_mg"))
        )
        daily_unit = normalize_unit(
            self._get(rule, "max_daily_unit")
            or (
                self._get(rule, "dose_unit")
                if self._get(rule, "max_daily_is_per_basis", False)
                else "mg"
            )
        )
        daily_limit = (
            self._absolute_quantity(
                Quantity(daily_maximum, daily_unit),
                weight=weight,
                body_surface=body_surface,
            )
            if daily_maximum is not None
            else None
        )
        if daily_maximum is not None and daily_limit is None:
            return "unsupported_dimension", ["unidade do limite diário"]
        if daily_limit is not None:
            prescribed = self._daily_quantity(prescribed_mg, daily_limit.unit)
            if prescribed is None:
                return "unsupported_dimension", ["dimensão do limite diário"]
            if prescribed.value > daily_limit.value:
                return "above_maximum", []

        cumulative_maximum = self._decimal(
            self._get(rule, "max_cumulative", self._get(rule, "max_cumulative_dose_mg"))
        )
        cumulative_unit = normalize_unit(self._get(rule, "max_cumulative_unit") or "mg")
        if cumulative_maximum is not None and cumulative_mg is not None:
            limit = self._absolute_quantity(
                Quantity(cumulative_maximum, cumulative_unit),
                weight=weight,
                body_surface=body_surface,
            )
            prescribed = Quantity(cumulative_mg, "mg").converted_to(limit.unit) if limit else None
            if limit is None or prescribed is None:
                return "unsupported_dimension", ["unidade do limite cumulativo"]
            if prescribed.value > limit.value:
                return "above_cumulative_maximum", []

        usual_range, range_missing = self._normalized_usual_range(
            rule,
            weight=weight,
            body_surface=body_surface,
            expected_scope="daily",
        )
        if range_missing:
            return "unsupported_dimension", range_missing
        if usual_range.low is None and usual_range.high is None:
            return ("within_prn_ceiling" if is_prn else "within_usual_range"), []
        target_unit = usual_range.normalized_unit
        comparable = self._daily_quantity(prescribed_mg, target_unit or "")
        if comparable is None:
            return "unsupported_dimension", ["unidade da faixa usual diária"]
        status = self._classify_usual_range(
            comparable,
            usual_range,
            within_status="within_prn_ceiling" if is_prn else "within_usual_range",
        )
        return status, []

    def _normalized_usual_range(
        self,
        rule: Any,
        *,
        weight: Decimal | None,
        body_surface: Decimal | None,
        expected_scope: str | None = None,
    ) -> tuple[NormalizedUsualDoseRange, list[str]]:
        low_value = self._decimal(self._get(rule, "usual_low"))
        high_value = self._decimal(self._get(rule, "usual_high"))
        source_unit = normalize_unit(
            self._get(
                rule,
                "usual_dose_unit",
                self._get(rule, "usual_unit", self._get(rule, "dose_unit")),
            )
        )
        configured_scope = str(
            self._get(rule, "usual_range_scope", self._get(rule, "usual_scope", ""))
            or ""
        )
        definition = parse_unit(source_unit)
        inferred_scope = (
            "rate"
            if definition and definition.dimension == UnitDimension.MASS_RATE
            else "daily"
        )
        scope = configured_scope or inferred_scope
        empty = NormalizedUsualDoseRange(
            low=None,
            high=None,
            source_unit=source_unit,
            normalized_unit=None,
            scope=scope,
        )
        if low_value is None and high_value is None:
            return empty, []
        if definition is None:
            return empty, ["unidade da faixa usual"]
        if scope not in {"daily", "per_administration", "rate"}:
            return empty, ["escopo da faixa usual"]
        if expected_scope and scope != expected_scope:
            return empty, [f"faixa usual com escopo {expected_scope}"]
        low = (
            self._absolute_quantity(
                Quantity(low_value, source_unit),
                weight=weight,
                body_surface=body_surface,
            )
            if low_value is not None
            else None
        )
        high = (
            self._absolute_quantity(
                Quantity(high_value, source_unit),
                weight=weight,
                body_surface=body_surface,
            )
            if high_value is not None
            else None
        )
        if (low_value is not None and low is None) or (high_value is not None and high is None):
            return empty, ["contexto corporal ou unidade da faixa usual"]
        normalized_unit = low.unit if low else high.unit if high else None
        if low and high:
            high = high.converted_to(low.unit)
            if high is None:
                return empty, ["limites dimensionalmente compatíveis da faixa usual"]
            if low.value > high.value:
                return empty, ["limites ordenados da faixa usual"]
        normalized = NormalizedUsualDoseRange(
            low=low,
            high=high,
            source_unit=source_unit,
            normalized_unit=normalized_unit,
            scope=scope,
        )
        return normalized, []

    @staticmethod
    def _classify_usual_range(
        prescribed: Quantity,
        usual_range: NormalizedUsualDoseRange,
        *,
        within_status: str,
    ) -> str:
        target_unit = usual_range.normalized_unit
        comparable = prescribed.converted_to(target_unit) if target_unit else None
        if comparable is None:
            return "unsupported_dimension"
        if usual_range.low is not None and comparable.value < usual_range.low.value:
            return "below_usual_range"
        if usual_range.high is not None and comparable.value > usual_range.high.value:
            return "above_usual_range"
        return within_status

    def _body_scalar(
        self,
        *,
        basis: str,
        unit: str,
        weight: Decimal | None,
        height_cm: Decimal | None,
        sex_for_dosing: Any,
        body_surface: Decimal | None,
    ) -> tuple[Decimal, str, dict[str, Any], list[str]]:
        missing: list[str] = []
        inputs: dict[str, Any] = {}
        scalar = Decimal("1")
        formula = "dose fixa"
        weight_bases = {
            "actual_weight",
            "real_weight",
            "weight",
            "ideal_weight",
            "adjusted_weight",
            "lean_body_mass",
        }
        if basis in weight_bases and "/kg" not in unit:
            missing.append("unidade por kg")
        if basis in {"bsa", "body_surface_area"} and "/m2" not in unit:
            missing.append("unidade por superfície corporal")
        if basis in {"actual_weight", "real_weight", "weight"}:
            if weight is None:
                missing.append("peso")
            else:
                scalar = weight
                formula = "dose_por_kg × peso_real_kg"
        elif basis in {"ideal_weight", "adjusted_weight", "lean_body_mass"}:
            if weight is None:
                missing.append("peso")
            if height_cm is None:
                missing.append("altura")
            if sex_for_dosing not in {"male", "female"}:
                missing.append("sexo para cálculo de dose")
            if not missing and weight is not None and height_cm is not None:
                height_in = height_cm / Decimal("2.54")
                male = sex_for_dosing == "male"
                ideal = max(
                    Decimal("0"),
                    (Decimal("50") if male else Decimal("45.5"))
                    + Decimal("2.3") * (height_in - Decimal("60")),
                )
                adjusted = ideal + Decimal("0.4") * (weight - ideal)
                bmi = weight / ((height_cm / Decimal("100")) ** 2)
                lean = (Decimal("9270") * weight) / (
                    (Decimal("6680") if male else Decimal("8780"))
                    + (Decimal("216") if male else Decimal("244")) * bmi
                )
                scalar = {
                    "ideal_weight": ideal,
                    "adjusted_weight": adjusted,
                    "lean_body_mass": lean,
                }[basis]
                inputs.update(
                    {
                        "ideal_weight_kg": present_decimal(ideal, Decimal("0.01")),
                        "adjusted_weight_kg": present_decimal(adjusted, Decimal("0.01")),
                        "lean_body_mass_kg": present_decimal(lean, Decimal("0.01")),
                    }
                )
                formula = f"dose_por_kg × {basis}"
        elif basis in {"bsa", "body_surface_area"} or "/m2" in unit:
            if body_surface is None:
                if weight is None:
                    missing.append("peso")
                if height_cm is None:
                    missing.append("altura")
            else:
                scalar = body_surface
                inputs["bsa_m2"] = present_decimal(body_surface, Decimal("0.001"))
                formula = "dose_por_m² × √((altura_cm × peso_kg) / 3600)"
        return scalar, formula, inputs, self._unique(missing)

    @staticmethod
    def _body_surface(weight: Decimal | None, height_cm: Decimal | None) -> Decimal | None:
        if weight is None or height_cm is None:
            return None
        return ((height_cm * weight) / Decimal("3600")).sqrt()

    @staticmethod
    def _absolute_quantity(
        quantity: Quantity,
        *,
        weight: Decimal | None,
        body_surface: Decimal | None,
    ) -> Quantity | None:
        absolute = remove_body_basis(
            quantity,
            weight_kg=weight,
            body_surface_m2=body_surface,
        )
        if absolute is None:
            return None
        definition = parse_unit(absolute.unit)
        if definition is None:
            return None
        if definition.dimension == UnitDimension.MASS_RATE and absolute.unit.endswith("/day"):
            target = "mg/day"
        else:
            target = canonical_target(absolute.unit)
        return absolute.converted_to(target) if target else None

    @staticmethod
    def _daily_quantity(value_mg: Decimal, target_unit: str) -> Quantity | None:
        target = parse_unit(target_unit)
        if target is None:
            return None
        source_unit = "mg/day" if target.dimension == UnitDimension.MASS_RATE else "mg"
        return Quantity(value_mg, source_unit).converted_to(target_unit)

    def _limit_manifest(self, rule: Any) -> dict[str, Any]:
        values = {
            "single": (
                self._get(rule, "max_single"),
                self._get(rule, "max_single_unit") or "mg",
                "administration",
            ),
            "daily": (
                self._get(rule, "max_daily", self._get(rule, "max_daily_dose_mg")),
                self._get(rule, "max_daily_unit") or "mg",
                "daily",
            ),
            "per_procedure": (
                self._get(rule, "max_per_procedure"),
                self._get(rule, "max_per_procedure_unit")
                or self._get(rule, "max_daily_unit")
                or "mg",
                "procedure",
            ),
            "rate": (self._get(rule, "max_rate"), self._get(rule, "rate_unit"), "rate"),
            "cumulative": (
                self._get(rule, "max_cumulative", self._get(rule, "max_cumulative_dose_mg")),
                self._get(rule, "max_cumulative_unit") or "mg",
                "cumulative",
            ),
        }
        return {
            name: {
                "value": value,
                "unit": normalize_unit(unit),
                "scope": scope,
                "dimension": (
                    parse_unit(unit).dimension.value if unit and parse_unit(unit) else "unknown"
                ),
            }
            for name, (value, unit, scope) in values.items()
        }

    @staticmethod
    def _alerts(status: str) -> list[dict[str, Any]]:
        safe = {
            "within_usual_range",
            "within_prn_ceiling",
            "within_single_limit",
            "calculated",
            "insufficient_data",
            "insufficient_rule",
            "unsupported_dimension",
        }
        if status in safe:
            return []
        return [
            {
                "code": status.upper(),
                "severity": "alto" if "maximum" in status else "moderado",
            }
        ]

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
    def _decimal(value: Any) -> Decimal | None:
        if value is None:
            return None
        try:
            converted = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
        return converted if converted.is_finite() else None

    @staticmethod
    def _output(value: Decimal | None) -> float | None:
        return float(value) if value is not None else None

    @staticmethod
    def _decimal_text(value: Decimal | None) -> str | None:
        if value is None:
            return None
        return format(value.normalize(), "f")

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))
