from __future__ import annotations

from fastapi.testclient import TestClient

from app.domain.user import UserRole


def _admin_headers(client: TestClient, create_test_user, auth_headers) -> dict[str, str]:
    create_test_user(email="admin@test.local", password="Admin@12345", role=UserRole.ADMIN)
    return auth_headers("admin@test.local", "Admin@12345")


def _checked_prescription(client: TestClient, headers: dict[str, str]) -> int:
    patient = client.post(
        "/api/patients",
        headers=headers,
        json={
            "name": "Paciente Relatorio",
            "age": 70,
            "weight_kg": 70,
            "height_cm": 170,
            "allergies": [],
            "comorbidities": ["hipertensao"],
            "current_medications": [],
            "renal_condition": None,
        },
    )
    medication = client.post(
        "/api/medications",
        headers=headers,
        json={
            "brand_name": "Tansul Demo",
            "active_ingredient": "tansulosina",
            "therapeutic_class": "alfa-bloqueador",
            "max_daily_dose_mg": 0.8,
            "allowed_routes": ["oral"],
            "contraindications": [],
            "notes": "Pode exigir cautela por tontura.",
            "source_jurisdiction": "BR",
            "evidence_source_type": "demo_seed",
            "validation_status": "demo",
        },
    )
    checked = client.post(
        "/api/prescriptions/check",
        headers=headers,
        json={
            "patient_id": patient.json()["id"],
            "medication_id": medication.json()["id"],
            "dose_mg": 0.4,
            "frequency_per_day": 1,
            "route": "oral",
            "duration_days": 7,
        },
    )
    assert checked.status_code == 200
    return int(checked.json()["audit_id"])


def test_prescription_reports_exports_and_generated_report_history(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    headers = _admin_headers(client, create_test_user, auth_headers)
    audit_id = _checked_prescription(client, headers)

    preview = client.get(f"/api/reports/prescriptions/{audit_id}/preview", headers=headers)
    technical_pdf = client.get(f"/api/reports/prescriptions/{audit_id}/pdf", headers=headers)
    patient_pdf = client.get(
        f"/api/reports/prescriptions/{audit_id}/patient-guidance.pdf",
        headers=headers,
    )
    exported_json = client.get(f"/api/exports/prescriptions/{audit_id}.json", headers=headers)
    exported_csv = client.get(f"/api/exports/prescriptions/{audit_id}.csv", headers=headers)
    reports = client.get("/api/reports", headers=headers)

    assert preview.status_code == 200
    assert preview.json()["evidence_bundle_hash"]
    assert preview.json()["narrative_metadata"]["fallback_used"] is True
    assert technical_pdf.status_code == 200
    assert technical_pdf.content.startswith(b"%PDF")
    assert patient_pdf.status_code == 200
    assert patient_pdf.content.startswith(b"%PDF")
    assert exported_json.status_code == 200
    assert "evidence_bundle_hash" in exported_json.text
    assert exported_csv.status_code == 200
    assert "medication" in exported_csv.text
    assert reports.status_code == 200
    assert len(reports.json()) >= 2
    assert {item["report_type"] for item in reports.json()} >= {
        "prescription_technical",
        "patient_guidance",
    }


def test_report_permissions_for_nursing_and_auditor(
    client: TestClient,
    create_test_user,
    auth_headers,
) -> None:
    admin_headers = _admin_headers(client, create_test_user, auth_headers)
    audit_id = _checked_prescription(client, admin_headers)
    create_test_user(
        email="nurse@test.local",
        password="Nurse@12345",
        role=UserRole.ENFERMAGEM,
        name="Enfermagem Teste",
    )
    nurse_headers = auth_headers("nurse@test.local", "Nurse@12345")
    create_test_user(
        email="auditor@test.local",
        password="Auditor@12345",
        role=UserRole.AUDITOR,
        name="Auditor Teste",
    )
    auditor_headers = auth_headers("auditor@test.local", "Auditor@12345")

    patient_pdf = client.get(
        f"/api/reports/prescriptions/{audit_id}/patient-guidance.pdf",
        headers=nurse_headers,
    )
    technical_pdf = client.get(f"/api/reports/prescriptions/{audit_id}/pdf", headers=nurse_headers)
    audit_json = client.get("/api/exports/audit-events.json", headers=auditor_headers)

    assert patient_pdf.status_code == 200
    assert technical_pdf.status_code == 403
    assert audit_json.status_code == 200
    assert "audit_events" in audit_json.text


def test_ai_report_composer_rejects_invalid_source_and_uses_fallback(
    client: TestClient,
    create_test_user,
    auth_headers,
    monkeypatch,
) -> None:
    headers = _admin_headers(client, create_test_user, auth_headers)
    audit_id = _checked_prescription(client, headers)
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
            "selected_model": "gpt-report-test",
            "custom_model": None,
            "base_url": None,
            "enable_external_calls": True,
            "timeout_seconds": 30,
            "temperature": 0.2,
            "max_output_tokens": 900,
            "use_json_mode": True,
        },
    )

    def fake_complete_json(*_args, **_kwargs):
        return {
            "executive_summary": "ok",
            "professional_explanation": "ok",
            "patient_guidance": "ok",
            "evidence_summary": "ok",
            "missing_data_note": "",
            "functional_context_note": "",
            "reconciliation_summary": "",
            "safety_counseling_summary": "",
            "limitations_note": "ok",
            "human_review_note": "ok",
            "source_note": "ok",
            "confidence": 0.8,
            "requires_human_review": True,
            "warnings": [],
            "cited_source_ids": ["fonte_inventada"],
        }

    monkeypatch.setattr(
        "app.services.ai_settings.AISettingsService.complete_json",
        fake_complete_json,
    )
    preview = client.get(f"/api/reports/prescriptions/{audit_id}/preview", headers=headers)

    assert preview.status_code == 200
    assert preview.json()["narrative_metadata"]["fallback_used"] is True
    assert preview.json()["narrative_metadata"]["status"] == "fallback_after_ai_error"
