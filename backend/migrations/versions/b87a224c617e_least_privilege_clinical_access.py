"""least privilege clinical access

Revision ID: b87a224c617e
Revises: a87d01c4e921
Create Date: 2026-07-29 04:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b87a224c617e"
down_revision: str | Sequence[str] | None = "a87d01c4e921"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "profession",
                sa.String(length=40),
                nullable=False,
                server_default="administration",
            )
        )
        batch_op.add_column(
            sa.Column("capabilities", sa.JSON(), nullable=False, server_default="[]")
        )
        batch_op.add_column(
            sa.Column(
                "capability_policy_version",
                sa.String(length=40),
                nullable=False,
                server_default="explicit-v1",
            )
        )
        batch_op.add_column(
            sa.Column("specialty_codes", sa.JSON(), nullable=False, server_default="[]")
        )
        batch_op.add_column(sa.Column("credential_type", sa.String(length=40)))
        batch_op.add_column(sa.Column("credential_code_demo", sa.String(length=80)))
        batch_op.add_column(sa.Column("credential_region", sa.String(length=20)))
        batch_op.add_column(sa.Column("credential_expires_at", sa.DateTime(timezone=True)))
        batch_op.add_column(
            sa.Column("institutional_policy", sa.JSON(), nullable=False, server_default="{}")
        )
        batch_op.add_column(
            sa.Column("sensitive_data_segments", sa.JSON(), nullable=False, server_default="[]")
        )
        batch_op.create_index("ix_users_profession", ["profession"])

    with op.batch_alter_table("patient_access_grants") as batch_op:
        batch_op.add_column(
            sa.Column(
                "institution_id",
                sa.String(length=100),
                nullable=False,
                server_default="demo",
            )
        )
        batch_op.add_column(
            sa.Column(
                "capability",
                sa.String(length=80),
                nullable=False,
                server_default="patient.read",
            )
        )
        batch_op.add_column(
            sa.Column(
                "purpose",
                sa.String(length=40),
                nullable=False,
                server_default="treatment",
            )
        )
        batch_op.add_column(sa.Column("granted_by_user_id", sa.Integer()))
        batch_op.add_column(
            sa.Column(
                "starts_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(timezone=True)))
        batch_op.add_column(sa.Column("revoked_at", sa.DateTime(timezone=True)))
        batch_op.add_column(sa.Column("revoked_by_user_id", sa.Integer()))
        batch_op.add_column(sa.Column("revocation_reason", sa.String(length=220)))
        batch_op.add_column(sa.Column("care_episode_id", sa.String(length=80)))
        batch_op.add_column(
            sa.Column(
                "status", sa.String(length=30), nullable=False, server_default="active"
            )
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )
        batch_op.create_foreign_key(
            "fk_patient_access_grants_granted_by",
            "users",
            ["granted_by_user_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_patient_access_grants_revoked_by",
            "users",
            ["revoked_by_user_id"],
            ["id"],
        )
        batch_op.create_index("ix_patient_access_grants_capability", ["capability"])
        batch_op.create_index("ix_patient_access_grants_purpose", ["purpose"])
        batch_op.create_index("ix_patient_access_grants_status", ["status"])
        batch_op.create_index("ix_patient_access_grants_care_episode_id", ["care_episode_id"])

    op.create_table(
        "care_team_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("institution_id", sa.String(length=100), nullable=False),
        sa.Column("team_code", sa.String(length=80), nullable=False),
        sa.Column("care_role", sa.String(length=80), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("granted_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("patient_id", "user_id", "team_code"),
    )
    op.create_index("ix_care_team_memberships_patient_id", "care_team_memberships", ["patient_id"])
    op.create_index("ix_care_team_memberships_user_id", "care_team_memberships", ["user_id"])
    op.create_index(
        "ix_care_team_memberships_institution_id", "care_team_memberships", ["institution_id"]
    )

    op.create_table(
        "care_episode_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("episode_id", sa.String(length=80), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("institution_id", sa.String(length=100), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("granted_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("episode_id", "user_id"),
    )
    op.create_index(
        "ix_care_episode_assignments_episode_id",
        "care_episode_assignments",
        ["episode_id"],
    )
    op.create_index(
        "ix_care_episode_assignments_patient_id",
        "care_episode_assignments",
        ["patient_id"],
    )
    op.create_index("ix_care_episode_assignments_user_id", "care_episode_assignments", ["user_id"])
    op.create_index(
        "ix_care_episode_assignments_institution_id",
        "care_episode_assignments",
        ["institution_id"],
    )

    op.create_table(
        "break_glass_accesses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("institution_id", sa.String(length=100), nullable=False),
        sa.Column("capability", sa.String(length=80), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("ended_by_user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("review_status", sa.String(length=30), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_by_user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("review_notes", sa.String(length=500)),
        sa.Column("objects_accessed", sa.JSON(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "idempotency_key"),
    )
    op.create_index("ix_break_glass_accesses_patient_id", "break_glass_accesses", ["patient_id"])
    op.create_index("ix_break_glass_accesses_user_id", "break_glass_accesses", ["user_id"])
    op.create_index(
        "ix_break_glass_accesses_institution_id", "break_glass_accesses", ["institution_id"]
    )
    op.create_index(
        "ix_break_glass_accesses_review_status", "break_glass_accesses", ["review_status"]
    )
    op.create_index("ix_break_glass_accesses_status", "break_glass_accesses", ["status"])

    op.create_table(
        "patient_psychological_contexts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "patient_id",
            sa.Integer(),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column("institution_id", sa.String(length=100), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("medication_safety_factors", sa.JSON(), nullable=False),
        sa.Column("confidential_notes", sa.Text()),
        sa.Column("consent_status", sa.String(length=40), nullable=False),
        sa.Column("policy_reference", sa.String(length=160)),
        sa.Column("updated_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_patient_psychological_contexts_patient_id",
        "patient_psychological_contexts",
        ["patient_id"],
        unique=True,
    )
    op.create_index(
        "ix_patient_psychological_contexts_institution_id",
        "patient_psychological_contexts",
        ["institution_id"],
    )


def downgrade() -> None:
    op.drop_table("patient_psychological_contexts")
    op.drop_table("break_glass_accesses")
    op.drop_table("care_episode_assignments")
    op.drop_table("care_team_memberships")
    with op.batch_alter_table("patient_access_grants") as batch_op:
        batch_op.drop_index("ix_patient_access_grants_care_episode_id")
        batch_op.drop_index("ix_patient_access_grants_status")
        batch_op.drop_index("ix_patient_access_grants_purpose")
        batch_op.drop_index("ix_patient_access_grants_capability")
        batch_op.drop_constraint("fk_patient_access_grants_revoked_by", type_="foreignkey")
        batch_op.drop_constraint("fk_patient_access_grants_granted_by", type_="foreignkey")
        for column in (
            "updated_at",
            "status",
            "care_episode_id",
            "revocation_reason",
            "revoked_by_user_id",
            "revoked_at",
            "expires_at",
            "starts_at",
            "granted_by_user_id",
            "purpose",
            "capability",
            "institution_id",
        ):
            batch_op.drop_column(column)
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_profession")
        for column in (
            "sensitive_data_segments",
            "institutional_policy",
            "credential_expires_at",
            "credential_region",
            "credential_code_demo",
            "credential_type",
            "specialty_codes",
            "capability_policy_version",
            "capabilities",
            "profession",
        ):
            batch_op.drop_column(column)
