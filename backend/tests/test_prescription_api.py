from fastapi.testclient import TestClient

from app.domain.user import UserRole


def test_prescription_check_endpoint_blocks_allergy_and_writes_audit(
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
            "name": "Paciente API",
            "age": 42,
            "weight_kg": 72,
            "height_cm": 171,
            "allergies": ["ibuprofeno"],
            "comorbidities": [],
            "current_medications": [],
        },
    )
    medication_response = client.post(
        "/api/medications",
        headers=headers,
        json={
            "brand_name": "Ibuvida",
            "active_ingredient": "ibuprofeno",
            "therapeutic_class": "anti-inflamatorio",
            "max_daily_dose_mg": 2400,
            "allowed_routes": ["oral"],
            "contraindications": [],
            "notes": "Teste",
        },
    )

    response = client.post(
        "/api/prescriptions/check",
        headers=headers,
        json={
            "patient_id": patient_response.json()["id"],
            "medication_id": medication_response.json()["id"],
            "dose_mg": 400,
            "frequency_per_day": 2,
            "route": "oral",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "bloqueado"
    assert payload["risk_level"] == "critico"
    assert payload["human_review_required"] is True
    assert payload["audit_id"] > 0

    audit_response = client.get("/api/audit", headers=headers)
    assert audit_response.status_code == 200
    prescription_events = [
        event for event in audit_response.json()["items"] if event["action"] == "prescription.check"
    ]
    assert len(prescription_events) == 1
    assert prescription_events[0]["user_email"] == "admin@test.local"
