from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.database.models import AgentRunModel, EvidenceSourceModel, ResearchStudyModel, UserModel
from app.schemas.research_v093_schema import (
    AgentReviewRequest,
    AgentRunCreate,
    AgentStepRequest,
)
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256
from app.services.research_service import ResearchConflict, ResearchNotFound

AGENT_POLICY_VERSION = "bounded-research-agent-v1"
TEMPLATES = {
    "evidence_review": {
        "version": "1",
        "tools": [
            "search_evidence",
            "fetch_evidence_metadata",
            "get_evidence_source",
            "propose_evidence_shortlist",
        ],
        "checkpoint_after": "propose_evidence_shortlist",
    },
    "study_design": {
        "version": "1",
        "tools": [
            "lookup_terminology",
            "propose_concept_set",
            "validate_cohort_dsl",
            "propose_analysis_plan",
        ],
        "checkpoint_after": "propose_analysis_plan",
    },
}
FORBIDDEN_TOOLS = {
    "shell",
    "filesystem",
    "raw_http",
    "browser",
    "raw_sql",
    "db_mutation",
    "spawn_agent",
    "execute_research_query",
    "approve_protocol",
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
        study = self.db.get(ResearchStudyModel, payload.study_id)
        if study is None or study.institution_id != actor.institution_id:
            raise ResearchNotFound("Estudo nÃ£o encontrado.")
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
            budgets=payload.budget.model_dump()
            | {
                "data_classification": payload.data_classification,
                "source_allowlist": payload.source_ids,
                "provider_policy": "existing_ai_task_router_only",
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
            raise ResearchConflict("Estado do agent run nÃ£o permite novo tool call.")
        if payload.tool in FORBIDDEN_TOOLS or payload.tool not in run.allowed_tools:
            self._stop(run, "abstained", "tool_denied")
            self._audit(actor, run, "agent.tool.denied")
            return run
        usage = dict(run.usage)
        usage["steps"] += 1
        usage["tool_calls"] += 1
        usage["tokens"] += payload.token_usage
        usage["cost_usd"] = round(float(usage["cost_usd"]) + payload.cost_usd, 6)
        budget = run.budgets
        if (
            usage["steps"] > budget["max_steps"]
            or usage["tool_calls"] > budget["max_tool_calls"]
            or usage["tokens"] > budget["max_tokens"]
            or usage["cost_usd"] > budget["max_cost_usd"]
            or (datetime.now(UTC) - run.created_at).total_seconds()
            > budget["max_wall_time_seconds"]
        ):
            run.usage = usage
            self._stop(run, "abstained", "budget_exceeded")
            self._audit(actor, run, "agent.budget.exceeded")
            return run
        rendered = str(payload.output).casefold()
        injection_detected = any(marker in rendered for marker in INJECTION_MARKERS)
        steps = list(run.steps)
        steps.append(
            {
                "index": len(steps) + 1,
                "tool": payload.tool,
                "tool_version": "1",
                "input_hash": canonical_sha256({"run": run.id, "tool": payload.tool}),
                "output_hash": canonical_sha256(payload.output),
                "source_ids": run.source_ids,
                "status": "completed",
                "prompt_injection_detected": injection_detected,
                "authority_expanded": False,
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
        run.steps = steps
        run.usage = usage
        run.state = "running"
        run.updated_at = datetime.now(UTC)
        if payload.tool == TEMPLATES[run.template]["checkpoint_after"]:
            run.state = "waiting_human"
            run.proposal = {
                "status": "proposal_only",
                "content_hash": canonical_sha256(payload.output),
                "source_ids": run.source_ids,
                "payload": payload.output,
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
            raise ResearchConflict("Agent run nÃ£o estÃ¡ aguardando revisÃ£o humana.")
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
            raise ResearchConflict("Agent run jÃ¡ estÃ¡ em estado terminal.")
        run.proposal = {}
        run.cancelled_at = datetime.now(UTC)
        self._stop(run, "cancelled", "human_cancelled")
        self._audit(actor, run, "agent.run.cancel")
        return run

    def _owned(self, run_id: str, actor: UserModel) -> AgentRunModel:
        run = self.db.get(AgentRunModel, run_id)
        if run is None or run.institution_id != actor.institution_id:
            raise ResearchNotFound("Agent run nÃ£o encontrado.")
        return run

    @staticmethod
    def _stop(run: AgentRunModel, state: str, reason: str) -> None:
        run.state = state
        run.stop_reason = reason
        run.updated_at = datetime.now(UTC)

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
            },
        )
