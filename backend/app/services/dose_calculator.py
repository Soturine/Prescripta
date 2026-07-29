from decimal import Decimal

from app.domain.alert import Alert, RiskLevel
from app.domain.dose_units import convert_value
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput


def calculate_daily_dose(prescription: PrescriptionInput) -> float | None:
    return prescription.daily_total_mg


def check_max_daily_dose(medication: Medication, prescription: PrescriptionInput) -> list[Alert]:
    daily_total = prescription.daily_total_mg or prescription.daily_upper_mg
    if daily_total is None:
        return []
    converted = convert_value(
        Decimal(str(daily_total)),
        "mg",
        medication.max_daily_dose_unit,
    )
    if converted is None:
        return [
            Alert(
                code="DAILY_DOSE_DIMENSION_UNPROVEN",
                title="Dimensão do limite diário não comprovada",
                description="A dose e o limite diário não possuem unidades compatíveis.",
                severity=RiskLevel.HIGH,
                recommendation="Revisar unidade, base corporal e regra antes de prosseguir.",
            )
        ]
    maximum = Decimal(str(medication.max_daily_dose_mg))
    if converted <= maximum:
        return []

    return [
        Alert(
            code="MAX_DAILY_DOSE_EXCEEDED",
            title="Dose diária acima do limite",
            description=(
                f"Dose diária calculada: {converted.normalize()} "
                f"{medication.max_daily_dose_unit}. Limite cadastrado: "
                f"{maximum.normalize()} {medication.max_daily_dose_unit}."
            ),
            severity=RiskLevel.CRITICAL,
            recommendation="Bloquear a prescrição e recalcular dose/frequência.",
        )
    ]


def check_weight_based_dose(
    patient: Patient,
    medication: Medication,
    prescription: PrescriptionInput,
) -> list[Alert]:
    if not medication.dose_by_weight_enabled or not medication.dose_mg_per_kg:
        return []

    daily_total = prescription.daily_total_mg or prescription.daily_upper_mg
    if daily_total is None:
        return []
    weight_limit = Decimal(str(medication.dose_mg_per_kg)) * Decimal(str(patient.weight_kg))
    daily_decimal = Decimal(str(daily_total))
    if daily_decimal <= weight_limit:
        return []

    return [
        Alert(
            code="WEIGHT_BASED_DOSE_EXCEEDED",
            title="Dose por peso acima do limite cadastrado",
            description=(
                f"Dose diaria calculada: {daily_decimal.normalize()} mg. "
                f"Limite por peso demonstrativo: {weight_limit.normalize()} mg/dia "
                f"({medication.dose_mg_per_kg:g} mg/kg x {patient.weight_kg:g} kg)."
            ),
            severity=RiskLevel.HIGH,
            recommendation=("Revisar dose por kg, peso registrado e fonte antes de prosseguir."),
        )
    ]
