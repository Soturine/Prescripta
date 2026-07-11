import subprocess
from pathlib import Path
from types import SimpleNamespace

from app.services.dose_intelligence import DoseIntelligenceService
from app.services.prescribing_policy import PrescribingPolicyService
from app.services.psychotropic_safety import PsychotropicSafetyService


def _patient(**overrides):
    values = {
        "age": 40,
        "weight_kg": 70,
        "height_cm": 170,
        "current_medications": [],
        "comorbidities": [],
        "mental_health_factors": [],
        "reproductive_gynecologic_factors": [],
        "pregnancy_or_lactation": None,
        "renal_condition": None,
        "hepatic_condition": None,
        "cardiac_condition": None,
        "clinical_notes": None,
        "diabetes": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _codes(new: str, patient) -> set[str]:
    medication = SimpleNamespace(active_ingredient=new)
    return {item.code for item in PsychotropicSafetyService().evaluate(medication, patient)}


def test_psychotropic_required_combinations():
    assert "SEROTONERGIC_MAOI_COMBINATION" in _codes(
        "sertralina", _patient(current_medications=["tranilcipromina"])
    )
    assert "SEROTONERGIC_TRAMADOL" in _codes(
        "sertralina", _patient(current_medications=["tramadol"])
    )
    assert "BENZODIAZEPINE_OPIOID" in _codes("diazepam", _patient(current_medications=["morfina"]))
    assert "LITHIUM_INTERACTION" in _codes("lítio", _patient(current_medications=["ibuprofeno"]))


def test_psychotropic_patient_vulnerabilities_and_missing_question():
    assert "ANTIDEPRESSANT_BIPOLAR_MANIA" in _codes(
        "fluoxetina", _patient(mental_health_factors=["transtorno bipolar"])
    )
    assert "BUPROPION_SEIZURE_HISTORY" in _codes(
        "bupropiona", _patient(comorbidities=["epilepsia"])
    )
    assert "VALPROATE_REPRODUCTIVE_CONTEXT" in _codes(
        "valproato", _patient(pregnancy_or_lactation=True)
    )
    assert "MISSING_MENTAL_HEALTH_HISTORY" in _codes("sertralina", _patient())


def test_dose_intelligence_weight_bsa_range_and_pending_review():
    service = DoseIntelligenceService()
    weight = service.evaluate(
        {
            "calculation_basis": "actual_weight",
            "dose_per_basis": 2,
            "usual_low": 1,
            "usual_high": 3,
            "max_daily": 4,
            "max_daily_is_per_basis": True,
            "dose_unit": "mg/kg/dia",
            "validation_status": "pending_review",
            "source_refs": ["demo:dose:v0.8.5"],
        },
        _patient(),
        {"dose_mg": 70, "frequency_per_day": 2},
    )
    assert weight.calculated_dose == 140
    assert weight.status == "within_usual_range"
    assert weight.requires_human_review is True
    bsa = service.evaluate(
        {
            "calculation_basis": "bsa",
            "dose_per_basis": 100,
            "dose_unit": "mg/m²",
            "source_refs": ["demo:dose:v0.8.5"],
        },
        _patient(),
    )
    assert bsa.inputs_used["bsa_m2"] > 1
    assert "√" in bsa.calculation_formula


def test_prescribing_policy_never_turns_demo_into_legal_block():
    user = SimpleNamespace(
        role="medico",
        specialty_code="general_practice",
        credential_verification_status="demo_unverified",
    )
    medication = SimpleNamespace(
        policy_type="institutional_policy",
        policy_strength="hard_block",
        required_specialty_codes=["anesthesiology"],
        recommended_specialty_codes=[],
        policy_source_refs=[],
        policy_validation_status="pending_review",
        prescription_form_type=None,
        requires_second_review=False,
    )
    result = PrescribingPolicyService().evaluate(user, medication)
    assert result.status == "requires_specialist_review"
    assert result.legal_regulatory_notes == []
    assert result.requires_human_review is True


def test_text_quality_script_rejects_visible_unaccented_terms(tmp_path: Path):
    fixture = tmp_path / "visible.md"
    fixture.write_text("A prescricao nao tem contexto clinico.\n", encoding="utf-8")
    script = Path(__file__).parents[2] / "scripts" / "check-text-quality.ps1"
    completed = subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-Path",
            str(fixture),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "Termo sem acento" in completed.stdout
