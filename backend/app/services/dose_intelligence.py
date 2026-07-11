from math import sqrt
from typing import Any

from app.domain.clinical_intelligence import DoseIntelligenceResult


class DoseIntelligenceService:
    """Calculadora determinística. Regras pendentes nunca são apresentadas como validadas."""

    def evaluate(
        self,
        rule: Any,
        patient: Any,
        prescription: Any | None = None,
    ) -> DoseIntelligenceResult:
        def get(obj: Any, key: str, default: Any = None) -> Any:
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        weight = get(patient, "weight_kg")
        height_cm = get(patient, "height_cm")
        basis = get(rule, "calculation_basis", "fixed")
        unit = get(rule, "dose_unit", get(rule, "unit", "mg"))
        validation = get(rule, "validation_status", "pending_review")
        missing: list[str] = []
        inputs: dict[str, Any] = {"weight_kg": weight, "height_cm": height_cm}
        scalar = 1.0
        formula = "dose fixa"

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
            if not missing:
                height_in = float(height_cm) / 2.54
                sex = str(get(patient, "sex", "unspecified"))
                ideal = max(0.0, (50 if sex == "male" else 45.5) + 2.3 * (height_in - 60))
                adjusted = ideal + 0.4 * (float(weight) - ideal)
                lean = (9270 * float(weight)) / (
                    (6680 if sex == "male" else 8780)
                    + (216 if sex == "male" else 244) * self._bmi(weight, height_cm)
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
        prescribed = None
        if prescription is not None:
            dose = get(prescription, "dose_mg", get(prescription, "dose"))
            frequency = get(prescription, "frequency_per_day", 1)
            prescribed = float(dose) * int(frequency) if dose is not None else None
        low = get(rule, "usual_low")
        high = get(rule, "usual_high")
        maximum = get(rule, "max_daily", get(rule, "max_daily_dose_mg"))
        procedure_max = get(rule, "max_per_procedure")
        alerts: list[dict[str, Any]] = []
        status = "insufficient_data" if missing else "calculated"
        if prescribed is not None:
            if low is not None and prescribed < float(low) * scalar:
                status = "below_usual_range"
            elif maximum is not None and prescribed > float(maximum) * scalar:
                status = "above_maximum"
            elif procedure_max is not None and prescribed > float(procedure_max):
                status = "above_procedure_maximum"
            elif high is not None and prescribed > float(high) * scalar:
                status = "above_usual_range"
            else:
                status = "within_usual_range"
            if status not in {"within_usual_range", "calculated"}:
                alerts.append(
                    {
                        "code": status.upper(),
                        "severity": "alto" if "maximum" in status else "moderado",
                    }
                )
        return DoseIntelligenceResult(
            status=status,
            calculated_dose=calculated,
            calculated_unit=unit,
            calculation_formula=formula,
            calculation_basis=basis,
            inputs_used=inputs | {"prescribed_daily_dose": prescribed},
            usual_range={"low": low, "high": high},
            max_limits={
                "daily": maximum,
                "per_procedure": procedure_max,
                "cumulative": get(rule, "max_cumulative"),
            },
            alerts=alerts,
            missing_data=missing,
            source_refs=list(get(rule, "source_refs", []) or []),
            validation_status=validation,
            requires_human_review=validation != "validated" or bool(alerts) or bool(missing),
            educational_notice=(
                "Cálculo demonstrativo; confirmar bula, fonte e protocolo institucional."
            ),
        )

    @staticmethod
    def _bmi(weight: float, height_cm: float) -> float:
        return float(weight) / ((float(height_cm) / 100) ** 2)
