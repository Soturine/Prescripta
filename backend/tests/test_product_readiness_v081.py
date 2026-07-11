from __future__ import annotations

from urllib.parse import quote

import httpx
import pytest
from fastapi.testclient import TestClient

from app.domain.user import UserRole
from app.integrations.services.clinical_deduplication_service import (
    ClinicalDeduplicationService,
)
from app.services.ai_settings import _MEMORY_CREDENTIALS, _PROVIDER_FAILURES


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://provider.test")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("provider error", request=request, response=response)


def _headers(client: TestClient, create_test_user, auth_headers) -> dict[str, str]:
    _MEMORY_CREDENTIALS.clear()
    _PROVIDER_FAILURES.clear()
    create_test_user(email="admin@v081.local", password="Admin@12345", role=UserRole.ADMIN)
    return auth_headers("admin@v081.local", "Admin@12345")


def _configure_openai(client: TestClient, headers: dict[str, str]) -> None:
    client.post(
        "/api/settings/ai/credentials",
        headers=headers,
        json={"provider": "openai", "api_key": "sk-test-secret-1234", "persist": True},
    )
    client.post(
        "/api/settings/ai/select-model",
        headers=headers,
        json={
            "provider": "openai",
            "selected_model": "gpt-v081-test",
            "custom_model": None,
            "base_url": None,
            "enable_external_calls": True,
            "timeout_seconds": 30,
            "temperature": 0.2,
            "max_output_tokens": 900,
            "use_json_mode": True,
        },
    )


def test_health_endpoint_reports_readiness_without_secret(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["version"] == "8.6.0"
    assert response.json()["database"] == "ok"
    assert "secret" not in response.text.lower()


def test_ai_connection_retries_transient_provider_errors(
    client: TestClient,
    create_test_user,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = _headers(client, create_test_user, auth_headers)
    _configure_openai(client, headers)
    calls = {"count": 0}

    def fake_post(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise httpx.TimeoutException("timeout")
        return FakeResponse({"choices": [{"message": {"content": '{"ok":true}'}}]})

    monkeypatch.setattr("app.services.ai_settings.httpx.post", fake_post)
    monkeypatch.setattr("app.services.ai_settings.time.sleep", lambda _seconds: None)

    tested = client.post(
        "/api/settings/ai/test",
        headers=headers,
        json={
            "provider": "openai",
            "model": "gpt-v081-test",
            "base_url": None,
            "enable_external_calls": True,
            "use_json_mode": True,
        },
    )

    assert tested.status_code == 200
    assert tested.json()["success"] is True
    assert calls["count"] == 3


def test_ai_health_exposes_open_circuit_after_repeated_transient_failures(
    client: TestClient,
    create_test_user,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = _headers(client, create_test_user, auth_headers)
    _configure_openai(client, headers)

    def fail_post(*_args, **_kwargs):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr("app.services.ai_settings.httpx.post", fail_post)
    monkeypatch.setattr("app.services.ai_settings.time.sleep", lambda _seconds: None)

    for _index in range(3):
        client.post(
            "/api/settings/ai/test",
            headers=headers,
            json={
                "provider": "openai",
                "model": "gpt-v081-test",
                "base_url": None,
                "enable_external_calls": True,
                "use_json_mode": True,
            },
        )
    health = client.get("/api/settings/ai/health", headers=headers)

    assert health.status_code == 200
    assert health.json()["circuit_breaker_state"] == "open"
    assert health.json()["failure_count"] >= 3
    assert health.json()["fallback_available"] is True


def test_dipyrone_brand_aliases_resolve_to_same_active_ingredient() -> None:
    service = ClinicalDeduplicationService()

    aliases = ["Novalgina", "Anador", "Dorflex", "Neosaldina", "Lisador", "metamizol"]
    results = [service.deduplicate_medication(alias) for alias in aliases]

    assert {result.mapped_code for result in results} == {"dipirona"}
    assert all(result.jurisdiction == "BR" for result in results)


def test_accepted_reconciliation_identifier_is_masked_and_hashed(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _headers(client, create_test_user, auth_headers)
    patient = client.post(
        "/api/patients",
        headers=headers,
        json={
            "name": "Paciente Identificador",
            "age": 40,
            "weight_kg": 70,
            "allergies": [],
            "comorbidities": [],
            "current_medications": [],
        },
    )
    patient_id = patient.json()["id"]
    imported = client.post(
        "/api/integrations/json/import",
        headers=headers,
        json={
            "consent_confirmed": True,
            "purpose": "teste identificador",
            "authorized_by": "Paciente/representante autorizado",
            "source_system": "hospital_teste",
            "patient_id": patient_id,
            "payload": {
                "patient": {
                    "name": "Paciente Identificador",
                    "identifiers": [
                        {
                            "type": "hospital_record_number",
                            "value": "HOSP-V081-9999",
                        }
                    ],
                }
            },
        },
    )
    reconciliation = client.get(
        f"/api/integrations/imports/{imported.json()['id']}/reconciliation",
        headers=headers,
    )
    identifier_item = next(
        item
        for item in reconciliation.json()["items"]
        if item["field_path"].startswith("patient.identifiers")
    )
    accepted = client.post(
        "/api/integrations/imports/"
        f"{imported.json()['id']}/reconciliation/items/"
        f"{quote(identifier_item['item_id'], safe='')}/accept",
        headers=headers,
        json={"justification": "identificador revisado"},
    )
    identifiers = client.get(f"/api/patients/{patient_id}/identifiers", headers=headers)

    assert accepted.status_code == 200
    assert identifiers.status_code == 200
    assert identifiers.json()[0]["display_masked"].endswith("9999")
    assert "HOSP-V081-9999" not in identifiers.text
