from app.domain.alert import Alert, RiskLevel
from app.domain.medication import Medication
from app.domain.prescription import PrescriptionInput


def calculate_daily_dose(prescription: PrescriptionInput) -> float:
    return prescription.dose_mg * prescription.frequency_per_day


def check_max_daily_dose(
    medication: Medication, prescription: PrescriptionInput
) -> list[Alert]:
    daily_total = calculate_daily_dose(prescription)
    if daily_total <= medication.max_daily_dose_mg:
        return []

    return [
        Alert(
            code="MAX_DAILY_DOSE_EXCEEDED",
            title="Dose diaria acima do limite",
            description=(
                f"Dose diaria calculada: {daily_total:g} mg. "
                f"Limite cadastrado: {medication.max_daily_dose_mg:g} mg."
            ),
            severity=RiskLevel.CRITICAL,
            recommendation="Bloquear a prescricao e recalcular dose/frequencia.",
        )
    ]
