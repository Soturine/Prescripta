from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import MedicationModel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.domain.user import UserRole
from app.knowledge.rag_service import ClinicalRAGService
from app.repositories.medication_repository import MedicationRepository
from app.services.alternative_service import AlternativeService
from app.services.normalizer import dedupe_terms, normalize_text
from app.services.risk_engine import RiskEngine


def _patient(**overrides: Any) -> Patient:
    values = {
        "id": 1,
        "name": "Paciente Clinico",
        "birth_date": None,
        "age": 72,
        "weight_kg": 80,
        "height_cm": 170,
        "allergies": [],
        "comorbidities": [],
        "current_medications": [],
        "renal_condition": None,
        "hepatic_condition": None,
        "cardiac_condition": None,
        "gastrointestinal_history": None,
        "hypertension": False,
        "diabetes": False,
        "pregnancy_or_lactation": None,
        "adverse_reactions": [],
        "clinical_notes": None,
        "clinical_profile_reviewed_at": None,
        "clinical_profile_completeness_score": 90,
    }
    values.update(overrides)
    return Patient(**values)


def _medication(**overrides: Any) -> Medication:
    values = {
        "id": 1,
        "brand_name": "Ibuvida",
        "active_ingredient": "ibuprofeno",
        "therapeutic_class": "anti-inflamatorio",
        "max_daily_dose_mg": 2400,
        "allowed_routes": ["oral"],
        "contraindications": [],
        "notes": "Teste",
        "max_duration_days": 5,
        "max_cumulative_dose_mg": 7200,
        "condition_specific_limits": {"renal": 1200, "hepatico": 800},
        "renal_caution": True,
        "hepatic_caution": True,
        "cardiac_caution": True,
        "gastrointestinal_caution": True,
        "elderly_caution": True,
        "metabolism_organs": ["hepatico"],
        "elimination_organs": ["renal"],
        "organs_involved": ["renal", "gastrointestinal"],
        "relevant_adverse_effects": ["sangramento gastrointestinal"],
        "structured_contraindications": ["renal"],
        "therapeutic_action": "analgesia",
        "alternative_group": "analgesia",
        "related_medications": ["paracetamol"],
        "knowledge_source": "Teste",
    }
    values.update(overrides)
    return Medication(**values)


def _prescription(**overrides: Any) -> PrescriptionInput:
    values = {
        "dose_mg": 400,
        "frequency_per_day": 2,
        "route": "oral",
        "duration_days": 3,
        "indication": "dor",
        "professional_notes": "Teste",
    }
    values.update(overrides)
    return PrescriptionInput(**values)


def _codes(result) -> set[str]:
    return {alert.code for alert in result.alerts}


def test_alerts_for_renal_hepatic_gastrointestinal_and_elderly_context() -> None:
    result = RiskEngine().evaluate(
        _patient(
            renal_condition="renal",
            hepatic_condition="hepatico",
            gastrointestinal_history="gastrointestinal",
        ),
        _medication(),
        _prescription(),
    )

    codes = _codes(result)
    assert "RENAL_CAUTION" in codes
    assert "HEPATIC_CAUTION" in codes
    assert "GASTROINTESTINAL_CAUTION" in codes
    assert "ELDERLY_CAUTION" in codes


def test_alert_for_adverse_reaction_history() -> None:
    result = RiskEngine().evaluate(
        _patient(adverse_reactions=["sangramento gastrointestinal"]),
        _medication(),
        _prescription(),
    )

    assert "ADVERSE_REACTION_HISTORY" in _codes(result)


def test_alerts_for_cumulative_dose_duration_and_condition_specific_limit() -> None:
    result = RiskEngine().evaluate(
        _patient(renal_condition="renal"),
        _medication(max_daily_dose_mg=5000),
        _prescription(dose_mg=700, frequency_per_day=2, duration_days=8),
    )

    codes = _codes(result)
    assert "CUMULATIVE_DOSE_EXCEEDED" in codes
    assert "DURATION_LIMIT_EXCEEDED" in codes
    assert "CONDITION_SPECIFIC_LIMIT_EXCEEDED" in codes


def test_missing_duration_and_incomplete_profile_generate_review_alerts() -> None:
    result = RiskEngine().evaluate(
        _patient(renal_condition="renal", clinical_profile_completeness_score=40),
        _medication(),
        _prescription(duration_days=None),
    )

    codes = _codes(result)
    assert "MISSING_DURATION" in codes
    assert "INCOMPLETE_CLINICAL_PROFILE" in codes


def test_critical_block_results_in_low_compatibility() -> None:
    result = RiskEngine().evaluate(
        _patient(allergies=["ibuprofeno"]),
        _medication(),
        _prescription(),
    )

    assert result.status.value == "bloqueado"
    assert result.compatibility["level"] == "baixa"
    assert result.compatibility["review_required"] is True


def test_rag_textual_fallback_returns_internal_sources() -> None:
    hits = ClinicalRAGService().retrieve_for_prescription(
        _patient(renal_condition="renal"),
        _medication(),
        _prescription(),
    )

    assert hits
    assert any(hit["source"] != "fallback" for hit in hits)
    assert all("educational_notice" in hit for hit in hits)


def test_normalization_and_deduplication_of_terms() -> None:
    assert normalize_text("Insuficiência renal") == "renal"
    assert dedupe_terms(["Nimesulida", "nimesulida", "NIMESULIDA"]) == ["nimesulida"]
    assert dedupe_terms(["fígado", "figado", "hepático"]) == ["hepatico"]


def test_alternatives_are_evaluated_by_risk_engine(db_session: Session) -> None:
    db_session.add_all(
        [
            MedicationModel(
                brand_name="Ibuvida",
                active_ingredient="ibuprofeno",
                therapeutic_class="anti-inflamatorio",
                max_daily_dose_mg=2400,
                allowed_routes=["oral"],
                contraindications=[],
                alternative_group="analgesia",
                renal_caution=True,
            ),
            MedicationModel(
                brand_name="Paracetamol Demo",
                active_ingredient="paracetamol",
                therapeutic_class="analgesico",
                max_daily_dose_mg=3000,
                allowed_routes=["oral"],
                contraindications=[],
                alternative_group="analgesia",
            ),
        ]
    )
    db_session.commit()
    repository = MedicationRepository(db_session)
    original = Medication.from_record(repository.list()[0])

    options = AlternativeService(repository).evaluated_options(
        _patient(renal_condition="renal"),
        original,
        _prescription(),
        should_include=True,
    )

    assert options
    assert options[0]["status"] in {"liberado", "atencao", "bloqueado"}
    assert "risk_level" in options[0]


def test_quick_triage_preserves_existing_data_and_audits(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    create_test_user(email="admin@test.local", password="Admin@12345", role=UserRole.ADMIN)
    headers = auth_headers("admin@test.local", "Admin@12345")
    patient_response = client.post(
        "/api/patients",
        headers=headers,
        json={
            "name": "Paciente Triage",
            "age": 50,
            "weight_kg": 70,
            "height_cm": 170,
            "allergies": ["dipirona"],
            "comorbidities": [],
            "current_medications": ["losartana"],
        },
    )

    triage_response = client.patch(
        f"/api/patients/{patient_response.json()['id']}/quick-triage",
        headers=headers,
        json={
            "renal_condition": True,
            "allergies": ["DIPIRONA"],
            "current_medications": ["losartana", "metformina"],
            "adverse_reactions": ["náusea"],
        },
    )
    audit_response = client.get("/api/audit", headers=headers)

    payload = triage_response.json()
    assert triage_response.status_code == 200
    assert payload["renal_condition"] == "funcao_renal_a_revisar"
    assert payload["allergies"] == ["dipirona"]
    assert payload["current_medications"] == ["losartana", "metformina"]
    assert any(event["action"] == "patient.quick_triage" for event in audit_response.json())
