from __future__ import annotations

import os
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlglot import exp, parse
from sqlglot.errors import ParseError

from app.database.models import ResearchQueryPreviewModel, ResearchStudyModel, UserModel
from app.schemas.research_v092_schema import ResearchQueryPreviewRequest
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256
from app.services.research_service import ResearchConflict, ResearchNotFound

QUERY_POLICY_VERSION = "research-query-policy-v1"
APPROVED_VIEW = "research_aggregate_comparisons"
ALLOWED_COLUMNS = {
    "id",
    "study_id",
    "institution_id",
    "dataset_snapshot_marker",
    "status",
    "exposed_n",
    "comparator_n",
    "exposed_events",
    "comparator_events",
    "content_hash",
    "executed_at",
}
ALLOWED_FUNCTIONS = {"count", "sum", "avg", "min", "max"}
DENIED_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
    exp.Create,
    exp.Alter,
    exp.Drop,
    exp.TruncateTable,
    exp.Command,
    exp.Transaction,
    exp.Union,
    exp.Intersect,
    exp.Except,
)


class ResearchQueryPolicyError(ValueError):
    pass


class ResearchQueryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def enabled() -> bool:
        return os.getenv("PRESCRIPTA_RESEARCH_QUERY_ASSISTANT_ENABLED", "false").lower() == "true"

    def preview(
        self, payload: ResearchQueryPreviewRequest, actor: UserModel
    ) -> ResearchQueryPreviewModel:
        study = self.db.get(ResearchStudyModel, payload.study_id)
        if study is None or study.institution_id != actor.institution_id:
            raise ResearchNotFound("Estudo não encontrado.")
        query, interpretation, estimated_cost = self._validate_and_scope(payload)
        enabled = self.enabled()
        policy = {
            "version": QUERY_POLICY_VERSION,
            "approved_views": [APPROVED_VIEW],
            "institution_scope": actor.institution_id,
            "study_scope": payload.study_id,
            "snapshot_scope": payload.dataset_snapshot_marker,
            "row_limit": payload.row_limit,
            "timeout_ms": payload.timeout_ms,
            "cost_budget": payload.cost_budget,
            "aggregate_only": True,
            "small_cells": "event fields are NULL when source run was suppressed",
            "human_execution_required": True,
        }
        preview = ResearchQueryPreviewModel(
            study_id=payload.study_id,
            institution_id=actor.institution_id,
            dataset_snapshot_marker=payload.dataset_snapshot_marker,
            natural_language_question_hash=canonical_sha256(payload.natural_language_question),
            normalized_query=query,
            structured_interpretation=interpretation,
            policy=policy,
            estimated_cost=estimated_cost,
            status="ready_for_human_execution" if enabled else "disabled_by_default",
            enabled=enabled,
            executed=False,
            result={},
            created_by_user_id=actor.id,
        )
        self.db.add(preview)
        self.db.flush()
        self._audit(actor, preview, "research.query.preview", preview.status)
        return preview

    def execute(self, preview_id: str, actor: UserModel) -> ResearchQueryPreviewModel:
        preview = self.db.get(ResearchQueryPreviewModel, preview_id)
        if preview is None or preview.institution_id != actor.institution_id:
            raise ResearchNotFound("Query preview não encontrado.")
        if not preview.enabled or not self.enabled():
            raise ResearchConflict("Research Query Assistant está desabilitado por default.")
        if preview.executed:
            raise ResearchConflict("Preview já foi executado; gere um novo preview.")
        timeout_ms = int(preview.policy["timeout_ms"])
        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            self.db.execute(
                text("SELECT set_config('statement_timeout', :timeout, true)"),
                {"timeout": f"{timeout_ms}ms"},
            )
        rows = self.db.execute(
            text(preview.normalized_query),
            {
                "institution_id": actor.institution_id,
                "study_id": preview.study_id,
                "dataset_snapshot_marker": preview.dataset_snapshot_marker,
            },
        ).mappings().all()
        bounded = [dict(row) for row in rows[: int(preview.policy["row_limit"])]]
        serialized_size = len(str(bounded).encode("utf-8"))
        if serialized_size > 200_000:
            raise ResearchConflict("Resultado excede o byte limit da policy.")
        preview.result = {
            "rows": bounded,
            "row_count": len(bounded),
            "aggregate_only": True,
            "small_cell_suppression_applied_at_source": True,
        }
        preview.executed = True
        preview.status = "executed_aggregate"
        self.db.flush()
        self._audit(actor, preview, "research.query.execute", preview.status)
        return preview

    def _validate_and_scope(
        self, payload: ResearchQueryPreviewRequest
    ) -> tuple[str, dict[str, Any], int]:
        try:
            statements = parse(payload.proposed_sql, read="postgres")
        except ParseError as exc:
            raise ResearchQueryPolicyError("SQL não pôde ser convertido em AST.") from exc
        if len(statements) != 1:
            raise ResearchQueryPolicyError("Multiple statements são bloqueados.")
        statement = statements[0]
        if not isinstance(statement, exp.Select):
            raise ResearchQueryPolicyError("Somente SELECT é permitido.")
        for node in statement.walk():
            if isinstance(node, DENIED_NODES):
                raise ResearchQueryPolicyError(
                    f"Nó AST bloqueado pela policy: {type(node).__name__}."
                )
        tables = list(statement.find_all(exp.Table))
        if not tables or any(
            table.name != APPROVED_VIEW or table.db or table.catalog for table in tables
        ):
            raise ResearchQueryPolicyError("Query deve usar somente approved research views.")
        if len(tables) != 1:
            raise ResearchQueryPolicyError("Joins não são permitidos no piloto v0.9.2.")
        columns = {column.name for column in statement.find_all(exp.Column)}
        if columns - ALLOWED_COLUMNS:
            raise ResearchQueryPolicyError("Query contém coluna não aprovada.")
        functions = {
            function.sql_name().lower()
            for function in statement.find_all(exp.Func)
        }
        if functions - ALLOWED_FUNCTIONS:
            raise ResearchQueryPolicyError("Query contém função não aprovada.")
        node_count = sum(1 for _ in statement.walk())
        estimated_cost = node_count * payload.row_limit
        if estimated_cost > payload.cost_budget:
            raise ResearchQueryPolicyError("Estimated cost excede o budget da policy.")
        scope = exp.and_(
            exp.column("institution_id").eq(exp.Placeholder(this="institution_id")),
            exp.column("study_id").eq(exp.Placeholder(this="study_id")),
            exp.column("dataset_snapshot_marker").eq(
                exp.Placeholder(this="dataset_snapshot_marker")
            ),
        )
        scoped = statement.copy().where(scope, append=True).limit(payload.row_limit)
        # Keep SQLAlchemy-style named placeholders; the same validated query runs on
        # PostgreSQL and on the bounded SQLite test fixture.
        normalized = scoped.sql()
        return (
            normalized,
            {
                "statement": "select",
                "views": [APPROVED_VIEW],
                "columns": sorted(columns),
                "functions": sorted(functions),
                "tenant_scope_injected": True,
                "study_scope_injected": True,
                "snapshot_scope_injected": True,
                "read_only": True,
            },
            estimated_cost,
        )

    def _audit(
        self,
        actor: UserModel,
        preview: ResearchQueryPreviewModel,
        action: str,
        status: str,
    ) -> None:
        AuditService(self.db).record_action(
            user=actor,
            action=action,
            resource_type="research_query_preview",
            resource_id=preview.id,
            status=status,
            details={
                "policy_version": QUERY_POLICY_VERSION,
                "study_id": preview.study_id,
                "estimated_cost": preview.estimated_cost,
                "raw_question_persisted": False,
                "patient_rows": False,
            },
        )
