from __future__ import annotations

import json
from datetime import datetime

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.models import ResearchStudyModel
from app.domain.user import UserRole
from app.schemas.research_v093_schema import (
    AgentReviewRequest,
    AgentRunCreate,
    AgentStepRequest,
    EvidenceSearchPlanCreate,
)
from app.services.agentic_research_service import AgenticResearchService
from app.services.evidence_acquisition_service import EvidenceAcquisitionService
from app.services.research_service import ResearchConflict, ResearchNotFound


class MockOutbound:
    def __init__(self, payloads: list[tuple[int, object] | tuple[int, object, str]]) -> None:
        self.payloads = list(payloads)
        self.calls: list[dict] = []

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        self.calls.append({"method": method, "url": url, **kwargs})
        item = self.payloads.pop(0)
        status, body = item[:2]
        content_type = item[2] if len(item) == 3 else "application/json"
        content = body if isinstance(body, bytes) else json.dumps(body).encode()
        return httpx.Response(
            status,
            headers={"content-type": content_type},
            content=content,
            request=httpx.Request(method, url),
        )


def _study(db: Session, actor, slug: str = "v093") -> ResearchStudyModel:
    study = ResearchStudyModel(
        institution_id=actor.institution_id,
        title="Synthetic v0.9.3 study",
        slug=slug,
        research_question="What synthetic association is observed?",
        objective="Demonstrate governed research workflows.",
        design="retrospective_cohort",
        owner_user_id=actor.id,
        demo_only=True,
        data_source_classification="synthetic",
    )
    db.add(study)
    db.flush()
    return study


def test_pubmed_plan_is_reproducible_persisted_and_metadata_only(
    monkeypatch: pytest.MonkeyPatch, db_session: Session, create_test_user
) -> None:
    monkeypatch.setenv("PRESCRIPTA_EVIDENCE_CONTACT_EMAIL", "research@example.test")
    actor = create_test_user(email="evidence-v093@example.test", role=UserRole.PESQUISADOR)
    study = _study(db_session, actor)
    mock = MockOutbound(
        [
            (200, {"esearchresult": {"idlist": ["123"]}}),
            (
                200,
                {
                    "result": {
                        "123": {
                            "title": "Synthetic evidence",
                            "pubdate": "2026",
                            "authors": [{"name": "Doe J"}],
                            "articleids": [
                                {"idtype": "doi", "value": "10.1000/demo"},
                                {"idtype": "pmcid", "value": "PMC123"},
                            ],
                        }
                    }
                },
            ),
            (
                200,
                b"<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID>"
                b"</MedlineCitation><PubmedData><ArticleIdList>"
                b'<ArticleId IdType="doi">10.1000/demo</ArticleId>'
                b'<ArticleId IdType="pmc">PMC123</ArticleId>'
                b"</ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>",
                "application/xml",
            ),
        ]
    )
    service = EvidenceAcquisitionService(db_session, client=mock, sleeper=lambda _: None)
    plan = service.create_plan(
        EvidenceSearchPlanCreate(
            study_id=study.id,
            providers=["pubmed"],
            canonical_query="synthetic medication safety",
            filters={"limit": 10},
        ),
        actor,
    )
    result = service.execute(plan.id, actor)
    assert result.status == "executed"
    assert result.result_count == 1
    assert result.identifiers[0]["doi"] == "10.1000/demo"
    assert result.identifiers[0]["pmcid"] == "PMC123"
    assert result.identifiers[0]["rights_status"] == "metadata_only"
    assert all(call["params"]["tool"] == "Prescripta" for call in mock.calls)
    assert all(call["params"]["email"] == "research@example.test" for call in mock.calls)
    assert "api_key" not in result.identifiers[0]
    assert mock.calls[-1]["url"].endswith("efetch.fcgi")


def test_provider_retry_openalex_configuration_and_malicious_xml(
    monkeypatch: pytest.MonkeyPatch, db_session: Session
) -> None:
    delays: list[float] = []
    retrying = MockOutbound(
        [
            (429, {}),
            (200, {"message": {"items": []}}),
        ]
    )
    service = EvidenceAcquisitionService(db_session, client=retrying, sleeper=delays.append)
    results, metadata = service._crossref("demo", "research@example.test", {"limit": 2})
    assert results == []
    assert metadata["polite_pool"] is True
    assert len(retrying.calls) == 2
    assert 0.3 in delays
    assert any(delay >= 0.5 for delay in delays)

    monkeypatch.setenv("OPENALEX_API_KEY", "configured-secret")
    openalex = MockOutbound(
        [
            (
                200,
                {
                    "meta": {"cost_usd": 0.001},
                    "results": [
                        {
                            "id": "https://openalex.org/W1",
                            "display_name": "Synthetic OpenAlex work",
                            "doi": "https://doi.org/10.1000/openalex",
                            "publication_year": 2026,
                        }
                    ],
                },
            )
        ]
    )
    service = EvidenceAcquisitionService(db_session, client=openalex)
    results, metadata = service._search_provider("openalex", "demo", {"limit": 1})
    assert results[0]["openalex_id"] == "https://openalex.org/W1"
    assert metadata["credits_reported"] == 0.001
    assert "api_key" not in json.dumps(results)

    malicious = MockOutbound(
        [(200, b'<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>', "text/xml")]
    )
    service = EvidenceAcquisitionService(db_session, client=malicious)
    with pytest.raises(ValueError, match="DTD and entities"):
        service._xml_request("https://eutils.ncbi.nlm.nih.gov/test", {})


def test_openalex_without_key_degrades_and_dedupe_preserves_ambiguity(
    monkeypatch: pytest.MonkeyPatch, db_session: Session, create_test_user
) -> None:
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    actor = create_test_user(email="openalex-v093@example.test", role=UserRole.PESQUISADOR)
    study = _study(db_session, actor, "openalex")
    service = EvidenceAcquisitionService(db_session, client=MockOutbound([]))
    plan = service.create_plan(
        EvidenceSearchPlanCreate(
            study_id=study.id, providers=["openalex"], canonical_query="demo evidence"
        ),
        actor,
    )
    assert service.execute(plan.id, actor).result_count == 0
    items = [
        service._normalized(provider="pubmed", title="Same title", year="2026", doi=None),
        service._normalized(provider="crossref", title=" Same   Title ", year="2026", doi=None),
    ]
    deduped = service.deduplicate(items)
    assert len(deduped) == 2
    assert deduped[1]["duplicate_status"] == "needs_review"


def test_evidence_metadata_cache_is_real_bounded_and_credential_free(db_session: Session) -> None:
    mock = MockOutbound([(200, {"message": {"items": []}})])
    service = EvidenceAcquisitionService(db_session, client=mock, sleeper=lambda _: None)
    first = service._crossref("cache-contract-unique", "cache@example.test", {"limit": 1})
    second = service._crossref("cache-contract-unique", "cache@example.test", {"limit": 1})
    assert first[0] == second[0] == []
    assert len(mock.calls) == 1
    assert second[1]["cache"] == "process_ttl_900s"
    assert second[1]["cache_hits"] == 1


def test_agent_state_machine_checkpoint_injection_and_cancel(
    db_session: Session, create_test_user
) -> None:
    actor = create_test_user(email="agent-v093@example.test", role=UserRole.PESQUISADOR)
    study = _study(db_session, actor, "agent")
    service = AgenticResearchService(db_session)
    run = service.create(
        AgentRunCreate(
            study_id=study.id,
            template="evidence_review",
            goal="Review registered public evidence",
        ),
        actor,
    )
    assert run.state == "queued"
    run = service.step(run.id, AgentStepRequest(idempotency_key="agent-step-1"), actor)
    assert run.state == "running"
    assert run.steps[0]["tool"] == "search_evidence"
    assert run.steps[0]["executed_by"] == "server_tool_registry"
    assert run.steps[0]["prompt_injection_detected"] is False
    assert run.steps[0]["authority_expanded"] is False
    assert service.step(run.id, AgentStepRequest(idempotency_key="agent-step-1"), actor) is run
    for index in range(2, 5):
        run = service.step(run.id, AgentStepRequest(idempotency_key=f"agent-step-{index}"), actor)
    assert run.state == "waiting_human"
    assert run.proposal["status"] == "proposal_only"
    with pytest.raises(ResearchConflict):
        service.step(run.id, AgentStepRequest(idempotency_key="agent-step-5"), actor)
    run = service.review(
        run.id, AgentReviewRequest(action="approve_as_draft", note="demo review"), actor
    )
    assert run.state == "completed"
    assert run.human_checkpoint["clinical_approval"] is False

    cancellable = service.create(
        AgentRunCreate(study_id=study.id, template="study_design", goal="Draft study"), actor
    )
    assert service.cancel(cancellable.id, actor).state == "cancelled"
    with pytest.raises(ResearchConflict):
        service.step(
            cancellable.id,
            AgentStepRequest(idempotency_key="cancelled-step"),
            actor,
        )


def test_agent_denies_tools_budgets_recursion_and_cross_tenant(
    db_session: Session, create_test_user
) -> None:
    actor = create_test_user(email="agent-owner@example.test", role=UserRole.PESQUISADOR)
    outsider = create_test_user(
        email="agent-outsider@example.test",
        role=UserRole.PESQUISADOR,
        institution_id="other",
    )
    same_tenant_non_owner = create_test_user(
        email="agent-non-owner@example.test", role=UserRole.PESQUISADOR
    )
    study = _study(db_session, actor, "agent-deny")
    service = AgenticResearchService(db_session)
    denied = service.create(
        AgentRunCreate(study_id=study.id, template="study_design", goal="Try recursion"), actor
    )
    denied.allowed_tools = ["spawn_agent"]
    assert (
        service.step(denied.id, AgentStepRequest(idempotency_key="denied-step"), actor).stop_reason
        == "tool_registry_violation"
    )
    with pytest.raises(ResearchNotFound):
        service.cancel(denied.id, outsider)
    with pytest.raises(ResearchNotFound):
        service.cancel(denied.id, same_tenant_non_owner)

    limited = service.create(
        AgentRunCreate(
            study_id=study.id,
            template="study_design",
            goal="Bounded draft",
        ),
        actor,
    )
    limited.budgets = limited.budgets | {"max_tokens": 0}
    result = service.step(
        limited.id,
        AgentStepRequest(idempotency_key="limited-step"),
        actor,
    )
    assert result.state == "abstained"
    assert result.stop_reason == "budget_exceeded"
    assert service._elapsed_seconds(datetime.now()) >= 0


def test_agent_v2_rejects_caller_authority_fields() -> None:
    with pytest.raises(ValidationError):
        AgentStepRequest.model_validate(
            {
                "idempotency_key": "authority-attempt",
                "tool": "spawn_agent",
                "output": {"approved": True},
                "token_usage": 1,
                "cost_usd": 1,
            }
        )
    with pytest.raises(ValidationError):
        AgentRunCreate.model_validate(
            {
                "study_id": "00000000-0000-0000-0000-000000000000",
                "template": "study_design",
                "goal": "Caller budget attempt",
                "budget": {"max_steps": 99},
            }
        )
