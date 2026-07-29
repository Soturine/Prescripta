import pytest
from fastapi.testclient import TestClient

from app.database.models import (
    AuditEventModel,
    MedicationModel,
    PatientModel,
    PrescriptionAuditModel,
)
from app.domain.user import UserRole
from app.reports.evidence_bundle import ReportEvidenceBundleBuilder
from app.services.audit_service import AuditService
from app.services.canonical_json import CANONICAL_HASH_ALGORITHM, canonical_sha256


def _create_decision(client, create_test_user, auth_headers):
    create_test_user(email="snapshot@test.local", password="Admin@12345", role=UserRole.ADMIN)
    headers = auth_headers("snapshot@test.local", "Admin@12345")
    patient = client.post(
        "/api/patients",
        headers=headers,
        json={
            "name": "Paciente Snapshot",
            "age": 44,
            "weight_kg": 70,
            "allergies": [],
            "comorbidities": [],
            "current_medications": [],
        },
    ).json()
    medication = client.post(
        "/api/medications",
        headers=headers,
        json={
            "brand_name": "Snapshot Demo",
            "active_ingredient": "substância snapshot",
            "therapeutic_class": "teste",
            "max_daily_dose_mg": 100,
            "allowed_routes": ["oral"],
            "contraindications": [],
        },
    ).json()
    checked = client.post(
        "/api/prescriptions/check",
        headers=headers,
        json={
            "patient_id": patient["id"],
            "medication_id": medication["id"],
            "dose_mg": 10,
            "frequency_per_day": 1,
            "route": "oral",
        },
    )
    assert checked.status_code == 200
    return checked.json()["audit_id"], patient["id"], medication["id"]


def test_report_uses_immutable_snapshot_after_live_records_change(
    client: TestClient, create_test_user, auth_headers, db_session
):
    audit_id, patient_id, medication_id = _create_decision(
        client, create_test_user, auth_headers
    )
    audit = db_session.get(PrescriptionAuditModel, audit_id)
    first = ReportEvidenceBundleBuilder(db_session).prescription_bundle(audit).stable_payload()

    patient = db_session.get(PatientModel, patient_id)
    medication = db_session.get(MedicationModel, medication_id)
    patient.weight_kg = 199
    medication.max_daily_dose_mg = 1
    medication.brand_name = "Nome alterado depois"
    db_session.commit()

    db_session.refresh(audit)
    second = ReportEvidenceBundleBuilder(db_session).prescription_bundle(audit).stable_payload()
    assert first == second
    assert audit.hash_algorithm == CANONICAL_HASH_ALGORITHM
    assert audit.snapshot_hash == canonical_sha256(audit.clinical_snapshot)
    assert second["metadata"]["clinical_data_source"] == "immutable_snapshot_only"


def test_snapshot_cannot_be_replaced_after_commit(
    client: TestClient, create_test_user, auth_headers, db_session
):
    audit_id, _, _ = _create_decision(client, create_test_user, auth_headers)
    audit = db_session.get(PrescriptionAuditModel, audit_id)
    audit.clinical_snapshot = {"tampered": True}
    with pytest.raises(ValueError, match="imutáveis"):
        db_session.commit()
    db_session.rollback()


def test_prescription_transaction_rolls_back_audit_and_events_on_failure(
    client: TestClient, create_test_user, auth_headers, db_session, monkeypatch
):
    create_test_user(email="uow@test.local", password="Admin@12345", role=UserRole.ADMIN)
    headers = auth_headers("uow@test.local", "Admin@12345")
    patient = client.post(
        "/api/patients",
        headers=headers,
        json={
            "name": "Paciente UoW",
            "age": 40,
            "weight_kg": 70,
            "allergies": [],
            "comorbidities": [],
            "current_medications": [],
        },
    ).json()
    medication = client.post(
        "/api/medications",
        headers=headers,
        json={
            "brand_name": "UoW Demo",
            "active_ingredient": "uow demo",
            "therapeutic_class": "teste",
            "max_daily_dose_mg": 100,
            "allowed_routes": ["oral"],
            "contraindications": [],
        },
    ).json()

    def fail_event(*_args, **_kwargs):
        raise RuntimeError("falha de auditoria simulada")

    monkeypatch.setattr(AuditService, "record_action", fail_event)
    with pytest.raises(RuntimeError, match="falha de auditoria"):
        client.post(
            "/api/prescriptions/check",
            headers=headers,
            json={
                "patient_id": patient["id"],
                "medication_id": medication["id"],
                "dose_mg": 10,
                "frequency_per_day": 1,
                "route": "oral",
            },
        )
    assert db_session.query(PrescriptionAuditModel).count() == 0
    assert db_session.query(AuditEventModel).filter(
        AuditEventModel.action == "prescription.check"
    ).count() == 0
