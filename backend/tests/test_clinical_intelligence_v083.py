from __future__ import annotations

from fastapi.testclient import TestClient

from app.domain.user import UserRole


def _admin_headers(client: TestClient, create_test_user, auth_headers) -> dict[str, str]:
    create_test_user(email="admin@v083.local", password="Admin@12345", role=UserRole.ADMIN)
    return auth_headers("admin@v083.local", "Admin@12345")


def _patient(client: TestClient, headers: dict[str, str], **overrides) -> int:
    payload = {
        "name": "Paciente v083",
        "age": 44,
        "weight_kg": 56,
        "height_cm": 162,
        "allergies": ["dipirona"],
        "comorbidities": ["asma"],
        "current_medications": ["sertralina"],
        "mental_health_factors": ["transtorno_bipolar"],
        "renal_condition": None,
    }
    payload.update(overrides)
    response = client.post("/api/patients", headers=headers, json=payload)
    assert response.status_code == 201
    return int(response.json()["id"])


def test_protocol_run_generates_report_and_uses_patient_context(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _admin_headers(client, create_test_user, auth_headers)
    patient_id = _patient(client, headers)

    run = client.post(
        "/api/protocols/anafilaxia/run",
        headers=headers,
        json={
            "patient_id": patient_id,
            "context": {"suspected_trigger": "medicamento informado"},
            "selected_step_orders": [1, 2, 4],
        },
    )
    assert run.status_code == 200
    body = run.json()
    assert body["patient_id"] == patient_id
    assert body["protocol_version"].startswith("v0.8.3")
    assert body["patient_context_summary"]["weight_kg"] == 56
    assert any("alergias" in flag.lower() for flag in body["triage_flags"])

    pdf = client.get(f"/api/protocols/runs/{body['run_id']}/report.pdf", headers=headers)
    reports = client.get("/api/reports", headers=headers, params={"target_type": "protocol_run"})
    audit = client.get(
        "/api/audit",
        headers=headers,
        params={"protocol": "anafilaxia", "protocol_version": body["protocol_version"]},
    )
    exported_json = client.get(
        f"/api/protocols/runs/{body['run_id']}/report.json",
        headers=headers,
    )
    exported_csv = client.get(
        f"/api/protocols/runs/{body['run_id']}/report.csv",
        headers=headers,
    )

    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert reports.status_code == 200
    assert reports.json()[0]["report_type"] == "protocol_run_report"
    assert audit.status_code == 200
    assert {event["action"] for event in audit.json()} >= {
        "protocol.run",
        "protocol.report_generated",
        "protocol.report_downloaded",
    }
    assert exported_json.status_code == 200
    assert '"protocol_run_report"' in exported_json.text
    assert exported_csv.status_code == 200
    assert "protocol_version" in exported_csv.text


def test_patient_document_extraction_review_and_knowledge_bundle(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _admin_headers(client, create_test_user, auth_headers)
    patient_id = _patient(client, headers, allergies=[], current_medications=[])

    document = client.post(
        f"/api/patients/{patient_id}/documents",
        headers=headers,
        json={
            "document_type": "laudo_texto",
            "title": "Resumo externo demonstrativo",
            "source_type": "manual_text",
            "raw_text": (
                "Paciente usa sertralina. Historico de transtorno bipolar. "
                "Relata alergia: dipirona."
            ),
        },
    )
    extraction = client.post(
        f"/api/patients/{patient_id}/documents/{document.json()['id']}/extract",
        headers=headers,
    )
    assert document.status_code == 201
    assert extraction.status_code == 200
    extraction_payload = extraction.json()
    assert extraction_payload["validation_status"] == "pending_review"
    assert extraction_payload["review_status"] == "pending_review"
    assert "sertralina" in extraction_payload["extracted_entities"]["medications"]

    reviewed = client.post(
        f"/api/patients/{patient_id}/document-extractions/{extraction_payload['id']}/review",
        headers=headers,
        json={
            "decision": "accept",
            "accepted_entities": extraction_payload["extracted_entities"],
            "justification": "Teste v0.8.3",
        },
    )
    bundle = client.get(f"/api/patients/{patient_id}/knowledge-bundle", headers=headers)
    patient = client.get(f"/api/patients/{patient_id}", headers=headers)

    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == "accepted"
    assert bundle.status_code == 200
    assert bundle.json()["send_identifiable_data"] is False
    assert len(bundle.json()["reviewed_documents"]) == 1
    assert "sertralina" in bundle.json()["reviewed_entities"]["medications"]
    assert "sertralina" in patient.json()["current_medications"]
    assert "transtorno bipolar" in " ".join(patient.json()["mental_health_factors"]).lower()


def test_weight_age_height_bundle_and_psychotropic_rules_are_used(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _admin_headers(client, create_test_user, auth_headers)
    patient_id = _patient(
        client,
        headers,
        age=70,
        weight_kg=20,
        height_cm=110,
        mental_health_factors=["transtorno_bipolar", "mania_hipomania"],
    )
    medication = client.post(
        "/api/medications",
        headers=headers,
        json={
            "brand_name": "Sertralina Peso Demo",
            "active_ingredient": "sertralina",
            "therapeutic_class": "inibidor seletivo da recaptacao de serotonina",
            "therapeutic_classes": ["antidepressivo", "isrs"],
            "source_jurisdiction": "BR",
            "evidence_source_type": "demo_seed",
            "validation_status": "demo",
            "max_daily_dose_mg": 10000,
            "dose_mg_per_kg": 2,
            "dose_by_weight_enabled": True,
            "allowed_routes": ["oral"],
            "contraindications": [],
            "neuropsychiatric_cautions": ["risco_serotoninergico"],
            "notes": "Demo para regra por peso e revisao neuropsiquiatrica.",
        },
    )
    checked = client.post(
        "/api/prescriptions/check",
        headers=headers,
        json={
            "patient_id": patient_id,
            "medication_id": medication.json()["id"],
            "dose_mg": 50,
            "frequency_per_day": 2,
            "route": "oral",
            "duration_days": 7,
        },
    )

    assert checked.status_code == 200
    body = checked.json()
    codes = {alert["code"] for alert in body["alerts"]}
    assert "WEIGHT_BASED_DOSE_EXCEEDED" in codes
    assert "ANTIDEPRESSANT_BIPOLAR_REVIEW" in codes
    assert body["dose_summary"]["weight_based_rule"]["was_considered"] is True
    assert body["dose_summary"]["anthropometrics"]["bmi_considered"] is True
    assert body["patient_knowledge_bundle"]["send_identifiable_data"] is False
    assert body["clinical_view"]["patient_data_considered"]


def test_medication_knowledge_lookup_bulk_import_and_review(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _admin_headers(client, create_test_user, auth_headers)

    lookup = client.post(
        "/api/medications/knowledge/lookup",
        headers=headers,
        json={
            "query": "amoxicilina",
            "source_name": "Texto institucional demonstrativo",
            "source_text": "amoxicilina; sinonimos: amoxicilina tri-hidratada",
        },
    )
    bulk = client.post(
        "/api/medications/knowledge/bulk-import",
        headers=headers,
        json={
            "source_name": "lote_v083",
            "items": [
                {"active_ingredient": "ondansetrona", "therapeutic_class": "antiemetico"},
                {"active_ingredient": "omeprazol", "therapeutic_class": "gastroprotetor"},
            ],
        },
    )
    approved = client.post(
        f"/api/medications/knowledge/curation-queue/{lookup.json()['id']}/review",
        headers=headers,
        json={"decision": "approve", "justification": "Curadoria teste"},
    )
    queue = client.get(
        "/api/medications/knowledge/curation-queue",
        headers=headers,
        params={"review_status": "pending_review"},
    )

    assert lookup.status_code == 200
    assert lookup.json()["review_status"] == "pending_review"
    assert bulk.status_code == 200
    assert len(bulk.json()) == 2
    assert approved.status_code == 200
    assert approved.json()["review_status"] == "approved"
    assert queue.status_code == 200
    assert all(item["review_status"] == "pending_review" for item in queue.json())
