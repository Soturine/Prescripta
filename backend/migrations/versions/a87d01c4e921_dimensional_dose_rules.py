"""dimensional dose rules

Revision ID: a87d01c4e921
Revises: 3978b04e2f62
Create Date: 2026-07-29 04:05:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a87d01c4e921"
down_revision: str | Sequence[str] | None = "3978b04e2f62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


NUMERIC_COLUMNS = (
    "max_daily_dose_mg",
    "dose_mg_per_kg",
    "usual_dose_low",
    "usual_dose_high",
    "max_single_dose",
    "max_per_procedure",
    "max_rate",
    "max_cumulative_dose_mg",
)


def upgrade() -> None:
    with op.batch_alter_table("medications") as batch_op:
        for column in NUMERIC_COLUMNS:
            batch_op.alter_column(
                column,
                existing_type=sa.Float(),
                type_=sa.Numeric(precision=24, scale=12),
                existing_nullable=column != "max_daily_dose_mg",
            )
        batch_op.add_column(
            sa.Column(
                "max_single_dose_unit",
                sa.String(length=40),
                nullable=False,
                server_default="mg",
            )
        )
        batch_op.add_column(
            sa.Column(
                "max_cumulative_dose_unit",
                sa.String(length=40),
                nullable=False,
                server_default="mg",
            )
        )
        batch_op.add_column(
            sa.Column(
                "dose_rule_version",
                sa.String(length=80),
                nullable=False,
                server_default="demo_dose_2026-07-r1",
            )
        )
        batch_op.add_column(
            sa.Column(
                "dose_rounding_policy",
                sa.String(length=80),
                nullable=False,
                server_default="prescripta-half-even-v1",
            )
        )
        batch_op.add_column(
            sa.Column(
                "dose_calculation_precision",
                sa.String(length=20),
                nullable=False,
                server_default="0.0001",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("medications") as batch_op:
        batch_op.drop_column("dose_calculation_precision")
        batch_op.drop_column("dose_rounding_policy")
        batch_op.drop_column("dose_rule_version")
        batch_op.drop_column("max_cumulative_dose_unit")
        batch_op.drop_column("max_single_dose_unit")
        for column in reversed(NUMERIC_COLUMNS):
            batch_op.alter_column(
                column,
                existing_type=sa.Numeric(precision=24, scale=12),
                type_=sa.Float(),
                existing_nullable=column != "max_daily_dose_mg",
            )
