from fastapi.testclient import TestClient

from app.database.models import AuditEventModel
from app.domain.user import UserRole


def test_cross_institution_access_is_denied_and_audited(
    client: TestClient, create_test_user, auth_headers, db_session
):
    create_test_user(
        email="owner@orga.local",
        password="Admin@12345",
        role=UserRole.ADMIN,
        institution_id="org-a",
    )
    create_test_user(
        email="outsider@orgb.local",
        password="Admin@12345",
        role=UserRole.MEDICO,
        institution_id="org-b",
    )
    owner_headers = auth_headers("owner@orga.local", "Admin@12345")
    outsider_headers = auth_headers("outsider@orgb.local", "Admin@12345")
    patient = client.post(
        "/api/patients",
        headers=owner_headers,
        json={
            "name": "Paciente Escopo A",
            "age": 50,
            "weight_kg": 70,
            "allergies": [],
            "comorbidities": [],
            "current_medications": [],
        },
    ).json()
    medication = client.post(
        "/api/medications",
        headers=owner_headers,
        json={
            "brand_name": "Escopo Demo",
            "active_ingredient": "escopo demo",
            "therapeutic_class": "teste",
            "max_daily_dose_mg": 100,
            "allowed_routes": ["oral"],
            "contraindications": [],
        },
    ).json()
    decision = client.post(
        "/api/prescriptions/check",
        headers=owner_headers,
        json={
            "patient_id": patient["id"],
            "medication_id": medication["id"],
            "dose_mg": 10,
            "frequency_per_day": 1,
            "route": "oral",
        },
    ).json()
    audit_id = decision["audit_id"]

    listed = client.get("/api/patients", headers=outsider_headers)
    patient_read = client.get(f"/api/patients/{patient['id']}", headers=outsider_headers)
    prescription = client.post(
        "/api/prescriptions/check",
        headers=outsider_headers,
        json={
            "patient_id": patient["id"],
            "medication_id": medication["id"],
            "dose_mg": 10,
            "frequency_per_day": 1,
            "route": "oral",
        },
    )
    report = client.get(
        f"/api/reports/prescriptions/{audit_id}/preview", headers=outsider_headers
    )
    exported = client.get(
        f"/api/exports/prescriptions/{audit_id}.json", headers=outsider_headers
    )
    counseling = client.post(
        f"/api/prescriptions/{audit_id}/patient-counseling", headers=outsider_headers
    )

    assert all(item["id"] != patient["id"] for item in listed.json())
    assert patient_read.status_code == 404
    assert prescription.status_code == 404
    assert report.status_code == 404
    assert exported.status_code == 404
    assert counseling.status_code == 404
    denied = db_session.query(AuditEventModel).filter(
        AuditEventModel.action == "authorization.denied"
    ).all()
    assert len(denied) >= 5
    assert all(event.user_email is None for event in denied)
