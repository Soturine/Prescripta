"""PRE-02 (apresentação ambígua), PRE-03 (observações não avaliadas), PRE-04 (idempotência)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database.models import (
    AuditEventModel,
    CDSIdempotencyModel,
    MedicationModel,
    UserModel,
)
from app.domain.user import UserRole
from app.services.clinical_decision_orchestrator import ClinicalDecisionOrchestrator

CDS_URL = "/api/cds/prescription-check"


def _headers(create_test_user, auth_headers, email: str = "cds-hardening@example.test"):
    create_test_user(email=email, password="Admin@12345", role=UserRole.MEDICO)
    return auth_headers(email, "Admin@12345")


def _medication(db_session, *, concentration: str, brand: str) -> MedicationModel:
    record = MedicationModel(
        brand_name=brand,
        active_ingredient="ambiguina",
        therapeutic_class="teste",
        concentration=concentration,
        max_daily_dose_mg=1000,
        allowed_routes=["oral"],
        contraindications=[],
    )
    db_session.add(record)
    db_session.commit()
    return record


def _body(**request: object) -> dict:
    medication_request = {"dose_mg": 10, "frequency_per_day": 1, "route": "oral"} | request
    return {
        "patient": {"age": 40, "weight_kg": 70, "hypertension": False, "diabetes": False},
        "medication_request": medication_request,
        "allergies": [],
        "conditions": [],
        "current_medications": [],
    }


def _cds_audits(db_session) -> int:
    db_session.expire_all()
    return db_session.scalar(
        select(func.count())
        .select_from(AuditEventModel)
        .where(AuditEventModel.action == "cds.prescription_check")
    )


def test_ambiguous_presentations_fail_closed_with_candidates(
    client: TestClient, create_test_user, auth_headers, db_session
) -> None:
    headers = _headers(create_test_user, auth_headers)
    low = _medication(db_session, concentration="100 mg", brand="Ambiguina 100")
    high = _medication(db_session, concentration="500 mg", brand="Ambiguina 500")

    ambiguous = client.post(CDS_URL, headers=headers, json=_body(active_ingredient="ambiguina"))
    assert ambiguous.status_code == 409
    detail = ambiguous.json()["detail"]
    assert detail["code"] == "ambiguous_medication"
    assert [item["medication_id"] for item in detail["candidates"]] == [low.id, high.id]
    assert {item["concentration"] for item in detail["candidates"]} == {"100 mg", "500 mg"}
    assert _cds_audits(db_session) == 0

    explicit = client.post(
        CDS_URL,
        headers=headers,
        json=_body(medication_id=high.id, active_ingredient="ambiguina"),
    )
    assert explicit.status_code == 200
    assert {card["source"].get("medication_id") for card in explicit.json()["cards"]} <= {
        high.id,
        None,
    }


def test_single_presentation_by_ingredient_still_resolves(
    client: TestClient, create_test_user, auth_headers, db_session
) -> None:
    headers = _headers(create_test_user, auth_headers)
    _medication(db_session, concentration="100 mg", brand="Ambiguina 100")
    response = client.post(CDS_URL, headers=headers, json=_body(active_ingredient="ambiguina"))
    assert response.status_code == 200


def test_observations_are_declared_not_evaluated(
    client: TestClient, create_test_user, auth_headers, db_session
) -> None:
    headers = _headers(create_test_user, auth_headers)
    _medication(db_session, concentration="100 mg", brand="Ambiguina 100")

    without = client.post(CDS_URL, headers=headers, json=_body(active_ingredient="ambiguina"))
    assert without.json()["observations_evaluation"] == {
        "status": "none_received",
        "received_count": 0,
        "evaluated_count": 0,
        "reason": None,
    }
    assert not any("Observações" in card["summary"] for card in without.json()["cards"])

    body = _body(active_ingredient="ambiguina") | {
        "observations": [{"code": "egfr", "value": 12, "unit": "mL/min/1.73m2"}]
    }
    with_obs = client.post(CDS_URL, headers=headers, json=body)
    assert with_obs.status_code == 200
    evaluation = with_obs.json()["observations_evaluation"]
    assert evaluation["status"] == "not_evaluated"
    assert evaluation["received_count"] == 1
    assert evaluation["evaluated_count"] == 0
    warning = [c for c in with_obs.json()["cards"] if c["summary"].startswith("Observações")]
    assert warning and warning[0]["indicator"] == "warning"


def test_observations_list_is_bounded(client: TestClient, create_test_user, auth_headers) -> None:
    headers = _headers(create_test_user, auth_headers)
    body = _body(active_ingredient="ambiguina") | {"observations": [{"code": "x"}] * 101}
    assert client.post(CDS_URL, headers=headers, json=body).status_code == 422


@pytest.mark.parametrize("same_content", [True, False])
def test_idempotency_race_replays_or_conflicts_without_orphan_audit(
    client: TestClient,
    create_test_user,
    auth_headers,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
    same_content: bool,
) -> None:
    headers = _headers(create_test_user, auth_headers)
    _medication(db_session, concentration="100 mg", brand="Ambiguina 100")
    body = _body(active_ingredient="ambiguina")
    first = client.post(CDS_URL, headers=headers | {"Idempotency-Key": "race-a"}, json=body)
    assert first.status_code == 200
    stored = db_session.scalar(select(CDSIdempotencyModel))
    assert _cds_audits(db_session) == 1

    original_init = ClinicalDecisionOrchestrator.__init__
    original_evaluate = ClinicalDecisionOrchestrator.evaluate

    def capturing_init(self, db=None):
        original_init(self, db)
        self._race_db = db

    def racing_evaluate(self, **kwargs):
        # Uma requisição concorrente grava a mesma chave depois da consulta inicial.
        self._race_db.add(
            CDSIdempotencyModel(
                user_id=kwargs["user"].id,
                idempotency_key="race-b",
                request_hash=stored.request_hash if same_content else "0" * 64,
                response_payload=stored.response_payload,
            )
        )
        self._race_db.flush()
        return original_evaluate(self, **kwargs)

    monkeypatch.setattr(ClinicalDecisionOrchestrator, "__init__", capturing_init)
    monkeypatch.setattr(ClinicalDecisionOrchestrator, "evaluate", racing_evaluate)
    loser = TestClient(client.app, raise_server_exceptions=False).post(
        CDS_URL, headers=headers | {"Idempotency-Key": "race-b"}, json=body
    )

    if same_content:
        assert loser.status_code == 200
        assert loser.json() == first.json()
    else:
        assert loser.status_code == 409
        assert loser.json()["detail"]["code"] == "idempotency_key_reused"
    # O perdedor não deixa auditoria órfã de uma avaliação cuja resposta não foi entregue.
    assert _cds_audits(db_session) == 1


def _validated_medication(db_session) -> MedicationModel:
    record = MedicationModel(
        brand_name="Validada Demo",
        active_ingredient="validadina",
        therapeutic_class="teste",
        max_daily_dose_mg=1000,
        allowed_routes=["oral"],
        contraindications=[],
        validation_status="validated",
        knowledge_source="Fonte sintética validada para teste",
        dose_rule_validation_status="validated",
        dose_source_refs=["dose:test:v1"],
        policy_validation_status="validated",
        policy_source_refs=["policy:test:v1"],
        policy_version="policy:test:v1",
    )
    db_session.add(record)
    db_session.commit()
    return record


def test_unevaluated_observations_never_yield_no_issue(
    client: TestClient, create_test_user, auth_headers, db_session
) -> None:
    """PRE-03b: observações recebidas e não avaliadas impedem `evaluated_no_issue`."""
    headers = _headers(create_test_user, auth_headers, "cds-verified@example.test")
    prescriber = db_session.scalar(
        select(UserModel).where(UserModel.email == "cds-verified@example.test")
    )
    prescriber.credential_verification_status = "verified"
    prescriber.specialty_code = "medicina_geral"
    db_session.commit()
    _validated_medication(db_session)
    body = _body(active_ingredient="validadina")

    clean = client.post(CDS_URL, headers=headers, json=body)
    assert clean.status_code == 200
    # Controle positivo: com cobertura completa e sem observações, a decisão pode ser favorável.
    assert clean.json()["decision"]["decision_status"] == "evaluated_no_issue"

    with_obs = client.post(
        CDS_URL,
        headers=headers,
        json=body | {"observations": [{"code": "potassium", "value": 7.1, "unit": "mmol/L"}]},
    )
    decision = with_obs.json()["decision"]
    assert decision["decision_status"] != "evaluated_no_issue"
    assert decision["human_review_required"] is True
    assert any(
        item.get("module") == "observations" for item in decision["coverage"]["not_evaluated"]
    )
