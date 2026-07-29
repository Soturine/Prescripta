from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import (
    AuditEventModel,
    BreakGlassAccessModel,
    PatientAccessGrantModel,
    PatientModel,
)
from app.database.session import finish_denied_request
from app.domain.user import Capability, Profession, UserRole, capability_values
from app.services.capability_policy import (
    InvalidProfessionalProfile,
    allowed_capabilities,
    validate_professional_profile,
)
from app.services.clinical_access_service import ClinicalAccessError, ClinicalAccessService
from app.services.object_authorization import ObjectAuthorizationService


def _patient(client: TestClient, headers: dict[str, str], name: str = "Paciente Demo") -> int:
    response = client.post(
        "/api/patients",
        headers=headers,
        json={"name": name, "age": 42, "weight_kg": 70},
    )
    assert response.status_code == 201, response.text
    return int(response.json()["id"])


def _grant(
    client: TestClient,
    headers: dict[str, str],
    patient_id: int,
    user_id: int,
    capability: str,
    *,
    purpose: str = "treatment",
) -> dict:
    response = client.post(
        f"/api/access/patients/{patient_id}/grants",
        headers=headers,
        json={
            "user_id": user_id,
            "capability": capability,
            "purpose": purpose,
            "reason": "Vinculo assistencial explicito para teste adversarial.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_same_tenant_requires_active_grant_and_scopes_listings(
    client: TestClient,
    create_test_user,
    auth_headers,
    db_session: Session,
) -> None:
    create_test_user(email="admin@access.local", role=UserRole.ADMIN)
    doctor = create_test_user(
        email="doctor@access.local", password="Doctor@12345", role=UserRole.MEDICO
    )
    admin_headers = auth_headers("admin@access.local", "Admin@12345")
    doctor_headers = auth_headers("doctor@access.local", "Doctor@12345")
    patient_id = _patient(client, admin_headers)

    assert client.get("/api/patients", headers=doctor_headers).json() == []
    assert client.get(f"/api/patients/{patient_id}", headers=doctor_headers).status_code == 404

    grant = _grant(
        client,
        admin_headers,
        patient_id,
        doctor.id,
        Capability.PATIENT_READ.value,
    )
    assert client.get(f"/api/patients/{patient_id}", headers=doctor_headers).status_code == 200
    assert [item["id"] for item in client.get("/api/patients", headers=doctor_headers).json()] == [
        patient_id
    ]

    stored = db_session.get(PatientAccessGrantModel, grant["id"])
    assert stored is not None
    stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()
    assert client.get(f"/api/patients/{patient_id}", headers=doctor_headers).status_code == 404

    stored.expires_at = datetime.now(UTC) + timedelta(hours=1)
    db_session.commit()
    revoked = client.post(
        f"/api/access/grants/{grant['id']}/revoke",
        headers=admin_headers,
        json={"reason": "Atendimento encerrado e acesso removido imediatamente."},
    )
    assert revoked.status_code == 200
    assert client.get(f"/api/patients/{patient_id}", headers=doctor_headers).status_code == 404

    db_session.expire_all()
    denials = db_session.query(AuditEventModel).filter_by(
        action="authorization.denied"
    ).all()
    assert denials
    assert all(event.user_name is None and event.user_email is None for event in denials)


def test_care_team_and_episode_are_exact_revocable_relationships(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    create_test_user(email="admin@team.local", role=UserRole.ADMIN)
    doctor = create_test_user(
        email="doctor@team.local", password="Doctor@12345", role=UserRole.MEDICO
    )
    admin_headers = auth_headers("admin@team.local", "Admin@12345")
    doctor_headers = auth_headers("doctor@team.local", "Doctor@12345")
    patient_id = _patient(client, admin_headers, "Paciente Equipe")

    membership = client.post(
        f"/api/access/patients/{patient_id}/care-team",
        headers=admin_headers,
        json={
            "user_id": doctor.id,
            "team_code": "cardio-demo",
            "care_role": "medico_assistente",
            "capabilities": [Capability.PATIENT_READ.value],
            "purpose": "treatment",
        },
    )
    assert membership.status_code == 201, membership.text
    assert client.get(f"/api/patients/{patient_id}", headers=doctor_headers).status_code == 200
    assert len(
        client.get(
            f"/api/access/patients/{patient_id}/care-team", headers=admin_headers
        ).json()
    ) == 1
    assert client.post(
        f"/api/access/care-team/{membership.json()['id']}/revoke",
        headers=admin_headers,
        json={"reason": "Profissional removido da equipe assistencial ativa."},
    ).status_code == 200
    assert client.get(f"/api/patients/{patient_id}", headers=doctor_headers).status_code == 404

    episode = client.post(
        f"/api/access/patients/{patient_id}/care-episodes",
        headers=admin_headers,
        json={
            "user_id": doctor.id,
            "episode_id": "episode-demo-001",
            "capabilities": [Capability.PATIENT_READ.value],
            "purpose": "treatment",
        },
    )
    assert episode.status_code == 201, episode.text
    assert client.get(f"/api/patients/{patient_id}", headers=doctor_headers).status_code == 200
    assert client.post(
        f"/api/access/care-episodes/{episode.json()['id']}/revoke",
        headers=admin_headers,
        json={"reason": "Episodio assistencial encerrado com revogacao imediata."},
    ).status_code == 200
    assert client.get(f"/api/patients/{patient_id}", headers=doctor_headers).status_code == 404


def test_grants_do_not_amplify_capability_or_cross_tenant(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    create_test_user(email="admin@scope.local", role=UserRole.ADMIN, institution_id="org-a")
    pharmacist = create_test_user(
        email="pharma@scope.local",
        password="Pharma@12345",
        role=UserRole.FARMACEUTICO,
        institution_id="org-a",
    )
    outsider = create_test_user(
        email="outside@scope.local",
        password="Outside@12345",
        role=UserRole.MEDICO,
        institution_id="org-b",
    )
    headers = auth_headers("admin@scope.local", "Admin@12345")
    patient_id = _patient(client, headers, "Paciente Escopo")

    amplification = client.post(
        f"/api/access/patients/{patient_id}/grants",
        headers=headers,
        json={
            "user_id": pharmacist.id,
            "capability": Capability.PATIENT_WRITE.value,
            "purpose": "treatment",
            "reason": "Tentativa deliberada de ampliar capacidade profissional.",
        },
    )
    cross_tenant = client.post(
        f"/api/access/patients/{patient_id}/grants",
        headers=headers,
        json={
            "user_id": outsider.id,
            "capability": Capability.PATIENT_READ.value,
            "purpose": "treatment",
            "reason": "Tentativa deliberada de cruzar a barreira institucional.",
        },
    )
    assert amplification.status_code == 422
    assert cross_tenant.status_code == 422


def test_break_glass_is_short_idempotent_audited_and_independently_reviewed(
    client: TestClient,
    create_test_user,
    auth_headers,
    db_session: Session,
) -> None:
    create_test_user(email="admin@break.local", role=UserRole.ADMIN)
    doctor = create_test_user(
        email="doctor@break.local", password="Doctor@12345", role=UserRole.MEDICO
    )
    reviewer = create_test_user(
        email="safety@break.local",
        password="Safety@12345",
        role=UserRole.CLINICAL_SAFETY_OFFICER,
    )
    admin_headers = auth_headers("admin@break.local", "Admin@12345")
    doctor_headers = auth_headers("doctor@break.local", "Doctor@12345")
    reviewer_headers = auth_headers("safety@break.local", "Safety@12345")
    patient_id = _patient(client, admin_headers, "Paciente Emergencia")
    request = {
        "capability": Capability.PATIENT_READ.value,
        "purpose": "treatment",
        "reason": "Emergencia demonstrativa exige consulta temporaria imediata.",
        "duration_minutes": 15,
        "idempotency_key": "break-glass-demo-001",
    }

    first = client.post(
        f"/api/access/patients/{patient_id}/break-glass",
        headers=doctor_headers,
        json=request,
    )
    second = client.post(
        f"/api/access/patients/{patient_id}/break-glass",
        headers=doctor_headers,
        json=request,
    )
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert client.get(f"/api/patients/{patient_id}", headers=doctor_headers).status_code == 200

    db_session.expire_all()
    access = db_session.get(BreakGlassAccessModel, first.json()["id"])
    assert access is not None
    assert access.objects_accessed[0]["id"] == str(patient_id)
    with pytest.raises(ClinicalAccessError, match="independente"):
        ClinicalAccessService(db_session).review_break_glass(
            access.id,
            type("Review", (), {"decision": "approved", "notes": "Self review blocked"})(),
            doctor,
        )

    ended = client.post(
        f"/api/access/break-glass/{access.id}/end", headers=doctor_headers
    )
    assert ended.status_code == 200
    assert client.get(f"/api/patients/{patient_id}", headers=doctor_headers).status_code == 404
    pending = client.get(
        "/api/access/break-glass",
        headers=reviewer_headers,
        params={"review_status": "pending_review"},
    )
    assert pending.status_code == 200
    assert any(item["id"] == access.id for item in pending.json())
    reviewed = client.post(
        f"/api/access/break-glass/{access.id}/review",
        headers=reviewer_headers,
        json={"decision": "approved", "notes": "Revisao independente demonstrativa."},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == "approved"
    assert reviewer.id != doctor.id


def test_psychological_notes_are_segmented_and_minimized(
    client: TestClient,
    create_test_user,
    auth_headers,
    db_session: Session,
) -> None:
    create_test_user(email="admin@psych.local", role=UserRole.ADMIN)
    psychologist = create_test_user(
        email="psych@psych.local", password="Psych@12345", role=UserRole.PSICOLOGO
    )
    doctor = create_test_user(
        email="doctor@psych.local", password="Doctor@12345", role=UserRole.MEDICO
    )
    psychiatrist = create_test_user(
        email="psychiatrist@psych.local",
        password="Doctor@12345",
        role=UserRole.MEDICO,
    )
    psychiatrist.specialty_codes = ["psychiatry"]
    psychiatrist.capabilities = sorted(
        set(psychiatrist.capabilities)
        | {Capability.PATIENT_SENSITIVE_PSYCHOLOGY_READ.value}
    )
    db_session.commit()
    admin_headers = auth_headers("admin@psych.local", "Admin@12345")
    psych_headers = auth_headers("psych@psych.local", "Psych@12345")
    doctor_headers = auth_headers("doctor@psych.local", "Doctor@12345")
    psychiatrist_headers = auth_headers("psychiatrist@psych.local", "Doctor@12345")
    patient_id = _patient(client, admin_headers, "Paciente Psicologia")

    for user, capability in (
        (psychologist, Capability.PSYCHOLOGY_CONTEXT_WRITE.value),
        (psychologist, Capability.PATIENT_SENSITIVE_PSYCHOLOGY_READ.value),
        (doctor, Capability.PATIENT_READ.value),
        (psychiatrist, Capability.PATIENT_SENSITIVE_PSYCHOLOGY_READ.value),
    ):
        _grant(client, admin_headers, patient_id, user.id, capability)

    updated = client.put(
        f"/api/patients/{patient_id}/psychological-context",
        headers=psych_headers,
        json={
            "purpose": "treatment",
            "medication_safety_factors": ["adesao_requer_acompanhamento"],
            "confidential_notes": "Nota psicologica confidencial ficticia.",
            "consent_status": "recorded",
            "policy_reference": "demo-policy-psych-v1",
        },
    )
    assert updated.status_code == 200, updated.text
    assert client.get(
        f"/api/patients/{patient_id}/psychological-context", headers=doctor_headers
    ).status_code == 403
    patient = client.get(f"/api/patients/{patient_id}", headers=doctor_headers)
    assert patient.status_code == 200
    assert patient.json()["mental_health_factors"] == ["adesao_requer_acompanhamento"]
    assert "Nota psicologica" not in patient.text
    sensitive = client.get(
        f"/api/patients/{patient_id}/psychological-context",
        headers=psychiatrist_headers,
    )
    assert sensitive.status_code == 200
    assert sensitive.json()["confidential_notes"].startswith("Nota psicologica")


def test_professional_templates_and_nursing_policy_are_least_privilege(
    client: TestClient,
    create_test_user,
    auth_headers,
    db_session: Session,
) -> None:
    assert Capability.PATIENT_READ.value not in capability_values(
        Profession.ADMINISTRATION
    )
    assert Capability.PATIENT_SENSITIVE_PSYCHOLOGY_READ.value in allowed_capabilities(
        Profession.MEDICINE, specialty_codes=["psychiatry"]
    )
    with pytest.raises(InvalidProfessionalProfile):
        validate_professional_profile(
            role=UserRole.ADMIN,
            profession=Profession.ADMINISTRATION,
            capabilities=[Capability.PATIENT_READ.value],
        )

    nurse = create_test_user(
        email="nurse@policy.local", password="Nurse@12345", role=UserRole.ENFERMAGEM
    )
    headers = auth_headers("nurse@policy.local", "Nurse@12345")
    payload = {
        "context": {
            "suspected_trigger": "medicamento ficticio",
            "weight_kg": 70,
            "age_years": 35,
            "respiratory_symptoms": True,
        },
        "selected_step_orders": [1],
        "notes": "Cenario demonstrativo sem dado real.",
    }
    assert client.post(
        "/api/protocols/anafilaxia/run", headers=headers, json=payload
    ).status_code == 403

    nurse.credential_type = "COREN_DEMO"
    nurse.credential_expires_at = datetime.now(UTC) + timedelta(days=30)
    nurse.institutional_policy = {
        "nursing_prescribing_enabled": True,
        "nursing_protocols": {
            "anafilaxia": {
                "source": "demo_policy",
                "version": "2026.07-demo",
                "allowed_conditions": ["anafilaxia_demo"],
                "limits": {"max_selected_steps": 4},
            }
        },
    }
    db_session.commit()
    allowed = client.post(
        "/api/protocols/anafilaxia/run", headers=headers, json=payload
    )
    assert allowed.status_code == 200, allowed.text


def test_denial_audit_never_commits_pending_clinical_work_and_is_rate_limited(
    create_test_user,
    db_session: Session,
) -> None:
    user = create_test_user(email="audit-uow@local.test", role=UserRole.MEDICO)
    pending_patient = PatientModel(
        institution_id="demo",
        name="Nao deve persistir",
        age=30,
        weight_kg=70,
    )
    db_session.add(pending_patient)
    ObjectAuthorizationService(db_session).record_denied(
        user, resource_type="patient", resource_id="999"
    )
    assert finish_denied_request(db_session) is False
    assert db_session.query(PatientModel).filter_by(name="Nao deve persistir").count() == 0
    assert db_session.query(AuditEventModel).filter_by(resource_id="999").count() == 0

    for resource_id in range(30):
        ObjectAuthorizationService(db_session).record_denied(
            user,
            resource_type="patient",
            resource_id=f"rate-{resource_id}",
        )
    db_session.commit()
    assert db_session.query(AuditEventModel).filter(
        AuditEventModel.resource_id.like("rate-%")
    ).count() == 20
