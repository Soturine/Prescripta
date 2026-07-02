from app.domain.alert import RiskLevel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.services.allergy_checker import check_allergies


def test_blocks_when_patient_has_allergy_to_active_ingredient() -> None:
    patient = Patient(
        id=1,
        name="Teste",
        birth_date=None,
        age=40,
        weight_kg=70,
        height_cm=170,
        allergies=["Ibuprofeno"],
        comorbidities=[],
        current_medications=[],
    )
    medication = Medication(
        id=1,
        brand_name="Ibuvida",
        active_ingredient="ibuprofeno",
        therapeutic_class="anti-inflamatorio",
        max_daily_dose_mg=2400,
        allowed_routes=["oral"],
        contraindications=[],
    )

    alerts = check_allergies(patient, medication)

    assert alerts
    assert alerts[0].severity == RiskLevel.CRITICAL
    assert alerts[0].code == "ALLERGY_BLOCK"
