#!/usr/bin/env python3
"""Sincroniza metadados gerados com a versão canônica da raiz."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def replace(path: str, pattern: str, replacement: str, *, count: int = 0) -> None:
    target = ROOT / path
    source = target.read_text(encoding="utf-8")
    updated, replacements = re.subn(pattern, replacement, source, count=count, flags=re.MULTILINE)
    if replacements == 0:
        raise SystemExit(f"Padrão de versão não encontrado em {path}")
    target.write_text(updated, encoding="utf-8")


def main() -> None:
    if not re.fullmatch(r"0\.\d+\.\d+", VERSION):
        raise SystemExit(f"VERSION inválida: {VERSION!r}")
    replace("backend/pyproject.toml", r'^(version\s*=\s*)"[^"]+"', rf'\1"{VERSION}"', count=1)
    replace("frontend/package.json", r'^(\s*"version"\s*:\s*)"[^"]+"', rf'\1"{VERSION}"', count=1)
    replace(
        "frontend/package-lock.json",
        r'^(\s*"version"\s*:\s*)"[^"]+"',
        rf'\1"{VERSION}"',
        count=2,
    )
    replace(
        "frontend/src/config/appVersion.ts",
        r'^export const APP_VERSION = "[^"]+";',
        f'export const APP_VERSION = "v{VERSION}";',
        count=1,
    )
    print(f"Metadados sincronizados com v{VERSION}.")


if __name__ == "__main__":
    main()
