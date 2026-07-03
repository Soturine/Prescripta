from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.integrations.services.clinical_deduplication_service import ClinicalDeduplicationService
from app.integrations.services.patient_matching_service import PatientMatchingService
from app.services.patient_identifier_service import PatientIdentifierService
from app.services.risk_engine import RiskEngine


def _patient(**overrides: object) -> Patient:
    values = {
        "id": 1,
        "name": "Paciente v06",
        "birth_date": None,
        "age": 36,
        "weight_kg": 70,
        "height_cm": 168,
        "allergies": [],
        "comorbidities": [],
        "current_medications": [],
        "clinical_profile_completeness_score": 90,
    }
    values.update(overrides)
    return Patient(**values)


def _medication(**overrides: object) -> Medication:
    values = {
        "id": 1,
        "brand_name": "Demo",
        "active_ingredient": "demo",
        "therapeutic_class": "teste",
        "max_daily_dose_mg": 1000,
        "max_duration_days": 10,
        "max_cumulative_dose_mg": 5000,
        "allowed_routes": ["oral"],
        "contraindications": [],
    }
    values.update(overrides)
    return Medication(**values)


def _codes(result) -> set[str]:
    return {alert.code for alert in result.alerts}


def test_exposure_plan_calculates_daily_and_cumulative_dose() -> None:
    result = RiskEngine().evaluate(
        _patient(),
        _medication(),
        PrescriptionInput(dose_mg=250, frequency_per_day=2, route="oral", duration_days=6),
    )

    assert result.dose_summary["daily_total_mg"] == 500
    assert result.dose_summary["estimated_cumulative_dose_mg"] == 3000
    assert result.dose_summary["exposure_plan"]["calculated_cumulative_dose_mg"] == 3000


def test_monitoring_and_pharmacokinetic_profile_generate_review_alerts() -> None:
    result = RiskEngine().evaluate(
        _patient(renal_condition="funcao_renal_a_revisar"),
        _medication(
            monitoring_required=True,
            monitoring_notes="Monitorar funcao renal.",
            renal_elimination_level="alto",
        ),
        PrescriptionInput(dose_mg=100, frequency_per_day=1, route="oral", duration_days=40),
    )

    codes = _codes(result)
    assert "MONITORING_REQUIRED" in codes
    assert "PROLONGED_USE_REVIEW" in codes
    assert "RENAL_ELIMINATION_REVIEW" in codes


def test_neuropsychiatric_serotonergic_and_seizure_reviews() -> None:
    result = RiskEngine().evaluate(
        _patient(
            current_medications=["fluoxetina"],
            mental_health_factors=["epilepsia_convulsoes"],
        ),
        _medication(
            therapeutic_class="inibidor seletivo da recaptacao de serotonina",
            neuropsychiatric_cautions=["risco_serotoninergico", "limiar_convulsivo"],
        ),
        PrescriptionInput(dose_mg=50, frequency_per_day=1, route="oral", duration_days=5),
    )

    codes = _codes(result)
    assert "SEROTONERGIC_REVIEW" in codes
    assert "SEIZURE_THRESHOLD_REVIEW" in codes


def test_rifamycin_contraceptive_rule_does_not_apply_to_all_antibiotics() -> None:
    patient = _patient(reproductive_gynecologic_factors=["uso_anticoncepcional_hormonal"])
    rifampicin = RiskEngine().evaluate(
        patient,
        _medication(active_ingredient="rifampicina"),
        PrescriptionInput(dose_mg=300, frequency_per_day=1, route="oral", duration_days=5),
    )
    amoxicillin = RiskEngine().evaluate(
        patient,
        _medication(active_ingredient="amoxicilina", therapeutic_class="antibiotico"),
        PrescriptionInput(dose_mg=500, frequency_per_day=3, route="oral", duration_days=5),
    )

    assert "RIFAMYCIN_HORMONAL_CONTRACEPTIVE_REVIEW" in _codes(rifampicin)
    assert "RIFAMYCIN_HORMONAL_CONTRACEPTIVE_REVIEW" not in _codes(amoxicillin)


def test_patient_identifier_hash_mask_and_matching(db_session) -> None:
    from app.database.models import PatientModel

    patient = PatientModel(name="Paciente Match", age=30, weight_kg=70)
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    identifier = PatientIdentifierService(db_session).create(
        patient_id=patient.id,
        identifier_type="hospital_record_number",
        identifier_value="HOSP-ABC-1234",
        issuing_system="hospital_demo",
        is_primary=True,
    )
    matches = PatientMatchingService(db_session).find_matches(
        patient_payload={"name": "Outro Paciente"},
        identifiers=[
            {
                "identifier_type": "hospital_record_number",
                "identifier_value": "HOSP-ABC-1234",
            }
        ],
    )

    assert identifier.display_masked.endswith("1234")
    assert identifier.identifier_value_hash != "HOSP-ABC-1234"
    assert matches[0].patient_id == patient.id
    assert matches[0].requires_human_review is True
    assert matches[0].auto_merge_allowed is False


def test_clinical_deduplication_preserves_original_value() -> None:
    result = ClinicalDeduplicationService().deduplicate_medication("Novalgina")
    condition = ClinicalDeduplicationService().deduplicate_condition("problema nos rins")

    assert result.original_value == "Novalgina"
    assert result.normalized_value == "dipirona"
    assert result.mapped_code == "dipirona"
    assert condition.original_value == "problema nos rins"
    assert condition.requires_review is True

