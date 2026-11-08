"""Server-side revocation of access tokens on logout (PRE-05).

Revision ID: b11a2c3d4e50
Revises: a10f0c0d1000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b11a2c3d4e50"
down_revision: str | None = "a10f0c0d1000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "revoked_access_tokens",
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("jti"),
    )
    op.create_index(
        "ix_revoked_access_tokens_user_id", "revoked_access_tokens", ["user_id"], unique=False
    )
    op.create_index(
        "ix_revoked_access_tokens_expires_at",
        "revoked_access_tokens",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_revoked_access_tokens_expires_at", table_name="revoked_access_tokens")
    op.drop_index("ix_revoked_access_tokens_user_id", table_name="revoked_access_tokens")
    op.drop_table("revoked_access_tokens")
