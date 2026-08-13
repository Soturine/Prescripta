"""Advanced research evidence and bounded agents v0.9.3.

Revision ID: f3a91c7d2b40
Revises: e8f3a921c4d0
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3a91c7d2b40"
down_revision: str | None = "e8f3a921c4d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evidence_search_plans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=100), nullable=False),
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("providers", sa.JSON(), nullable=False),
        sa.Column("canonical_query", sa.Text(), nullable=False),
        sa.Column("provider_queries", sa.JSON(), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("identifiers", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Integer()),
        sa.Column("executed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "study_id", "version"),
    )
    for column in ("institution_id", "study_id", "status", "content_hash"):
        op.create_index(f"ix_evidence_search_plans_{column}", "evidence_search_plans", [column])

    op.create_table(
        "evidence_acquisition_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("provider_metadata", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["plan_id"], ["evidence_search_plans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("plan_id", "institution_id", "provider", "status", "content_hash"):
        op.create_index(
            f"ix_evidence_acquisition_runs_{column}", "evidence_acquisition_runs", [column]
        )

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=100), nullable=False),
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("template", sa.String(length=80), nullable=False),
        sa.Column("template_version", sa.String(length=40), nullable=False),
        sa.Column("state", sa.String(length=40), nullable=False),
        sa.Column("goal_hash", sa.String(length=64), nullable=False),
        sa.Column("budgets", sa.JSON(), nullable=False),
        sa.Column("usage", sa.JSON(), nullable=False),
        sa.Column("allowed_tools", sa.JSON(), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("source_ids", sa.JSON(), nullable=False),
        sa.Column("proposal", sa.JSON(), nullable=False),
        sa.Column("human_checkpoint", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(length=80)),
        sa.Column("model", sa.String(length=160)),
        sa.Column("stop_reason", sa.String(length=120)),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("institution_id", "study_id", "template", "state"):
        op.create_index(f"ix_agent_runs_{column}", "agent_runs", [column])


def downgrade() -> None:
    op.drop_table("agent_runs")
    op.drop_table("evidence_acquisition_runs")
    op.drop_table("evidence_search_plans")
