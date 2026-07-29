#!/usr/bin/env python3
"""Falha quando metadados correntes divergem de VERSION."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
LABEL = f"v{VERSION}"
errors: list[str] = []


def expect(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        errors.append(f"{label}: esperado {expected!r}, encontrado {actual!r}")


if not re.fullmatch(r"0\.\d+\.\d+", VERSION):
    errors.append(f"VERSION deve usar a linha 0.x.y: {VERSION!r}")

with (ROOT / "backend/pyproject.toml").open("rb") as stream:
    expect("backend/pyproject.toml", tomllib.load(stream)["project"]["version"], VERSION)

frontend_package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
frontend_lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))
expect("frontend/package.json", frontend_package.get("version"), VERSION)
expect("frontend/package-lock.json", frontend_lock.get("version"), VERSION)
expect(
    "frontend/package-lock root package",
    frontend_lock.get("packages", {}).get("", {}).get("version"),
    VERSION,
)
expect(
    "frontend/src/config/appVersion.ts",
    (ROOT / "frontend/src/config/appVersion.ts").read_text(encoding="utf-8").splitlines()[0],
    f'export const APP_VERSION = "{LABEL}";',
)

wrong_pattern = re.compile(r"(?<!\d)(?:v?8\.6\.0|v860)(?!\d)", re.IGNORECASE)
historical_prefixes = (
    "docs/audits/",
    "docs/releases/v8.6.0",
)
historical_files = {"CHANGELOG.md"}
for path in ROOT.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".mjs", ".json", ".md", ".toml", ".yml", ".yaml", ".ps1", ".sh"}:
        continue
    relative = path.relative_to(ROOT).as_posix()
    if relative == "scripts/check_version_consistency.py":
        continue
    if relative.startswith(
        (".git/", ".tmp/", ".venv/", "frontend/node_modules/", "frontend/dist/")
    ):
        continue
    if relative.startswith("docs/releases/") and relative not in {
        f"docs/releases/{LABEL}.md",
        "docs/releases/README.md",
    }:
        continue
    if relative in historical_files or relative.startswith(historical_prefixes):
        continue
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if wrong_pattern.search(line):
            transparent_correction = (
                relative == f"docs/releases/{LABEL}.md"
                and "release histórica" in line.lower()
                and "numerada incorretamente" in line.lower()
            )
            if transparent_correction:
                continue
            errors.append(f"referência corrente incorreta em {relative}:{number}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"Versão consistente: {LABEL}.")
