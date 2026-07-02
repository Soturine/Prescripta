from app.domain.alert import PrescriptionStatus, RiskLevel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.services.risk_engine import RiskEngine


def _patient(**overrides: object) -> Patient:
    values = {
        "id": 1,
        "name": "Paciente",
        "birth_date": None,
        "age": 40,
        "weight_kg": 70,
        "height_cm": 170,
        "allergies": [],
        "comorbidities": [],
        "current_medications": [],
    }
    values.update(overrides)
    return Patient(**values)


def _medication(**overrides: object) -> Medication:
    values = {
        "id": 1,
        "brand_name": "Seguro",
        "active_ingredient": "seguridina",
        "therapeutic_class": "teste",
        "max_daily_dose_mg": 1000,
        "allowed_routes": ["oral"],
        "contraindications": [],
        "notes": None,
    }
    values.update(overrides)
    return Medication(**values)


def test_polypharmacy_generates_moderate_alert() -> None:
    result = RiskEngine().evaluate(
        _patient(current_medications=["a", "b", "c", "d", "e"]),
        _medication(),
        PrescriptionInput(dose_mg=100, frequency_per_day=1, route="oral"),
    )

    assert result.risk_level == RiskLevel.MODERATE
    assert any(alert.code == "POLYPHARMACY" for alert in result.alerts)


def test_elderly_patient_increases_risk_level() -> None:
    result = RiskEngine().evaluate(
        _patient(age=70),
        _medication(),
        PrescriptionInput(dose_mg=100, frequency_per_day=1, route="oral"),
    )

    assert result.risk_level == RiskLevel.MODERATE
    assert result.status == PrescriptionStatus.ATTENTION


def test_release_when_no_relevant_risk_exists() -> None:
    result = RiskEngine().evaluate(
        _patient(),
        _medication(),
        PrescriptionInput(dose_mg=100, frequency_per_day=1, route="oral"),
    )

    assert result.status == PrescriptionStatus.RELEASED
    assert result.risk_level == RiskLevel.LOW
    assert result.alerts == []


def test_invalid_route_generates_high_alert() -> None:
    result = RiskEngine().evaluate(
        _patient(),
        _medication(allowed_routes=["oral"]),
        PrescriptionInput(dose_mg=100, frequency_per_day=1, route="intravenosa"),
    )

    assert result.risk_level == RiskLevel.HIGH
    assert any(alert.code == "INVALID_ROUTE" for alert in result.alerts)
