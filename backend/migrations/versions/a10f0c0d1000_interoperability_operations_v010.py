"""Interoperability and tenant-scoped import identity v0.10.0.

Revision ID: a10f0c0d1000
Revises: f3a91c7d2b40
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a10f0c0d1000"
down_revision: str | None = "f3a91c7d2b40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinical_import_batches",
        sa.Column("institution_id", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "clinical_import_batches",
        sa.Column("idempotency_key", sa.String(length=160), nullable=True),
    )
    op.add_column(
        "clinical_import_batches",
        sa.Column("source_hash", sa.String(length=64), nullable=True),
    )
    op.execute(
        "UPDATE clinical_import_batches SET institution_id = COALESCE("
        "(SELECT institution_id FROM users WHERE users.id = clinical_import_batches.imported_by), "
        "'legacy')"
    )
    with op.batch_alter_table("clinical_import_batches") as batch_op:
        batch_op.alter_column("institution_id", existing_type=sa.String(length=100), nullable=False)
        batch_op.create_index("ix_clinical_import_batches_institution_id", ["institution_id"])
        batch_op.create_unique_constraint(
            "uq_clinical_import_batch_idempotency",
            ["institution_id", "source_type", "idempotency_key"],
        )


def downgrade() -> None:
    with op.batch_alter_table("clinical_import_batches") as batch_op:
        batch_op.drop_constraint("uq_clinical_import_batch_idempotency", type_="unique")
        batch_op.drop_index("ix_clinical_import_batches_institution_id")
        batch_op.drop_column("source_hash")
        batch_op.drop_column("idempotency_key")
        batch_op.drop_column("institution_id")
