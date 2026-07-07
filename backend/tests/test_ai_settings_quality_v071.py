from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.seed import seed_demo_data
from app.services.ai_settings import _MEMORY_CREDENTIALS


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def _headers(client: TestClient, db_session: Session, auth_headers) -> dict[str, str]:
    _MEMORY_CREDENTIALS.clear()
    seed_demo_data(db_session)
    return auth_headers("admin@prescripta.local", "Admin@12345")


def _explain_payload() -> dict[str, Any]:
    return {
        "patient": {"name": "Paciente Teste", "age": 44, "weight_kg": 70},
        "medication": {
            "brand_name": "Teste",
            "active_ingredient": "teste",
            "therapeutic_class": "analgesico",
            "max_daily_dose_mg": 1000,
            "allowed_routes": ["oral"],
            "contraindications": [],
        },
        "dose_mg": 100,
        "frequency_per_day": 1,
        "route": "oral",
        "status": "liberado",
        "risk_level": "baixo",
        "alerts": [],
        "recommendation": "Revisar conforme protocolo local.",
        "human_review_required": False,
        "user_profile": "medico",
        "dose_summary": {},
        "compatibility": {},
        "patient_factors_considered": [],
        "medication_factors_considered": [],
        "rag_evidence": [],
        "clinical_context_graph": {},
        "alternatives": [],
    }


def test_ai_credential_is_masked_and_never_returned_in_api_or_audit(
    client: TestClient,
    db_session: Session,
    auth_headers,
) -> None:
    headers = _headers(client, db_session, auth_headers)
    secret = "sk-test-secret-1234"

    saved = client.post(
        "/api/settings/ai/credentials",
        headers=headers,
        json={"provider": "openai", "api_key": secret, "base_url": None, "persist": True},
    )
    audit = client.get("/api/audit", headers=headers)

    assert saved.status_code == 200
    assert saved.json()["masked_api_key"] == "sk-t...1234"
    assert secret not in saved.text
    assert secret not in audit.text
    assert any(event["action"] == "ai_configuration.credential_saved" for event in audit.json())


def test_external_calls_disabled_prevents_provider_call_and_uses_fallback(
    client: TestClient,
    db_session: Session,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = _headers(client, db_session, auth_headers)
    client.post(
        "/api/settings/ai/credentials",
        headers=headers,
        json={"provider": "openai", "api_key": "sk-test-secret-1234", "persist": True},
    )
    selected = client.post(
        "/api/settings/ai/select-model",
        headers=headers,
        json={
            "provider": "openai",
            "selected_model": "gpt-test",
            "custom_model": None,
            "base_url": None,
            "enable_external_calls": False,
            "timeout_seconds": 30,
            "temperature": 0.2,
            "max_output_tokens": 900,
            "use_json_mode": True,
        },
    )

    def fail_post(*_args, **_kwargs):
        raise AssertionError("External provider should not be called")

    monkeypatch.setattr("app.services.ai_settings.httpx.post", fail_post)
    explained = client.post("/api/prescriptions/explain", headers=headers, json=_explain_payload())

    assert selected.status_code == 200
    assert explained.status_code == 200
    assert explained.json()["provider"] == "fallback"
    assert explained.json()["used_fallback"] is True


def test_selected_model_is_used_by_real_external_ai_call(
    client: TestClient,
    db_session: Session,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = _headers(client, db_session, auth_headers)
    captured: dict[str, str] = {}
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
            "selected_model": "gpt-selected-test",
            "custom_model": None,
            "base_url": None,
            "enable_external_calls": True,
            "timeout_seconds": 30,
            "temperature": 0.2,
            "max_output_tokens": 900,
            "use_json_mode": True,
        },
    )

    def fake_post(_url, *, headers, json, timeout):
        captured["model"] = json["model"]
        assert "Authorization" in headers
        assert timeout == 30
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"simple_explanation":"ok","technical_summary":"ok",'
                                '"review_questions":["revisar"],'
                                '"educational_notice":"ok"}'
                            )
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("app.services.ai_settings.httpx.post", fake_post)
    explained = client.post("/api/prescriptions/explain", headers=headers, json=_explain_payload())

    assert explained.status_code == 200
    assert captured["model"] == "gpt-selected-test"
    assert explained.json()["provider"] == "openai"
    assert explained.json()["model"] == "gpt-selected-test"
    assert explained.json()["used_fallback"] is False


def test_model_cache_refresh_uses_previous_cache_when_provider_fails(
    client: TestClient,
    db_session: Session,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = _headers(client, db_session, auth_headers)
    client.post(
        "/api/settings/ai/credentials",
        headers=headers,
        json={"provider": "openai", "api_key": "sk-test-secret-1234", "persist": True},
    )

    def fake_get_success(*_args, **_kwargs):
        return FakeResponse({"data": [{"id": "gpt-cache-test"}]})

    monkeypatch.setattr("app.services.ai_settings.httpx.get", fake_get_success)
    refreshed = client.get("/api/settings/ai/models?provider=openai&refresh=true", headers=headers)

    def fake_get_error(*_args, **_kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr("app.services.ai_settings.httpx.get", fake_get_error)
    cached = client.get("/api/settings/ai/models?provider=openai&refresh=true", headers=headers)

    assert refreshed.status_code == 200
    assert refreshed.json()["models"][0]["model_id"] == "gpt-cache-test"
    assert cached.status_code == 200
    assert cached.json()["status"] == "error_cache"
    assert cached.json()["models"][0]["model_id"] == "gpt-cache-test"


def test_custom_model_requires_connection_test_before_activation(
    client: TestClient,
    db_session: Session,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = _headers(client, db_session, auth_headers)
    client.post(
        "/api/settings/ai/credentials",
        headers=headers,
        json={"provider": "openai", "api_key": "sk-test-secret-1234", "persist": True},
    )
    payload = {
        "provider": "openai",
        "selected_model": None,
        "custom_model": "gpt-custom-test",
        "base_url": None,
        "enable_external_calls": True,
        "timeout_seconds": 30,
        "temperature": 0.2,
        "max_output_tokens": 900,
        "use_json_mode": True,
    }
    blocked = client.post("/api/settings/ai/select-model", headers=headers, json=payload)

    def fake_post(_url, *, headers, json, timeout):
        return FakeResponse({"choices": [{"message": {"content": '{"ok":true}'}}]})

    monkeypatch.setattr("app.services.ai_settings.httpx.post", fake_post)
    tested = client.post(
        "/api/settings/ai/test",
        headers=headers,
        json={
            "provider": "openai",
            "model": "gpt-custom-test",
            "base_url": None,
            "enable_external_calls": True,
            "use_json_mode": True,
        },
    )
    activated = client.post("/api/settings/ai/select-model", headers=headers, json=payload)

    assert blocked.status_code == 400
    assert tested.status_code == 200
    assert tested.json()["success"] is True
    assert activated.status_code == 200
    assert activated.json()["selected_model"] == "gpt-custom-test"


def test_text_quality_basics_for_env_and_docs() -> None:
    root = Path(__file__).resolve().parents[2]
    env_example = (root / ".env.example").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    assert "\n" in env_example.strip()
    assert "PRESCRIPTA_CONFIG_ENCRYPTION_KEY=" in env_example
    assert chr(0x00C3) not in readme
    assert chr(0xFFFD) not in readme
    assert len(readme.splitlines()) > 20


def test_safedose_audit_and_emergency_roadmap_docs_exist() -> None:
    root = Path(__file__).resolve().parents[2]

    assert (root / "docs/benchmark/safedose-parity-audit-v0.7.1.md").exists()
    assert (root / "docs/product/emergency-protocols-roadmap.md").exists()


def test_additional_fhir_review_scenario_is_accepted_for_human_review(
    client: TestClient,
    db_session: Session,
    auth_headers,
) -> None:
    headers = _headers(client, db_session, auth_headers)
    response = client.post(
        "/api/integrations/fhir/import-bundle",
        headers=headers,
        json={
            "consent_confirmed": True,
            "purpose": "teste fhir",
            "authorized_by": "Paciente Demo",
            "source_system": "fhir_v071",
            "patient_id": None,
            "bundle": {
                "resourceType": "Bundle",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "AllergyIntolerance",
                            "code": {"text": "dipirona"},
                        }
                    },
                    {
                        "resource": {
                            "resourceType": "Observation",
                            "code": {"text": "creatinina"},
                            "valueString": "externo pendente",
                        }
                    },
                ],
            },
        },
    )
    reconciliation = client.get(
        f"/api/integrations/imports/{response.json()['id']}/reconciliation",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending_review"
    assert len(response.json()["records"]) == 2
    assert reconciliation.status_code == 200
    assert reconciliation.json()["summary"]["total"] >= 2
