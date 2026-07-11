from typing import Any

from fastapi.testclient import TestClient

from app.api.routes import prescriptions
from app.core.config import Settings
from app.domain.user import UserRole
from app.schemas.prescription_schema import (
    AlertRead,
    PrescriptionExplainMedication,
    PrescriptionExplainPatient,
    PrescriptionExplainRequest,
)
from app.services.ai_explainer import AIExplainer


def _sample_explain_request() -> PrescriptionExplainRequest:
    return PrescriptionExplainRequest(
        patient=PrescriptionExplainPatient(
            id=1,
            name="Paciente Teste",
            birth_date=None,
            age=72,
            weight_kg=81,
            height_cm=174,
            allergies=["ibuprofeno"],
            comorbidities=["doenca renal grave"],
            current_medications=["varfarina"],
        ),
        medication=PrescriptionExplainMedication(
            id=1,
            brand_name="Ibuvida",
            active_ingredient="ibuprofeno",
            therapeutic_class="anti-inflamatorio",
            max_daily_dose_mg=2400,
            allowed_routes=["oral"],
            contraindications=["doenca renal grave"],
            notes="Teste",
        ),
        dose_mg=400,
        frequency_per_day=2,
        route="oral",
        status="bloqueado",
        risk_level="critico",
        alerts=[
            AlertRead(
                code="ALLERGY_BLOCK",
                title="Alergia relevante identificada",
                description="Alergia coincide com medicamento.",
                severity="critico",
                recommendation="Bloquear a prescricao.",
            )
        ],
        recommendation="Nao prosseguir sem revisao humana.",
        human_review_required=True,
        audit_id=1,
        user_profile="medico",
    )


def _create_blocked_check(
    client: TestClient,
    headers: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    patient_response = client.post(
        "/api/patients",
        headers=headers,
        json={
            "name": "Paciente IA",
            "age": 72,
            "weight_kg": 81,
            "height_cm": 174,
            "allergies": ["ibuprofeno"],
            "comorbidities": ["doenca renal grave"],
            "current_medications": ["varfarina"],
        },
    )
    medication_response = client.post(
        "/api/medications",
        headers=headers,
        json={
            "brand_name": "Ibuvida",
            "active_ingredient": "ibuprofeno",
            "therapeutic_class": "anti-inflamatorio",
            "max_daily_dose_mg": 2400,
            "allowed_routes": ["oral"],
            "contraindications": ["doenca renal grave"],
            "notes": "Teste",
        },
    )

    check_response = client.post(
        "/api/prescriptions/check",
        headers=headers,
        json={
            "patient_id": patient_response.json()["id"],
            "medication_id": medication_response.json()["id"],
            "dose_mg": 400,
            "frequency_per_day": 2,
            "route": "oral",
        },
    )

    return patient_response.json(), medication_response.json(), check_response.json()


def _explain_payload(
    patient: dict[str, Any],
    medication: dict[str, Any],
    check_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        **check_result,
        "patient": patient,
        "medication": medication,
        "dose_mg": 400,
        "frequency_per_day": 2,
        "route": "oral",
        "user_profile": "medico",
    }


def test_ai_explainer_returns_deterministic_fallback_without_api_key() -> None:
    explainer = AIExplainer(Settings(ai_provider="openai", ai_api_key="", ai_model="gpt-test"))

    result = explainer.explain(_sample_explain_request(), requester_role="medico")

    assert result.used_fallback is True
    assert result.provider == "fallback"
    assert result.prescription_status == "bloqueado"
    assert result.critical_alert_codes == ["ALLERGY_BLOCK"]
    assert "educacional" in result.educational_notice


def test_prescription_explain_endpoint_falls_back_without_api_key(
    client: TestClient,
    create_test_user,
    auth_headers,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        prescriptions,
        "settings",
        Settings(ai_provider="fallback", ai_api_key="", ai_model="gpt-test"),
    )
    create_test_user(email="admin@test.local", password="Admin@12345", role=UserRole.ADMIN)
    headers = auth_headers("admin@test.local", "Admin@12345")
    patient, medication, check_result = _create_blocked_check(client, headers)

    response = client.post(
        "/api/prescriptions/explain",
        headers=headers,
        json=_explain_payload(patient, medication, check_result),
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["used_fallback"] is True
    assert payload["simple_explanation"]
    assert payload["review_questions"]


def test_ai_explanation_does_not_change_final_status_or_risk(
    client: TestClient,
    create_test_user,
    auth_headers,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        prescriptions,
        "settings",
        Settings(ai_provider="fallback", ai_api_key="", ai_model="gpt-test"),
    )
    create_test_user(email="admin@test.local", password="Admin@12345", role=UserRole.ADMIN)
    headers = auth_headers("admin@test.local", "Admin@12345")
    patient, medication, check_result = _create_blocked_check(client, headers)

    response = client.post(
        "/api/prescriptions/explain",
        headers=headers,
        json=_explain_payload(patient, medication, check_result),
    )

    payload = response.json()
    assert payload["prescription_status"] == check_result["status"]
    assert payload["risk_level"] == check_result["risk_level"]


def test_ai_explanation_preserves_critical_blocking_alerts(
    client: TestClient,
    create_test_user,
    auth_headers,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        prescriptions,
        "settings",
        Settings(ai_provider="fallback", ai_api_key="", ai_model="gpt-test"),
    )
    create_test_user(email="admin@test.local", password="Admin@12345", role=UserRole.ADMIN)
    headers = auth_headers("admin@test.local", "Admin@12345")
    patient, medication, check_result = _create_blocked_check(client, headers)

    response = client.post(
        "/api/prescriptions/explain",
        headers=headers,
        json=_explain_payload(patient, medication, check_result),
    )

    payload = response.json()
    critical_codes = {
        alert["code"] for alert in check_result["alerts"] if alert["severity"] == "critico"
    }
    assert critical_codes
    assert critical_codes.issubset(set(payload["critical_alert_codes"]))
    assert "bloqueada" in payload["simple_explanation"]


def test_user_without_prescription_permission_cannot_request_explanation(
    client: TestClient,
    create_test_user,
    auth_headers,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        prescriptions,
        "settings",
        Settings(ai_provider="fallback", ai_api_key="", ai_model="gpt-test"),
    )
    create_test_user(email="admin@test.local", password="Admin@12345", role=UserRole.ADMIN)
    create_test_user(email="auditor@test.local", password="Auditor@12345", role=UserRole.AUDITOR)
    admin_headers = auth_headers("admin@test.local", "Admin@12345")
    auditor_headers = auth_headers("auditor@test.local", "Auditor@12345")
    patient, medication, check_result = _create_blocked_check(client, admin_headers)

    response = client.post(
        "/api/prescriptions/explain",
        headers=auditor_headers,
        json=_explain_payload(patient, medication, check_result),
    )

    assert response.status_code == 403


def test_audit_keeps_prescription_check_event_after_explanation(
    client: TestClient,
    create_test_user,
    auth_headers,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        prescriptions,
        "settings",
        Settings(ai_provider="fallback", ai_api_key="", ai_model="gpt-test"),
    )
    create_test_user(email="admin@test.local", password="Admin@12345", role=UserRole.ADMIN)
    headers = auth_headers("admin@test.local", "Admin@12345")
    patient, medication, check_result = _create_blocked_check(client, headers)

    explain_response = client.post(
        "/api/prescriptions/explain",
        headers=headers,
        json=_explain_payload(patient, medication, check_result),
    )
    audit_response = client.get("/api/audit", headers=headers)

    assert explain_response.status_code == 200
    prescription_checks = [
        event for event in audit_response.json()["items"] if event["action"] == "prescription.check"
    ]
    assert len(prescription_checks) == 1
    assert prescription_checks[0]["resource_id"] == str(check_result["audit_id"])
