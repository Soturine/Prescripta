"""terminology and OMOP v0.9.1

Revision ID: d4b7c91a2e30
Revises: 9c31f08bd274
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4b7c91a2e30"
down_revision: str | Sequence[str] | None = "9c31f08bd274"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _index(table: str, *columns: str) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def _legacy_dq_unique_name() -> str:
    expected = {"institution_id", "rule", "resource_type", "resource_id", "field"}
    constraints = sa.inspect(op.get_bind()).get_unique_constraints(
        "data_quality_findings"
    )
    for constraint in constraints:
        if set(constraint.get("column_names") or []) == expected:
            return str(
                constraint.get("name")
                or "uq_data_quality_findings_institution_id"
            )
    raise RuntimeError("Legacy Data Quality unique constraint was not found.")


def upgrade() -> None:
    with op.batch_alter_table("data_quality_runs") as batch:
        batch.add_column(sa.Column("cohort_run_id", sa.String(36)))
        batch.add_column(sa.Column("data_snapshot_marker", sa.String(160)))
        batch.add_column(sa.Column("data_snapshot_hash", sa.String(64)))
        batch.add_column(
            sa.Column("terminology_snapshot", sa.JSON(), nullable=False, server_default="{}")
        )
        batch.add_column(
            sa.Column(
                "ruleset_version",
                sa.String(80),
                nullable=False,
                server_default="prescripta-data-quality-v2",
            )
        )
        batch.add_column(
            sa.Column(
                "scope_status",
                sa.String(40),
                nullable=False,
                server_default="legacy_unscoped",
            )
        )
        batch.create_foreign_key(
            "fk_data_quality_runs_cohort_run", "cohort_runs", ["cohort_run_id"], ["id"]
        )
        for column in (
            "cohort_run_id",
            "data_snapshot_marker",
            "data_snapshot_hash",
            "scope_status",
        ):
            batch.create_index(op.f(f"ix_data_quality_runs_{column}"), [column])

    legacy_dq_unique = _legacy_dq_unique_name()
    with op.batch_alter_table(
        "data_quality_findings",
        naming_convention={"uq": "uq_%(table_name)s_%(column_0_name)s"},
    ) as batch:
        batch.drop_constraint(legacy_dq_unique, type_="unique")
        batch.create_unique_constraint(
            "uq_data_quality_findings_run_scope",
            ["run_id", "rule", "resource_type", "resource_id", "field"],
        )

    with op.batch_alter_table("analysis_plans") as batch:
        batch.add_column(sa.Column("data_quality_run_id", sa.String(36)))
        batch.create_foreign_key(
            "fk_analysis_plans_data_quality_run",
            "data_quality_runs",
            ["data_quality_run_id"],
            ["id"],
        )
        batch.create_index(op.f("ix_analysis_plans_data_quality_run_id"), ["data_quality_run_id"])

    with op.batch_alter_table("research_analysis_runs") as batch:
        batch.add_column(sa.Column("data_quality_run_id", sa.String(36)))
        batch.create_foreign_key(
            "fk_research_analysis_runs_data_quality_run",
            "data_quality_runs",
            ["data_quality_run_id"],
            ["id"],
        )
        batch.create_index(
            op.f("ix_research_analysis_runs_data_quality_run_id"), ["data_quality_run_id"]
        )

    op.create_table(
        "analysis_plan_outcomes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("analysis_plan_id", sa.String(36), nullable=False),
        sa.Column("outcome_version_id", sa.String(36), nullable=False),
        sa.Column("outcome_logical_name", sa.String(220), nullable=False),
        sa.Column("outcome_version", sa.Integer(), nullable=False),
        sa.Column("outcome_hash", sa.String(64), nullable=False),
        sa.Column("review_status", sa.String(40), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Integer()),
        sa.Column("terminology_refs", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_plan_id"], ["analysis_plans.id"]),
        sa.ForeignKeyConstraint(["outcome_version_id"], ["outcome_definitions.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("analysis_plan_id", "outcome_version_id"),
    )
    _index("analysis_plan_outcomes", "analysis_plan_id", "outcome_version_id")

    op.create_table(
        "analysis_run_outcomes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("analysis_run_id", sa.String(36), nullable=False),
        sa.Column("outcome_version_id", sa.String(36), nullable=False),
        sa.Column("outcome_logical_name", sa.String(220), nullable=False),
        sa.Column("outcome_version", sa.Integer(), nullable=False),
        sa.Column("outcome_hash", sa.String(64), nullable=False),
        sa.Column("review_status", sa.String(40), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Integer()),
        sa.Column("terminology_refs", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["research_analysis_runs.id"]),
        sa.ForeignKeyConstraint(["outcome_version_id"], ["outcome_definitions.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("analysis_run_id", "outcome_version_id"),
    )
    _index("analysis_run_outcomes", "analysis_run_id", "outcome_version_id")

    op.create_table(
        "terminology_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.String(100), nullable=False),
        sa.Column("canonical_system", sa.String(120), nullable=False),
        sa.Column("public_name", sa.String(220), nullable=False),
        sa.Column("steward", sa.String(220), nullable=False),
        sa.Column("family", sa.String(80), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("jurisdiction", sa.String(80)),
        sa.Column("locale", sa.String(40)),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("institution_id", "canonical_system"),
    )
    _index("terminology_sources", "institution_id", "canonical_system", "family")

    op.create_table(
        "terminology_releases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.Column("institution_id", sa.String(100), nullable=False),
        sa.Column("edition", sa.String(120), nullable=False),
        sa.Column("version", sa.String(120), nullable=False),
        sa.Column("release_date", sa.Date()),
        sa.Column("imported_at", sa.DateTime(timezone=True)),
        sa.Column("source_checksum", sa.String(64), nullable=False),
        sa.Column("source_artifact_name", sa.String(240), nullable=False),
        sa.Column("license_identifier", sa.String(120), nullable=False),
        sa.Column("license_name", sa.String(240), nullable=False),
        sa.Column("license_reference", sa.String(500), nullable=False),
        sa.Column("redistributable", sa.Boolean(), nullable=False),
        sa.Column("requires_license", sa.Boolean(), nullable=False),
        sa.Column("requires_login", sa.Boolean(), nullable=False),
        sa.Column("requires_attribution", sa.Boolean(), nullable=False),
        sa.Column("commercial_redistribution_allowed", sa.Boolean()),
        sa.Column("license_note", sa.Text(), nullable=False),
        sa.Column("license_status", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("imported_by_user_id", sa.Integer()),
        sa.Column("import_run_id", sa.String(36)),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["terminology_sources.id"]),
        sa.ForeignKeyConstraint(["imported_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("source_id", "edition", "version", "source_checksum"),
    )
    _index(
        "terminology_releases",
        "source_id",
        "institution_id",
        "version",
        "source_checksum",
        "license_status",
        "import_run_id",
        "content_hash",
    )

    op.create_table(
        "terminology_concepts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("release_id", sa.String(36), nullable=False),
        sa.Column("institution_id", sa.String(100), nullable=False),
        sa.Column("source_system", sa.String(120), nullable=False),
        sa.Column("source_code", sa.String(160), nullable=False),
        sa.Column("display", sa.String(500), nullable=False),
        sa.Column("normalized_display", sa.String(500), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("domain", sa.String(80), nullable=False),
        sa.Column("concept_class", sa.String(120)),
        sa.Column("standard_status", sa.String(40), nullable=False),
        sa.Column("omop_concept_id", sa.Integer()),
        sa.Column("valid_start_date", sa.Date()),
        sa.Column("valid_end_date", sa.Date()),
        sa.Column("invalid_reason", sa.String(80)),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["release_id"], ["terminology_releases.id"]),
        sa.UniqueConstraint("release_id", "source_code"),
    )
    _index(
        "terminology_concepts",
        "release_id",
        "institution_id",
        "source_system",
        "source_code",
        "normalized_display",
        "domain",
        "standard_status",
        "omop_concept_id",
        "invalid_reason",
    )

    op.create_table(
        "terminology_import_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("release_id", sa.String(36), nullable=False),
        sa.Column("institution_id", sa.String(100), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("artifact_name", sa.String(240), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("inserted_count", sa.Integer(), nullable=False),
        sa.Column("updated_count", sa.Integer(), nullable=False),
        sa.Column("skipped_count", sa.Integer(), nullable=False),
        sa.Column("rejected_count", sa.Integer(), nullable=False),
        sa.Column("error_summary", sa.JSON(), nullable=False),
        sa.Column("imported_by_user_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["release_id"], ["terminology_releases.id"]),
        sa.ForeignKeyConstraint(["imported_by_user_id"], ["users.id"]),
    )
    _index("terminology_import_runs", "release_id", "institution_id", "input_hash", "status")

    op.create_table(
        "terminology_mappings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mapping_family_id", sa.String(36), nullable=False),
        sa.Column("institution_id", sa.String(100), nullable=False),
        sa.Column("source_concept_id", sa.String(36), nullable=False),
        sa.Column("target_concept_id", sa.String(36), nullable=False),
        sa.Column("relationship_type", sa.String(80), nullable=False),
        sa.Column("mapping_method", sa.String(80), nullable=False),
        sa.Column("domain_expectation", sa.String(80), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("mapping_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("authored_by_user_id", sa.Integer(), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Integer()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("review_note", sa.Text()),
        sa.Column("supersedes_mapping_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_concept_id"], ["terminology_concepts.id"]),
        sa.ForeignKeyConstraint(["target_concept_id"], ["terminology_concepts.id"]),
        sa.ForeignKeyConstraint(["authored_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["supersedes_mapping_id"], ["terminology_mappings.id"]),
        sa.UniqueConstraint("mapping_family_id", "version"),
    )
    _index(
        "terminology_mappings",
        "mapping_family_id",
        "institution_id",
        "source_concept_id",
        "target_concept_id",
        "relationship_type",
        "mapping_hash",
        "status",
        "supersedes_mapping_id",
    )

    op.create_table(
        "concept_set_terminology_refs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("concept_set_version_id", sa.String(36), nullable=False),
        sa.Column("release_id", sa.String(36), nullable=False),
        sa.Column("mapping_hashes", sa.JSON(), nullable=False),
        sa.Column("expansion_policy", sa.String(80), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["concept_set_version_id"], ["concept_set_versions.id"]),
        sa.ForeignKeyConstraint(["release_id"], ["terminology_releases.id"]),
        sa.UniqueConstraint("concept_set_version_id", "release_id"),
    )
    _index("concept_set_terminology_refs", "concept_set_version_id", "release_id")

    op.create_table(
        "omop_etl_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.String(100), nullable=False),
        sa.Column("study_id", sa.String(36)),
        sa.Column("cohort_run_id", sa.String(36)),
        sa.Column("source_classification", sa.String(80), nullable=False),
        sa.Column("synthetic_only", sa.Boolean(), nullable=False),
        sa.Column("source_snapshot_marker", sa.String(160), nullable=False),
        sa.Column("source_snapshot_hash", sa.String(64), nullable=False),
        sa.Column("source_schema_version", sa.String(80), nullable=False),
        sa.Column("adapter_version", sa.String(80), nullable=False),
        sa.Column("cdm_version", sa.String(20), nullable=False),
        sa.Column("terminology_release_ids", sa.JSON(), nullable=False),
        sa.Column("mapping_hashes", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("export_files", sa.JSON(), nullable=False),
        sa.Column("export_hash", sa.String(64), nullable=False),
        sa.Column("executed_by_user_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"]),
        sa.ForeignKeyConstraint(["cohort_run_id"], ["cohort_runs.id"]),
        sa.ForeignKeyConstraint(["executed_by_user_id"], ["users.id"]),
    )
    _index(
        "omop_etl_runs",
        "institution_id",
        "study_id",
        "cohort_run_id",
        "status",
        "export_hash",
    )


def downgrade() -> None:
    for table in (
        "omop_etl_runs",
        "concept_set_terminology_refs",
        "terminology_mappings",
        "terminology_import_runs",
        "terminology_concepts",
        "terminology_releases",
        "terminology_sources",
        "analysis_run_outcomes",
        "analysis_plan_outcomes",
    ):
        op.drop_table(table)
    with op.batch_alter_table("research_analysis_runs") as batch:
        batch.drop_index(op.f("ix_research_analysis_runs_data_quality_run_id"))
        batch.drop_constraint("fk_research_analysis_runs_data_quality_run", type_="foreignkey")
        batch.drop_column("data_quality_run_id")
    with op.batch_alter_table("analysis_plans") as batch:
        batch.drop_index(op.f("ix_analysis_plans_data_quality_run_id"))
        batch.drop_constraint("fk_analysis_plans_data_quality_run", type_="foreignkey")
        batch.drop_column("data_quality_run_id")
    with op.batch_alter_table("data_quality_runs") as batch:
        for column in (
            "scope_status",
            "data_snapshot_hash",
            "data_snapshot_marker",
            "cohort_run_id",
        ):
            batch.drop_index(op.f(f"ix_data_quality_runs_{column}"))
        batch.drop_constraint("fk_data_quality_runs_cohort_run", type_="foreignkey")
        for column in (
            "scope_status",
            "ruleset_version",
            "terminology_snapshot",
            "data_snapshot_hash",
            "data_snapshot_marker",
            "cohort_run_id",
        ):
            batch.drop_column(column)
    with op.batch_alter_table(
        "data_quality_findings",
        naming_convention={"uq": "uq_%(table_name)s_%(column_0_name)s"},
    ) as batch:
        batch.drop_constraint("uq_data_quality_findings_run_scope", type_="unique")
        batch.create_unique_constraint(
            "uq_data_quality_findings_institution_id",
            ["institution_id", "rule", "resource_type", "resource_id", "field"],
        )
