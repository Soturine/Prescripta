#!/usr/bin/env python3
"""Valida integridade e conjunto mínimo de evidência visual da versão corrente."""

from __future__ import annotations

import hashlib
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABEL = f"v{(ROOT / 'VERSION').read_text(encoding='utf-8').strip()}"
errors: list[str] = []
required_stems = {
    "login",
    "dashboard-clinical",
    "dashboard-admin",
    "dashboard-auditor",
    "patients-list",
    "patient-details",
    "patient-history",
    "patient-documents",
    "medications-catalog",
    "medication-details",
    "medication-curation",
    "prescription-clinical",
    "prescription-technical",
    "dose-intelligence",
    "psychotropic-safety",
    "prescribing-policy",
    "protocols-list",
    "protocol-run",
    "imports",
    "reports",
    "audit",
    "ai-settings",
    "users-specialties",
    "mobile",
    "tablet",
}
required_files = {f"{stem}-{LABEL}.png" for stem in required_stems}
required_files |= {
    f"prescripta-{LABEL}-main-demo.gif",
    f"prescripta-{LABEL}-clinical-flow.gif",
    f"prescripta-{LABEL}-admin-flow.gif",
    f"prescripta-{LABEL}-audit-flow.gif",
    f"prescripta-{LABEL}-mobile-flow.gif",
}
current_dir = ROOT / "docs" / "assets" / LABEL
if not current_dir.is_dir():
    errors.append(f"Diretório de assets corrente ausente: docs/assets/{LABEL}")
else:
    groups: dict[str, list[str]] = defaultdict(list)
    current_names = {file.name for file in current_dir.iterdir() if file.is_file()}
    errors.extend(f"Asset obrigatório ausente: {name}" for name in sorted(required_files-current_names))
    for file in current_dir.iterdir():
        if file.suffix.lower() not in {".png", ".gif", ".jpg", ".jpeg"}:
            continue
        if file.stat().st_size == 0:
            errors.append(f"Asset vazio: {file.relative_to(ROOT)}")
        groups[hashlib.sha256(file.read_bytes()).hexdigest()].append(file.name)
    for names in groups.values():
        if len(names) > 1:
            errors.append(f"Hashes duplicados em {LABEL}: {', '.join(sorted(names))}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"Assets {LABEL} OK.")
