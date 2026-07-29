from fastapi.testclient import TestClient

from app.database.models import MedicationModel, PatientModel
from app.domain.user import UserRole


def _headers(client: TestClient, create_test_user, auth_headers, role: UserRole) -> dict[str, str]:
    email = f"{role.value}@test.local"
    create_test_user(email=email, password="Admin@12345", role=role)
    return auth_headers(email, "Admin@12345")


def test_json_import_requires_consent_and_accepts_after_human_review(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _headers(client, create_test_user, auth_headers, UserRole.ADMIN)
    denied = client.post(
        "/api/integrations/json/import",
        headers=headers,
        json={
            "consent_confirmed": False,
            "purpose": "teste",
            "authorized_by": "Paciente Demo",
            "source_system": "json_demo",
            "payload": {"current_medications": ["Novalgina"]},
        },
    )
    assert denied.status_code == 400

    created = client.post(
        "/api/integrations/json/import",
        headers=headers,
        json={
            "consent_confirmed": True,
            "purpose": "teste",
            "authorized_by": "Paciente Demo",
            "source_system": "json_demo",
            "payload": {
                "patient": {"name": "Paciente Importado", "birth_date": "1990-01-01"},
                "current_medications": ["Novalgina"],
                "conditions": ["DRC"],
            },
        },
    )
    payload = created.json()
    assert created.status_code == 200
    assert payload["status"] == "pending_review"
    assert payload["records"]
    assert any(
        record["mapped_payload"].get("normalized_value") == "dipirona"
        for record in payload["records"]
    )

    accepted = client.post(f"/api/integrations/imports/{payload['id']}/accept", headers=headers)
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"


def test_fhir_and_csv_imports_create_pending_batches(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _headers(client, create_test_user, auth_headers, UserRole.FARMACEUTICO)
    fhir = client.post(
        "/api/integrations/fhir/import-bundle",
        headers=headers,
        json={
            "consent_confirmed": True,
            "purpose": "teste",
            "authorized_by": "Paciente Demo",
            "source_system": "fhir_demo",
            "bundle": {
                "resourceType": "Bundle",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Patient",
                            "name": [{"given": ["Ana"], "family": "FHIR"}],
                            "birthDate": "1990-01-01",
                        }
                    },
                    {
                        "resource": {
                            "resourceType": "MedicationStatement",
                            "medicationCodeableConcept": {"text": "metamizol"},
                        }
                    },
                ],
            },
        },
    )
    csv_response = client.post(
        "/api/integrations/csv/import",
        headers=headers,
        json={
            "consent_confirmed": True,
            "purpose": "teste",
            "authorized_by": "Paciente Demo",
            "source_system": "csv_demo",
            "csv_text": "record_type,value\nmedication,Novalgina\ncondition,renal\n",
        },
    )

    assert fhir.status_code == 200
    assert fhir.json()["status"] == "pending_review"
    assert csv_response.status_code == 200
    assert csv_response.json()["records"]


def test_auditor_can_view_but_cannot_accept_import(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    admin_headers = _headers(client, create_test_user, auth_headers, UserRole.ADMIN)
    created = client.post(
        "/api/integrations/json/import",
        headers=admin_headers,
        json={
            "consent_confirmed": True,
            "purpose": "teste",
            "authorized_by": "Paciente Demo",
            "source_system": "json_demo",
            "payload": {"conditions": ["renal"]},
        },
    )
    auditor_headers = _headers(client, create_test_user, auth_headers, UserRole.AUDITOR)

    listed = client.get("/api/integrations/imports", headers=auditor_headers)
    accepted = client.post(
        f"/api/integrations/imports/{created.json()['id']}/accept",
        headers=auditor_headers,
    )

    assert listed.status_code == 200
    assert accepted.status_code == 403


def test_cds_prescription_check_persist_false_does_not_create_patient(
    client: TestClient,
    create_test_user,
    auth_headers,
    db_session,
) -> None:
    headers = _headers(client, create_test_user, auth_headers, UserRole.MEDICO)
    db_session.add(
        MedicationModel(
            brand_name="Rifampicina Demo",
            active_ingredient="rifampicina",
            therapeutic_class="rifamicina",
            max_daily_dose_mg=600,
            allowed_routes=["oral"],
            contraindications=[],
            validation_status="demo",
            dose_source_refs=["demo:rifampicina:dose"],
            policy_source_refs=["demo:rifampicina:policy"],
        )
    )
    db_session.commit()
    before_count = db_session.query(PatientModel).count()
    response = client.post(
        "/api/cds/prescription-check",
        headers=headers,
        json={
            "patient": {
                "age": 30,
                "weight_kg": 70,
                "hypertension": False,
                "diabetes": False,
                "reproductive_gynecologic_factors": ["uso_anticoncepcional_hormonal"],
            },
            "medication_request": {
                "active_ingredient": "rifampicina",
                "dose_mg": 300,
                "frequency_per_day": 1,
                "route": "oral",
                "duration_days": 5,
            },
            "allergies": [],
            "conditions": [],
            "current_medications": [],
            "persist": False,
        },
    )
    after_count = db_session.query(PatientModel).count()

    assert response.status_code == 200
    assert response.json()["cards"]
    assert response.json()["audit_id"].startswith("cds-")
    assert response.json()["decision"]["decision_status"] != "evaluated_no_issue"
    assert after_count == before_count


def test_cds_rejects_client_supplied_clinical_rule(
    client: TestClient, create_test_user, auth_headers
):
    headers = _headers(client, create_test_user, auth_headers, UserRole.MEDICO)
    response = client.post(
        "/api/cds/prescription-check",
        headers=headers,
        json={
            "patient": {"weight_kg": 70},
            "medication_request": {
                "active_ingredient": "rifampicina",
                "dose_mg": 1,
                "frequency_per_day": 1,
                "route": "oral",
                "max_daily_dose_mg": 999999,
            },
        },
    )
    assert response.status_code == 422


def test_cds_is_idempotent_per_user_and_rejects_key_reuse(
    client: TestClient, create_test_user, auth_headers, db_session
):
    headers = _headers(client, create_test_user, auth_headers, UserRole.MEDICO) | {
        "Idempotency-Key": "cds-test-1"
    }
    db_session.add(
        MedicationModel(
            brand_name="Dose Demo",
            active_ingredient="dose demo",
            therapeutic_class="teste",
            max_daily_dose_mg=10,
            allowed_routes=["oral"],
            contraindications=[],
        )
    )
    db_session.commit()
    body = {
        "patient": {"weight_kg": 70},
        "medication_request": {
            "active_ingredient": "dose demo",
            "dose_mg": 1,
            "frequency_per_day": 1,
            "route": "oral",
        },
    }
    first = client.post("/api/cds/prescription-check", headers=headers, json=body)
    repeated = client.post("/api/cds/prescription-check", headers=headers, json=body)
    changed = client.post(
        "/api/cds/prescription-check",
        headers=headers,
        json=body | {"allergies": []},
    )
    assert first.status_code == repeated.status_code == 200
    assert first.json() == repeated.json()
    assert changed.status_code == 409
