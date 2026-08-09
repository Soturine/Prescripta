from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import (
    InstitutionalClinicalProtocolModel,
    InstitutionalClinicalProtocolVersionModel,
    UserModel,
)
from app.domain.user import Capability, UserRole


def _create_patient_and_medication(
    client: TestClient,
    headers: dict[str, str],
) -> tuple[int, int]:
    patient = client.post(
        "/api/patients",
        headers=headers,
        json={"name": "Paciente Protocolo", "age": 42, "weight_kg": 70},
    )
    medication = client.post(
        "/api/medications",
        headers=headers,
        json={
            "brand_name": "Medicamento Protocolo",
            "active_ingredient": "substancia demo",
            "therapeutic_class": "classe demo",
            "max_daily_dose_mg": 2000,
            "usual_dose_low": 500,
            "usual_dose_high": 1000,
            "usual_dose_unit": "mg/day",
            "usual_range_scope": "daily",
            "allowed_routes": ["oral"],
            "contraindications": [],
        },
    )
    assert patient.status_code == 201, patient.text
    assert medication.status_code == 201, medication.text
    return patient.json()["id"], medication.json()["id"]


def _grant(
    client: TestClient,
    headers: dict[str, str],
    patient_id: int,
    user_id: int,
    capability: Capability,
) -> None:
    response = client.post(
        f"/api/access/patients/{patient_id}/grants",
        headers=headers,
        json={
            "user_id": user_id,
            "capability": capability.value,
            "purpose": "treatment",
            "reason": "Vinculo assistencial explicito para workflow profissional.",
        },
    )
    assert response.status_code == 201, response.text


def test_nursing_prescribing_is_bound_to_reviewed_protocol_scope(
    client: TestClient,
    create_test_user,
    auth_headers,
    db_session: Session,
) -> None:
    create_test_user(email="admin@protocol.local", role=UserRole.ADMIN)
    reviewer = create_test_user(
        email="reviewer@protocol.local",
        password="Reviewer@12345",
        role=UserRole.CLINICAL_SAFETY_OFFICER,
    )
    nurse = create_test_user(
        email="nurse@protocol.local",
        password="Nurse@12345",
        role=UserRole.ENFERMAGEM,
    )
    nurse.credential_type = "coren_demo"
    nurse.credential_region = "SP"
    nurse.credential_verification_status = "verified"
    nurse.credential_expires_at = datetime.now(UTC) + timedelta(days=365)
    db_session.commit()

    admin_headers = auth_headers("admin@protocol.local", "Admin@12345")
    reviewer_headers = auth_headers("reviewer@protocol.local", "Reviewer@12345")
    nurse_headers = auth_headers("nurse@protocol.local", "Nurse@12345")
    patient_id, medication_id = _create_patient_and_medication(client, admin_headers)
    _grant(client, admin_headers, patient_id, nurse.id, Capability.PATIENT_READ)
    _grant(client, admin_headers, patient_id, nurse.id, Capability.PRESCRIPTION_CHECK)

    protocol = client.post(
        "/api/clinical-protocols",
        headers=admin_headers,
        json={
            "code": "nursing.primary-care",
            "name": "Protocolo demonstrativo de enfermagem",
            "program": "atencao_primaria_demo",
        },
    )
    assert protocol.status_code == 201, protocol.text
    version = client.post(
        f"/api/clinical-protocols/{protocol.json()['id']}/versions",
        headers=admin_headers,
        json={
            "version": "2026.08-demo",
            "effective_from": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
            "effective_until": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
            "source_refs": ["institutional:protocol:nursing-primary-care:2026.08"],
            "clinical_context": {"jurisdiction": "BR", "demo_only": True},
            "eligible_professions": ["nursing"],
            "required_capability": Capability.NURSING_PROTOCOL_PRESCRIBE.value,
            "required_parameters": ["weight_kg"],
            "prescribing_scope": {
                "allowed_routes": ["oral"],
                "dose_min": 250,
                "dose_max": 500,
                "dose_unit": "mg",
                "frequency_min_per_day": 1,
                "frequency_max_per_day": 2,
                "max_duration_days": 7,
                "min_age_years": 18,
            },
            "medications": [{"medication_id": medication_id}],
            "conditions": [
                {
                    "terminology_system": "CID-10",
                    "terminology_version": "2026-demo",
                    "condition_code": "z00.0",
                    "label": "Condicao demonstrativa",
                }
            ],
            "credentials": [
                {
                    "credential_type": "coren_demo",
                    "credential_region": "SP",
                    "verification_required": True,
                    "unexpired_required": True,
                }
            ],
        },
    )
    assert version.status_code == 201, version.text
    reviewed = client.post(
        f"/api/clinical-protocols/versions/{version.json()['id']}/review",
        headers=reviewer_headers,
        json={
            "decision": "reviewed_demo",
            "note": "Revisao humana independente para uso demonstrativo.",
        },
    )
    assert reviewed.status_code == 200, reviewed.text

    base_request = {
        "patient_id": patient_id,
        "medication_id": medication_id,
        "dose_mg": 500,
        "frequency_per_day": 2,
        "route": "oral",
        "duration_days": 5,
        "condition_codes": ["Z00.0"],
    }
    missing_protocol = client.post(
        "/api/prescriptions/check",
        headers=nurse_headers,
        json=base_request,
    )
    assert missing_protocol.status_code == 200, missing_protocol.text
    assert (
        missing_protocol.json()["technical_details"]["prescribing_policy"]["status"]
        == "insufficient_protocol_context"
    )

    allowed = client.post(
        "/api/prescriptions/check",
        headers=nurse_headers,
        json={**base_request, "protocol_version_id": version.json()["id"]},
    )
    assert allowed.status_code == 200, allowed.text
    policy = allowed.json()["technical_details"]["prescribing_policy"]
    assert policy["status"] == "allowed"
    assert policy["capability_status"] == "granted"
    assert policy["relationship_status"] == "active"
    assert policy["protocol_context"]["applicable"] is True

    outside_scope = client.post(
        "/api/prescriptions/check",
        headers=nurse_headers,
        json={
            **base_request,
            "dose_mg": 750,
            "protocol_version_id": version.json()["id"],
        },
    )
    assert outside_scope.status_code == 200, outside_scope.text
    assert (
        outside_scope.json()["technical_details"]["prescribing_policy"]["status"]
        == "blocked_by_policy"
    )

    wrong_condition = client.post(
        "/api/prescriptions/check",
        headers=nurse_headers,
        json={
            **base_request,
            "condition_codes": ["X99"],
            "protocol_version_id": version.json()["id"],
        },
    )
    assert (
        wrong_condition.json()["technical_details"]["prescribing_policy"]["status"]
        == "blocked_by_policy"
    )

    version_row = db_session.get(
        InstitutionalClinicalProtocolVersionModel, version.json()["id"]
    )
    protocol_row = db_session.get(
        InstitutionalClinicalProtocolModel, protocol.json()["id"]
    )
    assert version_row is not None and protocol_row is not None

    version_row.requires_second_review = True
    db_session.commit()
    second_review = client.post(
        "/api/prescriptions/check",
        headers=nurse_headers,
        json={**base_request, "protocol_version_id": version_row.id},
    )
    assert (
        second_review.json()["technical_details"]["prescribing_policy"]["status"]
        == "requires_second_review"
    )
    version_row.requires_second_review = False

    version_row.source_refs = []
    db_session.commit()
    missing_source = client.post(
        "/api/prescriptions/check",
        headers=nurse_headers,
        json={**base_request, "protocol_version_id": version_row.id},
    )
    assert (
        missing_source.json()["technical_details"]["prescribing_policy"]["status"]
        == "insufficient_protocol_context"
    )
    version_row.source_refs = ["institutional:protocol:nursing-primary-care:2026.08"]

    protocol_row.status = "revoked"
    db_session.commit()
    revoked = client.post(
        "/api/prescriptions/check",
        headers=nurse_headers,
        json={**base_request, "protocol_version_id": version_row.id},
    )
    assert (
        revoked.json()["technical_details"]["prescribing_policy"]["status"]
        == "blocked_by_policy"
    )
    protocol_row.status = "active"

    nurse.credential_expires_at = datetime.now(UTC) - timedelta(days=1)
    db_session.commit()
    expired_credential = client.post(
        "/api/prescriptions/check",
        headers=nurse_headers,
        json={**base_request, "protocol_version_id": version_row.id},
    )
    assert (
        expired_credential.json()["technical_details"]["prescribing_policy"]["status"]
        == "insufficient_credentials"
    )

    stored_reviewer = db_session.get(UserModel, reviewer.id)
    assert stored_reviewer is not None
    assert stored_reviewer.id != protocol.json()["created_by_user_id"]


def test_pharmacy_intervention_reconciliation_and_formulation_lifecycles(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    admin = create_test_user(email="admin@pharmacy.local", role=UserRole.ADMIN)
    pharmacist = create_test_user(
        email="pharmacist@pharmacy.local",
        password="Pharmacist@12345",
        role=UserRole.FARMACEUTICO,
    )
    doctor = create_test_user(
        email="doctor@pharmacy.local",
        password="Doctor@12345",
        role=UserRole.MEDICO,
    )
    admin_headers = auth_headers("admin@pharmacy.local", "Admin@12345")
    pharmacist_headers = auth_headers("pharmacist@pharmacy.local", "Pharmacist@12345")
    doctor_headers = auth_headers("doctor@pharmacy.local", "Doctor@12345")
    patient_id, medication_id = _create_patient_and_medication(client, admin_headers)
    _grant(client, admin_headers, patient_id, pharmacist.id, Capability.PATIENT_READ)
    _grant(client, admin_headers, patient_id, doctor.id, Capability.PATIENT_READ)

    intervention_payload = {
        "patient_id": patient_id,
        "medication_id": medication_id,
        "intervention_type": "dose",
        "severity": "moderate",
        "priority": "priority",
        "problem": "Dose requer confirmacao farmacoterapeutica demonstrativa.",
        "recommendation": "Revisar dose com o prescritor e registrar a decisao.",
        "source_refs": ["institutional:pharmacy-demo:2026"],
        "dose_snapshot": {"amount": "500", "unit": "mg"},
        "idempotency_key": "pharmacy-intervention-demo-001",
    }
    created = client.post(
        "/api/pharmacy/interventions",
        headers=pharmacist_headers,
        json=intervention_payload,
    )
    replay = client.post(
        "/api/pharmacy/interventions",
        headers=pharmacist_headers,
        json=intervention_payload,
    )
    assert created.status_code == 201, created.text
    assert replay.status_code == 201, replay.text
    assert replay.json()["id"] == created.json()["id"]

    decision = client.post(
        f"/api/pharmacy/interventions/{created.json()['id']}/decision",
        headers=doctor_headers,
        json={
            "decision": "accepted",
            "reason": "Ajuste aceito apos revisao humana do contexto clinico.",
            "expected_version": 1,
        },
    )
    assert decision.status_code == 200, decision.text
    stale = client.post(
        f"/api/pharmacy/interventions/{created.json()['id']}/resolve",
        headers=pharmacist_headers,
        json={"resolution": "Ajuste documentado no workflow.", "expected_version": 1},
    )
    assert stale.status_code == 409
    resolved = client.post(
        f"/api/pharmacy/interventions/{created.json()['id']}/resolve",
        headers=pharmacist_headers,
        json={"resolution": "Ajuste documentado no workflow.", "expected_version": 2},
    )
    assert resolved.status_code == 200, resolved.text
    events = client.get(
        f"/api/pharmacy/interventions/{created.json()['id']}/events",
        headers=pharmacist_headers,
    )
    assert [item["event_type"] for item in events.json()] == [
        "created",
        "decision",
        "resolved",
    ]

    reconciliation = client.post(
        "/api/pharmacy/reconciliations",
        headers=pharmacist_headers,
        json={
            "patient_id": patient_id,
            "source_refs": ["patient-report:demo"],
            "idempotency_key": "medication-reconciliation-demo-001",
            "items": [
                {
                    "medication_id": medication_id,
                    "medication_name": "Medicamento Protocolo",
                    "source_ref": "patient-report:demo:item-1",
                    "discrepancy": "Frequencia nao confirmada.",
                    "formulation": "comprimido",
                    "concentration": "500 mg",
                }
            ],
        },
    )
    assert reconciliation.status_code == 201, reconciliation.text
    item = reconciliation.json()["items"][0]
    decided_item = client.post(
        f"/api/pharmacy/reconciliation-items/{item['id']}/decision",
        headers=pharmacist_headers,
        json={
            "status": "confirmed",
            "action": "maintain",
            "justification": "Paciente confirmou o esquema durante revisao humana.",
            "expected_version": 1,
        },
    )
    assert decided_item.status_code == 200, decided_item.text
    detail = client.get(
        f"/api/pharmacy/reconciliations/{reconciliation.json()['id']}",
        headers=pharmacist_headers,
    )
    assert detail.json()["status"] == "completed"

    formulation = client.post(
        "/api/pharmacy/formulation-reviews",
        headers=pharmacist_headers,
        json={
            "reconciliation_item_id": item["id"],
            "formulation": "comprimido",
            "concentration": "500 mg",
            "dose": {
                "amount": 500,
                "amount_unit": "mg",
                "administration_kind": "intermittent",
                "frequency_per_day": 2,
                "route": "oral",
            },
        },
    )
    assert formulation.status_code == 201, formulation.text
    assert formulation.json()["result"]["requires_human_review"] is True
    assert formulation.json()["institution_id"] == admin.institution_id
