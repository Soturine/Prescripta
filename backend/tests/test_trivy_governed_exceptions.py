"""Evidência de release deriva as exceções Trivy do arquivo real e bloqueia exceção vencida."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "trivy_governed_exceptions", ROOT / "scripts" / "trivy_governed_exceptions.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_current_file_matches_parsed_entries(capsys) -> None:
    assert module.main([str(ROOT / ".trivyignore.yaml"), "--today", "2026-11-08"]) == 0
    entries = json.loads(capsys.readouterr().out)
    assert {item["id"] for item in entries} == {"CVE-2026-85091", "CVE-2026-76844"}
    assert "CVE-2026-14456" not in {item["id"] for item in entries}


def test_expired_exception_blocks_release(tmp_path, capsys) -> None:
    path = tmp_path / "ignore.yaml"
    path.write_text(
        "vulnerabilities:\n  - id: CVE-0000-1\n    expired_at: 2026-09-07\n", encoding="utf-8"
    )
    assert module.main([str(path), "--today", "2026-11-08"]) == 1
    assert "vencida" in capsys.readouterr().err


def test_missing_expiry_blocks_release(tmp_path) -> None:
    path = tmp_path / "ignore.yaml"
    path.write_text("vulnerabilities:\n  - id: CVE-0000-2\n", encoding="utf-8")
    assert module.main([str(path), "--today", "2026-11-08"]) == 1


def test_empty_policy_is_allowed(tmp_path, capsys) -> None:
    path = tmp_path / "ignore.yaml"
    path.write_text("vulnerabilities: []\n", encoding="utf-8")
    assert module.main([str(path)]) == 0
    assert json.loads(capsys.readouterr().out) == []
