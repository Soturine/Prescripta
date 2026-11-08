"""Index patients.institution_id used by every scoped patient listing (NEW-18).

Revision ID: c12b3d4e5f60
Revises: b11a2c3d4e50
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c12b3d4e5f60"
down_revision: str | None = "b11a2c3d4e50"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_patients_institution_id", "patients", ["institution_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_patients_institution_id", table_name="patients")
