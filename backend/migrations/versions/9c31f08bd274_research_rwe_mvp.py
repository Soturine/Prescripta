"""research rwe mvp

Revision ID: 9c31f08bd274
Revises: 42168c1cc660
Create Date: 2026-08-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9c31f08bd274"
down_revision: str | Sequence[str] | None = "42168c1cc660"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("outcome_definitions", sa.Column("reviewed_at", sa.DateTime(timezone=True)))
    op.add_column("analysis_plans", sa.Column("cohort_run_id", sa.String(36)))
    op.add_column(
        "analysis_plans", sa.Column("variables", sa.JSON(), nullable=False, server_default="[]")
    )
    op.add_column(
        "analysis_plans", sa.Column("steps", sa.JSON(), nullable=False, server_default="[]")
    )
    op.add_column(
        "analysis_plans",
        sa.Column("output_specification", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "analysis_plans", sa.Column("source_refs", sa.JSON(), nullable=False, server_default="[]")
    )
    op.add_column("analysis_plans", sa.Column("reviewed_at", sa.DateTime(timezone=True)))
    op.add_column(
        "analysis_plans",
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_foreign_key(
        "fk_analysis_plans_cohort_run", "analysis_plans", "cohort_runs", ["cohort_run_id"], ["id"]
    )
    op.create_index(op.f("ix_analysis_plans_cohort_run_id"), "analysis_plans", ["cohort_run_id"])

    op.create_table(
        "data_quality_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.String(100), nullable=False),
        sa.Column("study_id", sa.String(36)),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("executed_by_user_id", sa.Integer(), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"]),
        sa.ForeignKeyConstraint(["executed_by_user_id"], ["users.id"]),
    )
    for column in ("institution_id", "study_id", "status", "content_hash"):
        op.create_index(op.f(f"ix_data_quality_runs_{column}"), "data_quality_runs", [column])
    op.add_column("data_quality_findings", sa.Column("run_id", sa.String(36)))
    op.create_foreign_key(
        "fk_data_quality_findings_run",
        "data_quality_findings",
        "data_quality_runs",
        ["run_id"],
        ["id"],
    )
    op.create_index(op.f("ix_data_quality_findings_run_id"), "data_quality_findings", ["run_id"])

    op.create_table(
        "research_analysis_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("study_id", sa.String(36), nullable=False),
        sa.Column("analysis_plan_id", sa.String(36), nullable=False),
        sa.Column("cohort_run_id", sa.String(36), nullable=False),
        sa.Column("institution_id", sa.String(100), nullable=False),
        sa.Column("data_snapshot_marker", sa.String(160), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("executed_by_user_id", sa.Integer(), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"]),
        sa.ForeignKeyConstraint(["analysis_plan_id"], ["analysis_plans.id"]),
        sa.ForeignKeyConstraint(["cohort_run_id"], ["cohort_runs.id"]),
        sa.ForeignKeyConstraint(["executed_by_user_id"], ["users.id"]),
    )
    for column in (
        "study_id",
        "analysis_plan_id",
        "cohort_run_id",
        "institution_id",
        "status",
        "content_hash",
    ):
        op.create_index(
            op.f(f"ix_research_analysis_runs_{column}"), "research_analysis_runs", [column]
        )

    op.create_table(
        "research_packages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("study_id", sa.String(36), nullable=False),
        sa.Column("analysis_run_id", sa.String(36), nullable=False),
        sa.Column("institution_id", sa.String(100), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("files", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("aggregate_only", sa.Boolean(), nullable=False),
        sa.Column("exported_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"]),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["research_analysis_runs.id"]),
        sa.ForeignKeyConstraint(["exported_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("analysis_run_id", "content_hash"),
    )
    for column in ("study_id", "analysis_run_id", "institution_id", "content_hash"):
        op.create_index(op.f(f"ix_research_packages_{column}"), "research_packages", [column])


def downgrade() -> None:
    for column in ("content_hash", "institution_id", "analysis_run_id", "study_id"):
        op.drop_index(op.f(f"ix_research_packages_{column}"), table_name="research_packages")
    op.drop_table("research_packages")
    for column in (
        "content_hash",
        "status",
        "institution_id",
        "cohort_run_id",
        "analysis_plan_id",
        "study_id",
    ):
        op.drop_index(
            op.f(f"ix_research_analysis_runs_{column}"), table_name="research_analysis_runs"
        )
    op.drop_table("research_analysis_runs")
    op.drop_index(op.f("ix_data_quality_findings_run_id"), table_name="data_quality_findings")
    op.drop_constraint("fk_data_quality_findings_run", "data_quality_findings", type_="foreignkey")
    op.drop_column("data_quality_findings", "run_id")
    for column in ("content_hash", "status", "study_id", "institution_id"):
        op.drop_index(op.f(f"ix_data_quality_runs_{column}"), table_name="data_quality_runs")
    op.drop_table("data_quality_runs")
    op.drop_index(op.f("ix_analysis_plans_cohort_run_id"), table_name="analysis_plans")
    op.drop_constraint("fk_analysis_plans_cohort_run", "analysis_plans", type_="foreignkey")
    for column in (
        "created_at",
        "reviewed_at",
        "source_refs",
        "output_specification",
        "steps",
        "variables",
        "cohort_run_id",
    ):
        op.drop_column("analysis_plans", column)
    op.drop_column("outcome_definitions", "reviewed_at")
