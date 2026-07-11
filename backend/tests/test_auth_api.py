from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.domain.user import UserRole
from app.repositories.user_repository import UserRepository


def test_valid_login_returns_token_and_user(client: TestClient, create_test_user) -> None:
    create_test_user(email="admin@test.local", password="Admin@12345", role=UserRole.ADMIN)

    response = client.post(
        "/api/auth/login",
        json={"email": "admin@test.local", "password": "Admin@12345"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
    assert payload["user"]["role"] == "admin"


def test_invalid_login_returns_401(client: TestClient, create_test_user) -> None:
    create_test_user(email="admin@test.local", password="Admin@12345", role=UserRole.ADMIN)

    response = client.post(
        "/api/auth/login",
        json={"email": "admin@test.local", "password": "wrong"},
    )

    assert response.status_code == 401


def test_password_is_not_stored_as_plain_text(db_session: Session, create_test_user) -> None:
    user = create_test_user(email="admin@test.local", password="Admin@12345")

    stored = UserRepository(db_session).get(user.id)

    assert stored is not None
    assert stored.hashed_password != "Admin@12345"
    assert "Admin@12345" not in stored.hashed_password


def test_inactive_user_cannot_access_protected_route(client: TestClient, create_test_user) -> None:
    user = create_test_user(
        email="inactive@test.local",
        password="Admin@12345",
        role=UserRole.ADMIN,
        is_active=False,
    )
    token = create_access_token(str(user.id))

    response = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_protected_route_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/dashboard")

    assert response.status_code == 401


def test_profile_without_permission_returns_403(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    create_test_user(
        email="auditor@test.local",
        password="Auditor@12345",
        role=UserRole.AUDITOR,
    )
    headers = auth_headers("auditor@test.local", "Auditor@12345")

    response = client.post(
        "/api/patients",
        headers=headers,
        json={"name": "Bloqueado", "age": 40, "weight_kg": 70},
    )

    assert response.status_code == 403


def test_admin_can_access_user_management(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    create_test_user(email="admin@test.local", password="Admin@12345", role=UserRole.ADMIN)
    headers = auth_headers("admin@test.local", "Admin@12345")

    response = client.get("/api/users", headers=headers)

    assert response.status_code == 200
    assert response.json()[0]["email"] == "admin@test.local"


def test_doctor_can_check_prescription_and_audit_keeps_user(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    create_test_user(email="admin@test.local", password="Admin@12345", role=UserRole.ADMIN)
    create_test_user(email="medico@test.local", password="Medico@12345", role=UserRole.MEDICO)
    admin_headers = auth_headers("admin@test.local", "Admin@12345")
    doctor_headers = auth_headers("medico@test.local", "Medico@12345")

    patient = client.post(
        "/api/patients",
        headers=admin_headers,
        json={"name": "Paciente", "age": 35, "weight_kg": 70},
    ).json()
    medication = client.post(
        "/api/medications",
        headers=admin_headers,
        json={
            "brand_name": "Seguro",
            "active_ingredient": "seguridina",
            "therapeutic_class": "teste",
            "max_daily_dose_mg": 1000,
            "allowed_routes": ["oral"],
            "contraindications": [],
        },
    ).json()

    response = client.post(
        "/api/prescriptions/check",
        headers=doctor_headers,
        json={
            "patient_id": patient["id"],
            "medication_id": medication["id"],
            "dose_mg": 100,
            "frequency_per_day": 1,
            "route": "oral",
        },
    )

    assert response.status_code == 200

    audit = client.get("/api/audit", headers=admin_headers).json()["items"]
    prescription_events = [event for event in audit if event["action"] == "prescription.check"]
    assert prescription_events[0]["user_email"] == "medico@test.local"
