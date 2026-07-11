from __future__ import annotations

from fastapi.testclient import TestClient

from app.domain.user import UserRole


def _headers(client: TestClient, create_test_user, auth_headers) -> dict[str, str]:
    create_test_user(email="admin@v082.local", password="Admin@12345", role=UserRole.ADMIN)
    return auth_headers("admin@v082.local", "Admin@12345")


def test_protocols_list_and_detail_are_available(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _headers(client, create_test_user, auth_headers)

    listed = client.get("/api/protocols", headers=headers)
    detail = client.get("/api/protocols/anafilaxia", headers=headers)

    assert listed.status_code == 200
    assert len(listed.json()) >= 7
    assert {item["id"] for item in listed.json()} >= {
        "anafilaxia",
        "pcr",
        "convulsao",
        "hipoglicemia",
        "dor_toracica",
        "broncoespasmo",
        "intoxicacao",
    }
    assert detail.status_code == 200
    assert detail.json()["source_name"]
    assert detail.json()["steps"][0]["requires_human_judgment"] is True
    assert client.get("/api/protocols/dor_toracica", headers=headers).status_code == 200


def test_protocol_run_requires_minimum_context(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _headers(client, create_test_user, auth_headers)

    response = client.post("/api/protocols/hipoglicemia/run", headers=headers, json={})

    assert response.status_code == 422
    assert "Contexto mínimo ausente" in response.text


def test_protocol_run_records_audit_and_calculations(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _headers(client, create_test_user, auth_headers)

    run = client.post(
        "/api/protocols/anafilaxia/run",
        headers=headers,
        json={
            "context": {
                "suspected_trigger": "antibiótico informado pelo paciente",
                "weight_kg": 70,
                "age_years": 35,
                "respiratory_symptoms": True,
            },
            "selected_step_orders": [1, 2, 3],
            "notes": "Cenário demonstrativo sem dado real.",
        },
    )
    audit = client.get("/api/audit", headers=headers, params={"resource_type": "protocol_run"})

    assert run.status_code == 200
    body = run.json()
    assert body["run_id"] > 0
    assert body["calculated_values"][0]["source_ref"] == "anafilaxia_adrenalina_im"
    assert body["calculated_values"][0]["requires_human_confirmation"] is True
    assert audit.status_code == 200
    events = audit.json()
    assert {event["action"] for event in events} >= {"protocol.run", "protocol.step_checked"}
    run_event = next(event for event in events if event["action"] == "protocol.run")
    assert run_event["details"]["secret_logged"] is False


def test_protocol_report_and_exports_use_run_event(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _headers(client, create_test_user, auth_headers)
    run = client.post(
        "/api/protocols/hipoglicemia/run",
        headers=headers,
        json={"context": {"glucose_mg_dl": 52, "conscious": True, "can_swallow": True}},
    )
    run_id = run.json()["run_id"]

    report = client.get(
        "/api/protocols/hipoglicemia/report",
        headers=headers,
        params={"run_id": run_id},
    )
    exported_json = client.get(
        f"/api/protocols/hipoglicemia/events/{run_id}.json",
        headers=headers,
    )
    exported_csv = client.get(
        f"/api/protocols/hipoglicemia/events/{run_id}.csv",
        headers=headers,
    )

    assert report.status_code == 200
    assert report.json()["run_id"] == run_id
    assert "Classificação glicêmica" in str(report.json()["report_payload"])
    assert exported_json.status_code == 200
    assert exported_json.headers["content-type"].startswith("application/json")
    assert exported_csv.status_code == 200
    assert "protocol_id" in exported_csv.text


def test_protocol_explain_uses_fallback_without_changing_structure(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _headers(client, create_test_user, auth_headers)

    explained = client.post(
        "/api/protocols/broncoespasmo/explain",
        headers=headers,
        json={"context": {"spo2": 91}, "question": "Qual o racional inicial?"},
    )

    assert explained.status_code == 200
    body = explained.json()
    assert body["used_fallback"] is True
    assert body["structure_locked"] is True
    assert body["protocol_id"] == "broncoespasmo"
    assert "não substitui" in body["educational_notice"]
