from app.domain.alert import RiskLevel
from app.domain.medication import Medication
from app.domain.prescription import PrescriptionInput
from app.services.dose_calculator import calculate_daily_dose, check_max_daily_dose


def test_blocks_when_daily_dose_exceeds_maximum() -> None:
    medication = Medication(
        id=1,
        brand_name="Dosemed",
        active_ingredient="dosemida",
        therapeutic_class="teste",
        max_daily_dose_mg=100,
        allowed_routes=["oral"],
        contraindications=[],
    )
    prescription = PrescriptionInput(dose_mg=60, frequency_per_day=2, route="oral")

    alerts = check_max_daily_dose(medication, prescription)

    assert calculate_daily_dose(prescription) == 120
    assert alerts[0].severity == RiskLevel.CRITICAL
