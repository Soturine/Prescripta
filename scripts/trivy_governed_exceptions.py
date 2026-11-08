#!/usr/bin/env python3
"""Deriva as exceções Trivy governadas a partir de `.trivyignore.yaml` para o release-evidence.

Antes, `release-provenance.yml` publicava uma lista literal (`["CVE-2026-14456"]`) que ficou
desatualizada quando a exceção foi removida. Este script lê o arquivo real e falha se alguma
exceção estiver vencida na data da release, ou se faltar `expired_at`.

Formato mínimo esperado (subconjunto usado no repositório, sem dependência de PyYAML):
    vulnerabilities:
      - id: CVE-...
        purls: [...]
        expired_at: AAAA-MM-DD
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ENTRY = re.compile(r"^\s*-\s+id:\s*(?P<id>\S+)\s*$")
EXPIRY = re.compile(r"^\s*expired_at:\s*(?P<date>\d{4}-\d{2}-\d{2})\s*$")


def parse(text: str) -> list[dict[str, str | None]]:
    entries: list[dict[str, str | None]] = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        if match := ENTRY.match(line):
            entries.append({"id": match["id"], "expired_at": None})
        elif (match := EXPIRY.match(line)) and entries:
            entries[-1]["expired_at"] = match["date"]
    return entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, nargs="?", default=Path(".trivyignore.yaml"))
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args(argv)
    entries = parse(args.path.read_text(encoding="utf-8"))
    problems = [
        f"{item['id']}: sem expired_at" if item["expired_at"] is None
        else f"{item['id']}: vencida em {item['expired_at']}"
        for item in entries
        if item["expired_at"] is None or date.fromisoformat(item["expired_at"]) < args.today
    ]
    if problems:
        print("Exceções Trivy inválidas para release: " + "; ".join(problems), file=sys.stderr)
        return 1
    print(json.dumps(entries, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
