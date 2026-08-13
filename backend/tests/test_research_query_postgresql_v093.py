from __future__ import annotations

import os
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.schemas.research_v092_schema import ResearchQueryPreviewRequest
from app.services.research_query_service import ResearchQueryService


@pytest.fixture
def postgres_session() -> Session:
    url = os.getenv("PRESCRIPTA_DATABASE_URL", "")
    if not url.startswith("postgresql"):
        pytest.skip("PostgreSQL integration test")
    engine = create_engine(url)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _payload() -> ResearchQueryPreviewRequest:
    return ResearchQueryPreviewRequest(
        study_id="11111111-1111-1111-1111-111111111111",
        dataset_snapshot_marker="synthetic-v093",
        natural_language_question="Quantas comparacoes agregadas existem?",
        proposed_sql="SELECT count(id) FROM research_aggregate_comparisons",
        purpose="PostgreSQL planner integration test",
    )


def test_postgresql_explain_json_is_authoritative(postgres_session: Session) -> None:
    service = ResearchQueryService(postgres_session)
    payload = _payload()
    query, _, _ = service._validate_and_scope(payload)
    actor = SimpleNamespace(institution_id="institution-test")

    plan = service._planner_preview(query, payload, actor)  # type: ignore[arg-type]

    assert plan["status"] == "accepted"
    assert plan["planner_total_cost"] >= 0
    assert plan["plan_nodes"] >= 1
    assert plan["cost_unit"] == "relative PostgreSQL planner units, not milliseconds"


def test_postgresql_transaction_rejects_database_write(postgres_session: Session) -> None:
    service = ResearchQueryService(postgres_session)

    with pytest.raises(DBAPIError), service._postgres_read_only(3000, 500) as connection:
        connection.execute(text("UPDATE research_studies SET title = title"))
