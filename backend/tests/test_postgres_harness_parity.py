"""NEW-05: o harness opt-in de PostgreSQL recria as views das migrações exatamente como elas são."""

from __future__ import annotations

from pathlib import Path

from conftest import MIGRATION_VIEWS

MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "e8f3a921c4d0_research_copilot_comparative_v092.py"
)


def test_harness_view_ddl_matches_migration() -> None:
    source = MIGRATION.read_text(encoding="utf-8")
    # A migração concatena literais; compara o DDL normalizado sem aspas de continuação.
    flattened = "".join(
        line.split('"')[1] for line in source.splitlines() if line.strip().startswith('"')
    )
    for ddl in MIGRATION_VIEWS.values():
        assert ddl in flattened
