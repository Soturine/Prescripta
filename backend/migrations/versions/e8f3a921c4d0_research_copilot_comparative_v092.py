"""Research Copilot v2 and comparative RWE foundations.

Revision ID: e8f3a921c4d0
Revises: d4b7c91a2e30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e8f3a921c4d0"
down_revision: str | None = "d4b7c91a2e30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("analysis_plans") as batch_op:
        batch_op.add_column(sa.Column("comparator_cohort_run_id", sa.String(length=36)))
        batch_op.add_column(
            sa.Column("exact_reference_set", sa.JSON(), nullable=False, server_default="{}")
        )
        batch_op.add_column(
            sa.Column("method_configuration", sa.JSON(), nullable=False, server_default="{}")
        )
        batch_op.add_column(
            sa.Column("causal_assumptions", sa.JSON(), nullable=False, server_default="{}")
        )
        batch_op.create_foreign_key(
            "fk_analysis_plans_comparator_cohort_run_id",
            "cohort_runs",
            ["comparator_cohort_run_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_analysis_plans_comparator_cohort_run_id", ["comparator_cohort_run_id"]
        )
    op.create_table(
        "research_comparison_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=100), nullable=False),
        sa.Column("analysis_plan_id", sa.String(length=36), nullable=True),
        sa.Column("exposed_cohort_run_id", sa.String(length=36), nullable=False),
        sa.Column("comparator_cohort_run_id", sa.String(length=36), nullable=False),
        sa.Column("data_quality_run_id", sa.String(length=36), nullable=False),
        sa.Column("exact_references", sa.JSON(), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("diagnostics", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("exposed_n", sa.Integer(), nullable=False),
        sa.Column("comparator_n", sa.Integer(), nullable=False),
        sa.Column("exposed_events", sa.Integer(), nullable=True),
        sa.Column("comparator_events", sa.Integer(), nullable=True),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("synthetic_only", sa.Boolean(), nullable=False),
        sa.Column("executed_by_user_id", sa.Integer(), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_plan_id"], ["analysis_plans.id"]),
        sa.ForeignKeyConstraint(["comparator_cohort_run_id"], ["cohort_runs.id"]),
        sa.ForeignKeyConstraint(["data_quality_run_id"], ["data_quality_runs.id"]),
        sa.ForeignKeyConstraint(["executed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["exposed_cohort_run_id"], ["cohort_runs.id"]),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "study_id",
        "institution_id",
        "analysis_plan_id",
        "exposed_cohort_run_id",
        "comparator_cohort_run_id",
        "data_quality_run_id",
        "input_hash",
        "content_hash",
        "status",
    ):
        op.create_index(
            f"ix_research_comparison_runs_{column}",
            "research_comparison_runs",
            [column],
        )
    with op.batch_alter_table("research_packages") as batch_op:
        batch_op.alter_column("analysis_run_id", existing_type=sa.String(length=36), nullable=True)
        batch_op.add_column(sa.Column("comparison_run_id", sa.String(length=36)))
        batch_op.create_foreign_key(
            "fk_research_packages_comparison_run_id",
            "research_comparison_runs",
            ["comparison_run_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_research_packages_comparison_run_id", ["comparison_run_id"]
        )
        batch_op.create_unique_constraint(
            "uq_research_packages_comparison_content",
            ["comparison_run_id", "content_hash"],
        )

    op.create_table(
        "medication_safety_research_drafts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=100), nullable=False),
        sa.Column("source_finding_id", sa.String(length=100), nullable=False),
        sa.Column("medication_candidate", sa.String(length=220), nullable=False),
        sa.Column("outcome_candidate", sa.String(length=220), nullable=False),
        sa.Column("suggested_question", sa.Text(), nullable=False),
        sa.Column("source_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("synthetic_only", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "study_id", "source_finding_id"),
    )
    for column in ("study_id", "institution_id", "source_finding_id"):
        op.create_index(
            f"ix_medication_safety_research_drafts_{column}",
            "medication_safety_research_drafts",
            [column],
        )

    op.create_table(
        "evidence_extractions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=100), nullable=False),
        sa.Column("schema_version", sa.String(length=80), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("extracted_fields", sa.JSON(), nullable=False),
        sa.Column("claims", sa.JSON(), nullable=False),
        sa.Column("prompt_injection_detected", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["evidence_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("source_id", "institution_id", "content_hash", "status"):
        op.create_index(
            f"ix_evidence_extractions_{column}", "evidence_extractions", [column]
        )

    op.create_table(
        "research_query_previews",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=100), nullable=False),
        sa.Column("dataset_snapshot_marker", sa.String(length=160), nullable=False),
        sa.Column("natural_language_question_hash", sa.String(length=64), nullable=False),
        sa.Column("normalized_query", sa.Text(), nullable=False),
        sa.Column("structured_interpretation", sa.JSON(), nullable=False),
        sa.Column("policy", sa.JSON(), nullable=False),
        sa.Column("estimated_cost", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("executed", sa.Boolean(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("study_id", "institution_id", "dataset_snapshot_marker", "status"):
        op.create_index(
            f"ix_research_query_previews_{column}", "research_query_previews", [column]
        )
    op.execute(
        "CREATE VIEW research_aggregate_comparisons AS "
        "SELECT id, study_id, institution_id, status, exposed_n, comparator_n, "
        "exposed_events, comparator_events, content_hash, executed_at "
        "FROM research_comparison_runs"
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS research_aggregate_comparisons")
    op.drop_table("research_query_previews")
    op.drop_table("evidence_extractions")
    op.drop_table("medication_safety_research_drafts")
    op.execute("DELETE FROM research_packages WHERE comparison_run_id IS NOT NULL")
    with op.batch_alter_table("research_packages") as batch_op:
        batch_op.drop_constraint("uq_research_packages_comparison_content", type_="unique")
        batch_op.drop_index("ix_research_packages_comparison_run_id")
        batch_op.drop_constraint(
            "fk_research_packages_comparison_run_id", type_="foreignkey"
        )
        batch_op.drop_column("comparison_run_id")
        batch_op.alter_column("analysis_run_id", existing_type=sa.String(length=36), nullable=False)
    op.drop_table("research_comparison_runs")
    with op.batch_alter_table("analysis_plans") as batch_op:
        batch_op.drop_index("ix_analysis_plans_comparator_cohort_run_id")
        batch_op.drop_constraint(
            "fk_analysis_plans_comparator_cohort_run_id", type_="foreignkey"
        )
        batch_op.drop_column("causal_assumptions")
        batch_op.drop_column("method_configuration")
        batch_op.drop_column("exact_reference_set")
        batch_op.drop_column("comparator_cohort_run_id")
