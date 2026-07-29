import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect


def _alembic(backend: Path, env: dict[str, str], *args: str) -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=backend,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_alembic_upgrade_downgrade_and_schema_check(tmp_path: Path):
    backend = Path(__file__).parents[1]
    database = tmp_path / "migration.db"
    url = f"sqlite:///{database.as_posix()}"
    env = os.environ | {
        "PRESCRIPTA_ENV": "test",
        "PRESCRIPTA_AUTO_SEED": "false",
        "PRESCRIPTA_DATABASE_URL": url,
    }
    _alembic(backend, env, "upgrade", "head")
    tables = set(inspect(create_engine(url)).get_table_names())
    assert {"patients", "prescription_audits", "alembic_version"} <= tables
    _alembic(backend, env, "downgrade", "base")
    _alembic(backend, env, "upgrade", "head")
    _alembic(backend, env, "check")
