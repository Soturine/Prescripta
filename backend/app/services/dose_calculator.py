from app.domain.alert import Alert, RiskLevel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput


def calculate_daily_dose(prescription: PrescriptionInput) -> float:
    return prescription.dose_mg * prescription.frequency_per_day


def check_max_daily_dose(medication: Medication, prescription: PrescriptionInput) -> list[Alert]:
    daily_total = calculate_daily_dose(prescription)
    if daily_total <= medication.max_daily_dose_mg:
        return []

    return [
        Alert(
            code="MAX_DAILY_DOSE_EXCEEDED",
            title="Dose diária acima do limite",
            description=(
                f"Dose diária calculada: {daily_total:g} mg. "
                f"Limite cadastrado: {medication.max_daily_dose_mg:g} mg."
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

    daily_total = calculate_daily_dose(prescription)
    weight_limit = float(medication.dose_mg_per_kg) * float(patient.weight_kg)
    if daily_total <= weight_limit:
        return []

    return [
        Alert(
            code="WEIGHT_BASED_DOSE_EXCEEDED",
            title="Dose por peso acima do limite cadastrado",
            description=(
                f"Dose diaria calculada: {daily_total:g} mg. "
                f"Limite por peso demonstrativo: {weight_limit:g} mg/dia "
                f"({medication.dose_mg_per_kg:g} mg/kg x {patient.weight_kg:g} kg)."
            ),
            severity=RiskLevel.HIGH,
            recommendation=("Revisar dose por kg, peso registrado e fonte antes de prosseguir."),
        )
    ]
