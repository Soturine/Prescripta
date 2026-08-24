from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.database.models import AgentRunModel, EvidenceSourceModel, ResearchStudyModel, UserModel
from app.domain.user import Capability
from app.schemas.research_v093_schema import AgentReviewRequest, AgentRunCreate, AgentStepRequest
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256
from app.services.research_service import ResearchConflict, ResearchNotFound

AGENT_POLICY_VERSION = "bounded-research-agent-v2"
SERVER_BUDGET = {
    "max_steps": 4,
    "max_wall_time_seconds": 300,
    "max_tool_calls": 4,
    "max_tokens": 4_000,
    "max_cost_usd": 1.0,
}
TEMPLATES = {
    "evidence_review": {
        "version": "2",
        "tools": [
            "search_evidence",
            "fetch_evidence_metadata",
            "get_evidence_source",
            "propose_evidence_shortlist",
        ],
        "checkpoint_after": "propose_evidence_shortlist",
    },
    "study_design": {
        "version": "2",
        "tools": [
            "lookup_terminology",
            "propose_concept_set",
            "validate_cohort_dsl",
            "propose_analysis_plan",
        ],
        "checkpoint_after": "propose_analysis_plan",
    },
}
TERMINAL_STATES = {"completed", "rejected", "failed", "abstained", "cancelled"}
INJECTION_MARKERS = (
    "ignore previous instructions",
    "reveal secret",
    "call shell",
    "export patient data",
    "approve protocol",
)


class AgenticResearchService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: AgentRunCreate, actor: UserModel) -> AgentRunModel:
        self._study_in_scope(payload.study_id, actor)
        sources = [self.db.get(EvidenceSourceModel, source_id) for source_id in payload.source_ids]
        if any(
            source is None or source.institution_id != actor.institution_id for source in sources
        ):
            raise ResearchNotFound("Fonte fora do tenant ou inexistente.")
        template = TEMPLATES[payload.template]
        run = AgentRunModel(
            institution_id=actor.institution_id,
            study_id=payload.study_id,
            template=payload.template,
            template_version=template["version"],
            state="queued",
            goal_hash=canonical_sha256(payload.goal),
            budgets=SERVER_BUDGET
            | {
                "data_classification": payload.data_classification,
                "source_allowlist": payload.source_ids,
                "provider_policy": "existing_ai_task_router_only",
                "budget_authority": "server",
            },
            usage={"steps": 0, "tool_calls": 0, "tokens": 0, "cost_usd": 0.0},
            allowed_tools=template["tools"],
            steps=[],
            source_ids=payload.source_ids,
            proposal={},
            human_checkpoint={},
            created_by_user_id=actor.id,
            updated_at=datetime.now(UTC),
        )
        self.db.add(run)
        self.db.flush()
        self._audit(actor, run, "agent.run.create")
        return run

    def step(self, run_id: str, payload: AgentStepRequest, actor: UserModel) -> AgentRunModel:
        run = self._owned(run_id, actor)
        if run.state in TERMINAL_STATES or run.state == "waiting_human":
            raise ResearchConflict("Estado do agent run não permite novo tool call.")
        if any(step.get("idempotency_key") == payload.idempotency_key for step in run.steps):
            return run
        tool_index = len(run.steps)
        if tool_index >= len(run.allowed_tools):
            self._stop(run, "abstained", "workflow_exhausted")
            return run
        tool = run.allowed_tools[tool_index]
        if tool not in TEMPLATES[run.template]["tools"]:
            self._stop(run, "abstained", "tool_registry_violation")
            self._audit(actor, run, "agent.tool.denied")
            return run

        output = self._execute_registered_tool(run, tool)
        measured_tokens = len(str(output).split())
        usage = dict(run.usage)
        usage["steps"] += 1
        usage["tool_calls"] += 1
        usage["tokens"] += measured_tokens
        budget = run.budgets
        if (
            usage["steps"] > budget["max_steps"]
            or usage["tool_calls"] > budget["max_tool_calls"]
            or usage["tokens"] > budget["max_tokens"]
            or self._elapsed_seconds(run.created_at) > budget["max_wall_time_seconds"]
        ):
            run.usage = usage
            self._stop(run, "abstained", "budget_exceeded")
            self._audit(actor, run, "agent.budget.exceeded")
            return run

        steps = list(run.steps)
        steps.append(
            {
                "index": len(steps) + 1,
                "tool": tool,
                "tool_version": "2",
                "input_hash": canonical_sha256({"run": run.id, "tool": tool}),
                "output_hash": canonical_sha256(output),
                "idempotency_key": payload.idempotency_key,
                "measured_tokens": measured_tokens,
                "source_ids": run.source_ids,
                "status": "completed",
                "prompt_injection_detected": any(
                    marker in str(output).casefold() for marker in INJECTION_MARKERS
                ),
                "authority_expanded": False,
                "executed_by": "server_tool_registry",
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
        run.steps = steps
        run.usage = usage
        run.state = "running"
        run.updated_at = datetime.now(UTC)
        if tool == TEMPLATES[run.template]["checkpoint_after"]:
            run.state = "waiting_human"
            run.proposal = {
                "status": "proposal_only",
                "content_hash": canonical_sha256(output),
                "source_ids": run.source_ids,
                "payload": output,
            }
            run.human_checkpoint = {
                "status": "waiting",
                "actions": ["approve_as_draft", "reject", "request_revision", "cancel"],
            }
        self.db.flush()
        self._audit(actor, run, "agent.step.complete")
        return run

    def review(self, run_id: str, payload: AgentReviewRequest, actor: UserModel) -> AgentRunModel:
        run = self._owned(run_id, actor)
        if run.state != "waiting_human":
            raise ResearchConflict("Agent run não está aguardando revisão humana.")
        if payload.action == "cancel":
            return self.cancel(run_id, actor)
        state = {
            "approve_as_draft": "completed",
            "reject": "rejected",
            "request_revision": "running",
        }[payload.action]
        run.state = state
        run.reviewed_by_user_id = actor.id
        run.human_checkpoint = {
            "status": payload.action,
            "reviewer_user_id": actor.id,
            "note_hash": canonical_sha256(payload.note),
            "reviewed_at": datetime.now(UTC).isoformat(),
            "clinical_approval": False,
        }
        run.stop_reason = "human_approved_as_draft" if state == "completed" else payload.action
        run.updated_at = datetime.now(UTC)
        self.db.flush()
        self._audit(actor, run, "agent.checkpoint.review")
        return run

    def cancel(self, run_id: str, actor: UserModel) -> AgentRunModel:
        run = self._owned(run_id, actor)
        if run.state in TERMINAL_STATES:
            raise ResearchConflict("Agent run já está em estado terminal.")
        run.proposal = {}
        run.cancelled_at = datetime.now(UTC)
        self._stop(run, "cancelled", "human_cancelled")
        self._audit(actor, run, "agent.run.cancel")
        return run

    def _owned(self, run_id: str, actor: UserModel) -> AgentRunModel:
        run = self.db.get(AgentRunModel, run_id)
        if run is None or run.institution_id != actor.institution_id:
            raise ResearchNotFound("Agent run não encontrado.")
        self._study_in_scope(run.study_id, actor)
        return run

    def _study_in_scope(self, study_id: str, actor: UserModel) -> ResearchStudyModel:
        study = self.db.get(ResearchStudyModel, study_id)
        elevated = Capability.ACCESS_MANAGE.value in set(actor.capabilities or [])
        if (
            study is None
            or study.institution_id != actor.institution_id
            or (study.owner_user_id != actor.id and not elevated)
        ):
            raise ResearchNotFound("Estudo não encontrado.")
        return study

    def _execute_registered_tool(self, run: AgentRunModel, tool: str) -> dict:
        sources = [self.db.get(EvidenceSourceModel, source_id) for source_id in run.source_ids]
        source_refs = [source.id for source in sources if source is not None]
        handlers: dict[str, Callable[[], dict]] = {
            "search_evidence": lambda: {"candidate_source_ids": source_refs},
            "fetch_evidence_metadata": lambda: {"source_ids": source_refs, "metadata_only": True},
            "get_evidence_source": lambda: {"source_ids": source_refs, "content_loaded": False},
            "propose_evidence_shortlist": lambda: {
                "source_ids": source_refs,
                "recommendation_status": "human_review_required",
            },
            "lookup_terminology": lambda: {"status": "proposal_only", "matches": []},
            "propose_concept_set": lambda: {"status": "proposal_only", "concepts": []},
            "validate_cohort_dsl": lambda: {"status": "not_executed", "valid": None},
            "propose_analysis_plan": lambda: {"status": "proposal_only", "study_id": run.study_id},
        }
        handler = handlers.get(tool)
        if handler is None:
            raise ResearchConflict("Tool fora do registry server-side.")
        return handler()

    @staticmethod
    def _stop(run: AgentRunModel, state: str, reason: str) -> None:
        run.state = state
        run.stop_reason = reason
        run.updated_at = datetime.now(UTC)

    @staticmethod
    def _elapsed_seconds(created_at: datetime) -> float:
        normalized = created_at if created_at.tzinfo else created_at.replace(tzinfo=UTC)
        return (datetime.now(UTC) - normalized).total_seconds()

    def _audit(self, actor: UserModel, run: AgentRunModel, action: str) -> None:
        AuditService(self.db).record_action(
            user=actor,
            action=action,
            resource_type="agent_run",
            resource_id=run.id,
            status=run.state,
            details={
                "policy_version": AGENT_POLICY_VERSION,
                "template": run.template,
                "usage": run.usage,
                "allowed_tools": run.allowed_tools,
                "recursive_spawning": False,
                "raw_goal_persisted": False,
                "caller_supplied_tool_output_usage": False,
            },
        )
