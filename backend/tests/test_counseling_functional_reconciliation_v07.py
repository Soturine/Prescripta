from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import MedicationModel, PatientModel
from app.database.seed import seed_demo_data
from app.schemas.counseling_schema import MedicationCounselingProviderOutput
from app.services.adverse_effect_taxonomy import category_for_code, taxonomy_snapshot
from app.services.medication_counseling_extractor import MedicationCounselingExtractor


def _seeded_headers(client: TestClient, db_session: Session, auth_headers) -> dict[str, str]:
    seed_demo_data(db_session)
    return auth_headers("admin@prescripta.local", "Admin@12345")


def _medication_by_active(db_session: Session, active: str) -> MedicationModel:
    medication = db_session.scalar(
        select(MedicationModel).where(MedicationModel.active_ingredient == active)
    )
    assert medication is not None
    return medication


def test_adverse_effect_taxonomy_contains_required_v07_categories() -> None:
    codes = {entry["code"] for entry in taxonomy_snapshot()}

    assert {"insonia", "sonolencia", "tontura"}.issubset(codes)
    assert {"alteracao_humor", "risco_serotoninergico"}.issubset(codes)
    assert {"baixa_libido", "alteracao_ejaculatoria"}.issubset(codes)
    assert {"dor_cabeca", "tremor", "hipertermia", "hipotermia"}.issubset(codes)
    assert {"dirigir", "operar_maquinas", "trabalho_em_altura"}.issubset(codes)
    assert {"procurar_atendimento", "reacao_alergica", "desmaio"}.issubset(codes)
    assert category_for_code("tremor") == "neurologic"


def test_counseling_generate_uses_fallback_source_and_keeps_pending_review(
    client: TestClient,
    db_session: Session,
    auth_headers,
) -> None:
    headers = _seeded_headers(client, db_session, auth_headers)
    created = client.post(
        "/api/medications",
        headers=headers,
        json={
            "brand_name": "Fonte Demo",
            "active_ingredient": "fonte demo",
            "therapeutic_class": "demo",
            "max_daily_dose_mg": 100,
            "allowed_routes": ["oral"],
            "contraindications": [],
            "notes": "Teste",
        },
    )

    response = client.post(
        f"/api/medications/{created.json()['id']}/counseling-summary/generate",
        headers=headers,
        json={
            "source_text": (
                "Fonte demonstrativa: pode causar tontura, sedacao, operar maquinas, "
                "dirigir e queda de pressao. Procurar atendimento em desmaio."
            )
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["validation_status"] == "pending_review"
    assert payload["generated_by"] == "fallback_deterministic"
    assert payload["requires_review"] is True
    assert payload["driving_warning"] is True
    assert "tontura" in payload["main_adverse_effects"]
    assert payload["jurisdiction"] == "BR"


def test_counseling_review_promotes_summary_to_validated(
    client: TestClient,
    db_session: Session,
    auth_headers,
) -> None:
    headers = _seeded_headers(client, db_session, auth_headers)
    medication = _medication_by_active(db_session, "tansulosina")

    response = client.post(
        f"/api/medications/{medication.id}/counseling-summary/review",
        headers=headers,
        json={"validation_status": "validated", "justification": "ok"},
    )

    assert response.status_code == 200
    assert response.json()["validation_status"] == "validated"
    assert response.json()["requires_review"] is False


def test_invalid_provider_json_is_rejected() -> None:
    class BadProvider:
        provider_name = "bad"

        def extract(self, _request):
            return {"confidence": "unsafe_free_text"}

    output = {"confidence": "unsafe_free_text"}
    with pytest.raises(ValidationError):
        MedicationCounselingProviderOutput.model_validate(output)

    medication = MedicationModel(
        brand_name="Teste",
        active_ingredient="teste",
        therapeutic_class="demo",
        max_daily_dose_mg=1,
        allowed_routes=["oral"],
        contraindications=[],
        notes="Fonte com tontura.",
    )
    with pytest.raises(ValidationError):
        MedicationCounselingExtractor(provider=BadProvider()).extract(
            medication,
            source_text="Fonte com tontura.",
        )


def test_tansulosina_demo_summary_includes_activity_pressure_and_sexual_effects(
    client: TestClient,
    db_session: Session,
    auth_headers,
) -> None:
    headers = _seeded_headers(client, db_session, auth_headers)
    medication = _medication_by_active(db_session, "tansulosina")

    response = client.get(
        f"/api/medications/{medication.id}/counseling-summary",
        headers=headers,
    )
    payload = response.json()

    assert response.status_code == 200
    assert "tontura" in payload["main_adverse_effects"]
    assert payload["driving_warning"] is True
    assert payload["machine_operation_warning"] is True
    assert payload["blood_pressure_warning"] is True
    assert "alteracao_ejaculatoria" in payload["libido_sexual_effects"]


def test_functional_profile_and_no_history_mode_shape_prescription_counseling(
    client: TestClient,
    db_session: Session,
    auth_headers,
) -> None:
    headers = _seeded_headers(client, db_session, auth_headers)
    medication = _medication_by_active(db_session, "tansulosina")
    patient = db_session.scalar(
        select(PatientModel).where(PatientModel.name == "Carlos Demonstracao")
    )
    assert patient is not None

    response = client.post(
        "/api/prescriptions/check",
        headers=headers,
        json={
            "patient_id": patient.id,
            "medication_id": medication.id,
            "dose_mg": 0.4,
            "frequency_per_day": 1,
            "route": "oral",
            "duration_days": 30,
        },
    )
    counseling = response.json()["patient_counseling"]

    assert response.status_code == 200
    assert counseling["functional_context"]["profile_known"] is True
    assert counseling["functional_context"]["personalized_warnings"]
    assert counseling["missing_data_mode"]["does_not_block_flow"] is True

    created = client.post(
        "/api/patients",
        headers=headers,
        json={"name": "Sem Historico", "age": 40, "weight_kg": 70},
    )
    no_history = client.post(
        "/api/prescriptions/check",
        headers=headers,
        json={
            "patient_id": created.json()["id"],
            "medication_id": medication.id,
            "dose_mg": 0.4,
            "frequency_per_day": 1,
            "route": "oral",
        },
    )
    no_history_payload = no_history.json()

    assert no_history.status_code == 200
    assert no_history_payload["missing_data_mode"]["incomplete_history"] is True
    assert "perfil funcional" in no_history_payload["missing_data_mode"]["missing_data"]
    assert no_history_payload["contextual_question"]["should_ask"] is True


def test_patient_functional_profile_endpoint_audits_updates(
    client: TestClient,
    db_session: Session,
    auth_headers,
) -> None:
    headers = _seeded_headers(client, db_session, auth_headers)
    patient = db_session.scalar(select(PatientModel).where(PatientModel.name == "Ana Exemplo"))
    assert patient is not None

    response = client.put(
        f"/api/patients/{patient.id}/functional-profile",
        headers=headers,
        json={
            "drives_regularly": True,
            "operates_machinery": True,
            "works_at_height": False,
            "source": "manual",
            "notes": "Teste v0.7",
        },
    )
    audit = client.get("/api/audit", headers=headers)

    assert response.status_code == 200
    assert response.json()["drives_regularly"] is True
    assert any(
        event["action"] == "patient.functional_profile.update" for event in audit.json()
    )


def test_granular_reconciliation_detects_conflict_and_records_item_decisions(
    client: TestClient,
    db_session: Session,
    auth_headers,
) -> None:
    headers = _seeded_headers(client, db_session, auth_headers)
    patient = db_session.scalar(select(PatientModel).where(PatientModel.name == "Ana Exemplo"))
    assert patient is not None

    created = client.post(
        "/api/integrations/json/import",
        headers=headers,
        json={
            "consent_confirmed": True,
            "purpose": "teste",
            "authorized_by": "Paciente Demo",
            "source_system": "json_v07",
            "patient_id": patient.id,
            "payload": {
                "patient": {"name": "Nome Conflitante", "birth_date": "1990-01-01"},
                "current_medications": ["Novalgina"],
                "conditions": ["renal"],
            },
        },
    )
    batch_id = created.json()["id"]
    reconciliation = client.get(
        f"/api/integrations/imports/{batch_id}/reconciliation",
        headers=headers,
    )
    payload = reconciliation.json()

    assert reconciliation.status_code == 200
    assert payload["summary"]["conflicts"] >= 1
    assert any(item["badge"] == "conflito" for item in payload["items"])

    safe = client.post(
        f"/api/integrations/imports/{batch_id}/reconciliation/accept-safe",
        headers=headers,
    )
    assert safe.status_code == 200

    conflict = next(item for item in payload["items"] if item["badge"] == "conflito")
    rejected = client.post(
        f"/api/integrations/imports/{batch_id}/reconciliation/items/{conflict['item_id']}/reject",
        headers=headers,
        json={"justification": "conflito mantido"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["decision"] == "rejected"

    new_item = next(
        item for item in payload["items"] if item["badge"] in {"novo", "possivel_match"}
    )
    accepted = client.post(
        f"/api/integrations/imports/{batch_id}/reconciliation/items/{new_item['item_id']}/accept",
        headers=headers,
        json={"justification": "aceite granular"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["decision"] == "accepted"

    audit = client.get("/api/audit", headers=headers)
    assert any(
        event["action"] == "clinical_reconciliation.item.accepted" for event in audit.json()
    )


def test_auditor_can_view_reconciliation_but_cannot_decide(
    client: TestClient,
    db_session: Session,
    auth_headers,
) -> None:
    headers = _seeded_headers(client, db_session, auth_headers)
    auditor_headers = auth_headers("auditor@prescripta.local", "Auditor@12345")
    created = client.post(
        "/api/integrations/json/import",
        headers=headers,
        json={
            "consent_confirmed": True,
            "purpose": "teste",
            "authorized_by": "Paciente Demo",
            "source_system": "json_v07",
            "payload": {"conditions": ["renal"]},
        },
    )
    batch_id = created.json()["id"]
    viewed = client.get(
        f"/api/integrations/imports/{batch_id}/reconciliation",
        headers=auditor_headers,
    )
    item_id = viewed.json()["items"][0]["item_id"]
    decided = client.post(
        f"/api/integrations/imports/{batch_id}/reconciliation/items/{item_id}/accept",
        headers=auditor_headers,
        json={"justification": None},
    )

    assert viewed.status_code == 200
    assert decided.status_code == 403
