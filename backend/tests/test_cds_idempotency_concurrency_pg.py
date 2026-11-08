"""PRE-04 com concorrência real: requisições simultâneas, conexões distintas, PostgreSQL.

Roda só com `PRESCRIPTA_TEST_DATABASE_URL=postgresql+psycopg://...` (harness opt-in do conftest);
em SQLite (uma conexão compartilhada) não há concorrência real e o teste é pulado.
"""

from __future__ import annotations

import os
import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database.models import AuditEventModel, CDSIdempotencyModel, MedicationModel
from app.domain.user import UserRole

pytestmark = pytest.mark.skipif(
    not os.getenv("PRESCRIPTA_TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="concorrência real exige PostgreSQL",
)

CDS_URL = "/api/cds/prescription-check"
ROUNDS = 8


def _body(dose: int) -> dict:
    return {
        "patient": {"age": 40, "weight_kg": 70, "hypertension": False, "diabetes": False},
        "medication_request": {
            "active_ingredient": "concorrina",
            "dose_mg": dose,
            "frequency_per_day": 1,
            "route": "oral",
        },
        "allergies": [],
        "conditions": [],
        "current_medications": [],
    }


def _race(client: TestClient, headers: dict, bodies: list[dict]) -> list[int]:
    barrier = threading.Barrier(len(bodies))
    results: list[tuple[int, dict]] = [None] * len(bodies)  # type: ignore[list-item]

    def worker(index: int, body: dict) -> None:
        barrier.wait()
        response = client.post(CDS_URL, headers=headers, json=body)
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}
        results[index] = (response.status_code, payload)

    threads = [threading.Thread(target=worker, args=(i, b)) for i, b in enumerate(bodies)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    return results  # type: ignore[return-value]


@pytest.mark.parametrize("same_content", [True, False])
def test_concurrent_same_key_is_exactly_once(
    create_test_user, auth_headers, db_session, same_content: bool
) -> None:
    create_test_user(email="race-pg@example.test", password="Admin@12345", role=UserRole.MEDICO)
    base_headers = auth_headers("race-pg@example.test", "Admin@12345")
    db_session.add(
        MedicationModel(
            brand_name="Concorrina",
            active_ingredient="concorrina",
            therapeutic_class="teste",
            max_daily_dose_mg=1000,
            allowed_routes=["oral"],
            contraindications=[],
        )
    )
    db_session.commit()
    client = TestClient(__import__("app.main", fromlist=["app"]).app, raise_server_exceptions=False)

    for round_index in range(ROUNDS):
        headers = base_headers | {"Idempotency-Key": f"race-{same_content}-{round_index}"}
        bodies = [_body(10), _body(10 if same_content else 20)]
        results = _race(client, headers, bodies)
        statuses = sorted(status for status, _ in results)

        assert 500 not in statuses, results
        if same_content:
            assert statuses == [200, 200]
            assert results[0][1] == results[1][1]  # resposta reproduzida idêntica
        else:
            assert statuses == [200, 409]

    db_session.expire_all()
    keys = db_session.scalar(select(func.count()).select_from(CDSIdempotencyModel))
    audits = db_session.scalar(
        select(func.count())
        .select_from(AuditEventModel)
        .where(AuditEventModel.action == "cds.prescription_check")
    )
    assert keys == ROUNDS
    assert audits == ROUNDS  # exatamente uma auditoria por chave, sem órfãs
