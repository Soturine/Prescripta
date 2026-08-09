from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import AIInteractionModel
from app.domain.user import Capability, UserRole
from app.schemas.ai_task_schema import AIRequestSchema
from app.services.ai_settings import AISettingsService
from app.services.ai_task_router import AITaskError, AITaskRouter
from app.services.cohort_dsl import CohortDSLValidationError, CohortDSLValidator


def _ai_request(**overrides) -> AIRequestSchema:
    payload = {
        "task_type": "evidence_summary",
        "data_classification": "synthetic",
        "source_ids": [],
        "preferred_provider": "fallback",
        "allowed_providers": ["fallback"],
        "purpose": "adversarial_output_validation",
        "input": {},
    }
    payload.update(overrides)
    return AIRequestSchema.model_validate(payload)


def test_ai_provider_policy_is_fail_closed() -> None:
    with pytest.raises(AITaskError, match="não reconhecido"):
        AITaskRouter._provider_for(
            _ai_request(allowed_providers=["shadow-provider"]),
            "fallback",
        )
    with pytest.raises(AITaskError, match="preferido inválido"):
        AITaskRouter._provider_for(
            _ai_request(preferred_provider="unknown"),
            "fallback",
        )
    with pytest.raises(AITaskError, match="preferido negado"):
        AITaskRouter._provider_for(
            _ai_request(preferred_provider="openai", allowed_providers=["fallback"]),
            "openai",
        )
    with pytest.raises(AITaskError, match="fallback está desabilitado"):
        AITaskRouter._provider_for(
            _ai_request(preferred_provider=None, allowed_providers=["ollama"]),
            "openai",
        )
    with pytest.raises(AITaskError, match="provider local"):
        AITaskRouter._provider_for(
            _ai_request(
                data_classification="restricted",
                preferred_provider=None,
                allowed_providers=["openai"],
            ),
            "openai",
        )


def test_ai_request_and_output_contracts_are_strict(
    db_session: Session,
    create_test_user,
) -> None:
    actor = create_test_user(email="ai-contract@v089.local", role=UserRole.PESQUISADOR)
    router = AITaskRouter(db_session)
    request = _ai_request()

    with pytest.raises(ValidationError, match="extra_forbidden"):
        AIRequestSchema.model_validate({**request.model_dump(), "unexpected": True})
    with pytest.raises(AITaskError, match="schema estruturado"):
        router._validate_output(request, "not-json", actor)
    with pytest.raises(AITaskError, match="omitiu campos"):
        router._validate_output(request, {"status": "needs_review"}, actor)
    with pytest.raises(AITaskError, match="não suportados"):
        router._validate_output(
            request,
            {"claims": [], "status": "needs_review", "source_ids": [], "decision": "allow"},
            actor,
        )
    with pytest.raises(AITaskError, match="Versão de schema"):
        router._validate_output(
            _ai_request(schema_version="v2"),
            {"claims": [], "status": "needs_review", "source_ids": []},
            actor,
        )
    with pytest.raises(AITaskError, match="alterou as fontes"):
        router._validate_output(
            _ai_request(source_ids=["source-a"]),
            {"claims": [], "status": "needs_review", "source_ids": []},
            actor,
        )


def test_ai_timeout_and_malformed_json_use_audited_fallback(
    monkeypatch: pytest.MonkeyPatch,
    db_session: Session,
    create_test_user,
) -> None:
    actor = create_test_user(email="ai-fallback@v089.local", role=UserRole.PESQUISADOR)
    config = SimpleNamespace(provider="openai", model="gpt-demo")
    monkeypatch.setattr(AISettingsService, "runtime_config", lambda _self: config)

    for error in (TimeoutError("provider timeout"), json.JSONDecodeError("bad", "{", 0)):
        monkeypatch.setattr(
            AISettingsService,
            "complete_json",
            lambda _self, _error=error, **_kwargs: (_ for _ in ()).throw(_error),
        )
        interaction = AITaskRouter(db_session).execute(
            _ai_request(
                preferred_provider="openai",
                allowed_providers=["openai", "fallback"],
            ),
            actor,
        )
        assert interaction.provider == "fallback"
        assert interaction.fallback_used is True
        assert interaction.sanitized_error_class == type(error).__name__
        assert interaction.output_payload["status"] == "insufficient_source_support"

    assert db_session.scalar(select(func.count(AIInteractionModel.id))) == 2


def test_ai_local_only_failure_does_not_fall_back_to_external(
    monkeypatch: pytest.MonkeyPatch,
    db_session: Session,
    create_test_user,
) -> None:
    actor = create_test_user(email="ai-local@v089.local", role=UserRole.PESQUISADOR)
    config = SimpleNamespace(provider="ollama", model="local-demo")
    monkeypatch.setattr(AISettingsService, "runtime_config", lambda _self: config)
    monkeypatch.setattr(
        AISettingsService,
        "complete_json",
        lambda _self, **_kwargs: (_ for _ in ()).throw(TimeoutError("offline")),
    )
    with pytest.raises(AITaskError, match="provider local autorizado indisponível"):
        AITaskRouter(db_session).execute(
            _ai_request(
                data_classification="sensitive",
                preferred_provider="ollama",
                allowed_providers=["ollama"],
            ),
            actor,
        )
    assert db_session.scalar(select(func.count(AIInteractionModel.id))) == 0


def test_ai_oversized_context_and_empty_source_support(
    db_session: Session,
    create_test_user,
) -> None:
    actor = create_test_user(email="ai-context@v089.local", role=UserRole.PESQUISADOR)
    with pytest.raises(AITaskError, match="excede"):
        AITaskRouter(db_session).execute(
            _ai_request(input={"text": "x" * 200}, max_context=20),
            actor,
        )
    interaction = AITaskRouter(db_session).execute(_ai_request(), actor)
    assert interaction.source_ids == []
    assert interaction.output_payload == {
        "claims": [],
        "status": "insufficient_source_support",
        "source_ids": [],
    }


@pytest.mark.parametrize(
    ("definition", "message"),
    [
        (
            {"all": [{"criterion": "age", "operator": "gte", "value": 18, "sql": "DROP"}]},
            "Campos não permitidos",
        ),
        (
            {"all": [{"all": [{"criterion": "age", "operator": "gte", "value": 18}]}]},
            "Campos não permitidos",
        ),
        (
            {
                "all": [
                    {
                        "criterion": "age",
                        "operator": "gte",
                        "value": 18,
                        "window": {"before_index_days": -1},
                    }
                ]
            },
            "Window deve usar dias",
        ),
        (
            {"all": [{"criterion": "date", "operator": "after", "value": "2026-02-30"}]},
            "Data impossível",
        ),
        (
            {
                "all": [
                    {
                        "criterion": "demographic",
                        "operator": "eq",
                        "field": "tenant_id",
                        "value": "demo",
                    }
                ]
            },
            "Campo demográfico",
        ),
        ({"all": [{"criterion": "age", "operator": "gte", "value": 18}] * 31}, "limite de 30"),
    ],
)
def test_cohort_dsl_rejects_adversarial_shapes(
    db_session: Session,
    definition: dict,
    message: str,
) -> None:
    with pytest.raises(CohortDSLValidationError, match=message):
        CohortDSLValidator(db_session, "demo").validate(definition)


def _grant_patient(
    client: TestClient,
    admin_headers: dict[str, str],
    patient_id: int,
    user_id: int,
) -> int:
    response = client.post(
        f"/api/access/patients/{patient_id}/grants",
        headers=admin_headers,
        json={
            "user_id": user_id,
            "capability": Capability.PATIENT_READ.value,
            "purpose": "treatment",
            "reason": "Vínculo sintético para teste adversarial v0.8.9.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_pharmacy_queue_reapplies_patient_scope_and_idempotency(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    admin = create_test_user(email="admin-pharmacy@v089.local", role=UserRole.ADMIN)
    pharmacist = create_test_user(
        email="pharmacy@v089.local",
        password="Pharmacy@12345",
        role=UserRole.FARMACEUTICO,
    )
    doctor = create_test_user(
        email="doctor-pharmacy@v089.local",
        password="Doctor@12345",
        role=UserRole.MEDICO,
    )
    outside = create_test_user(
        email="outside-pharmacy@v089.local",
        password="Outside@12345",
        role=UserRole.FARMACEUTICO,
        institution_id="outside-v089",
    )
    admin_headers = auth_headers(admin.email, "Admin@12345")
    pharmacist_headers = auth_headers(pharmacist.email, "Pharmacy@12345")
    doctor_headers = auth_headers(doctor.email, "Doctor@12345")
    outside_headers = auth_headers(outside.email, "Outside@12345")
    patient = client.post(
        "/api/patients",
        headers=admin_headers,
        json={"name": "Paciente Farmácia v0.8.9", "age": 55, "weight_kg": 72},
    )
    assert patient.status_code == 201
    patient_id = patient.json()["id"]
    grant_id = _grant_patient(client, admin_headers, patient_id, pharmacist.id)

    payload = {
        "patient_id": patient_id,
        "intervention_type": "dose",
        "severity": "moderate",
        "priority": "priority",
        "problem": "Dose sintética exige revisão farmacêutica humana.",
        "recommendation": "Revisar o contexto com o prescritor responsável.",
        "source_refs": ["fixture:pharmacy:v089"],
        "idempotency_key": "test-test-test",
    }
    unauthorized = client.post(
        "/api/pharmacy/interventions", headers=doctor_headers, json=payload
    )
    assert unauthorized.status_code == 403
    assert client.post(
        "/api/pharmacy/interventions",
        headers=pharmacist_headers,
        json={**payload, "source_refs": []},
    ).status_code == 422
    created = client.post("/api/pharmacy/interventions", headers=pharmacist_headers, json=payload)
    assert created.status_code == 201, created.text
    intervention_id = created.json()["id"]
    conflict = client.post(
        "/api/pharmacy/interventions",
        headers=pharmacist_headers,
        json={**payload, "problem": "Conteúdo diferente para a mesma chave sintética."},
    )
    assert conflict.status_code == 409
    assert client.get(
        f"/api/pharmacy/interventions/{intervention_id}/events",
        headers=outside_headers,
    ).status_code == 422

    revoked = client.post(
        f"/api/access/grants/{grant_id}/revoke",
        headers=admin_headers,
        json={"reason": "Encerramento sintético do vínculo para teste."},
    )
    assert revoked.status_code == 200, revoked.text
    queue = client.get("/api/pharmacy/interventions", headers=pharmacist_headers)
    assert queue.status_code == 200
    assert queue.json() == []
    assert client.get(
        f"/api/pharmacy/interventions/{intervention_id}/events",
        headers=pharmacist_headers,
    ).status_code == 422
