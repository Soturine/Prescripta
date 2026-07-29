from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.database.models import AuditEventModel
from app.domain.user import UserRole
from app.repositories.audit_repository import AuditRepository
from app.schemas.patient_schema import PatientCreate, age_on_date


def test_birth_date_is_authoritative_and_divergent_age_is_rejected() -> None:
    today = date.today()
    birth_date = date(today.year - 40, today.month, today.day)

    assert age_on_date(birth_date) == 40
    PatientCreate(name="Paciente", birth_date=birth_date, age=40, weight_kg=70)
    with pytest.raises(ValidationError, match="Idade divergente"):
        PatientCreate(name="Paciente", birth_date=birth_date, age=39, weight_kg=70)


def test_patient_and_medication_lists_are_server_paginated(
    client: TestClient, create_test_user, auth_headers
) -> None:
    create_test_user(role=UserRole.ADMIN)
    headers = auth_headers("admin@test.local", "Admin@12345")
    for index in range(3):
        patient = client.post(
            "/api/patients",
            headers=headers,
            json={"name": f"Paciente {index}", "age": 30 + index, "weight_kg": 70},
        )
        medication = client.post(
            "/api/medications",
            headers=headers,
            json={
                "brand_name": f"Medicamento {index}",
                "active_ingredient": f"substancia {index}",
                "therapeutic_class": "demo",
                "max_daily_dose_mg": 100,
                "allowed_routes": ["oral"],
                "contraindications": [],
            },
        )
        assert patient.status_code == 201
        assert medication.status_code == 201

    patients_page = client.get(
        "/api/patients", headers=headers, params={"page": 2, "page_size": 2}
    )
    medications_page = client.get(
        "/api/medications", headers=headers, params={"page": 2, "page_size": 2}
    )

    assert len(patients_page.json()) == 1
    assert len(medications_page.json()) == 1


def test_birth_date_removes_redundant_stored_age(
    client: TestClient, create_test_user, auth_headers
) -> None:
    create_test_user(role=UserRole.ADMIN)
    headers = auth_headers("admin@test.local", "Admin@12345")
    today = date.today()
    birth_date = date(today.year - 35, today.month, today.day)

    created = client.post(
        "/api/patients",
        headers=headers,
        json={
            "name": "Paciente Data Autoritativa",
            "birth_date": birth_date.isoformat(),
            "age": 35,
            "weight_kg": 70,
        },
    )
    divergent_update = client.put(
        f"/api/patients/{created.json()['id']}",
        headers=headers,
        json={"age": 34},
    )

    assert created.status_code == 201
    assert created.json()["age"] is None
    assert divergent_update.status_code == 422


def test_audit_bulk_read_declares_truncation_manifest(db_session) -> None:
    db_session.add_all(
        [
            AuditEventModel(
                action="test.event",
                resource_type="test",
                resource_id=str(index),
                details={},
            )
            for index in range(7)
        ]
    )
    db_session.commit()

    events, manifest = AuditRepository(db_session).list_all_filtered(
        batch_size=2, max_items=5
    )

    assert len(events) == 5
    assert manifest == {
        "total_available": 7,
        "returned": 5,
        "truncated": True,
        "maximum_export_items": 5,
    }
