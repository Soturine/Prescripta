#!/usr/bin/env python3
"""Verificador canônico, multiplataforma, de UTF-8 e português visível."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EXTENSIONS = {".md", ".py", ".ts", ".tsx"}
TARGETS = ("README.md", "CHANGELOG.md", "ROADMAP.md", "AGENTS.md", "CONTRIBUTING.md", "docs", "backend/app", "frontend/src", "scripts", "examples")
MOJIBAKE = ("Ã", "Â", "�", "â€™", "â€œ", "â€")
FORBIDDEN = (
    "nao", "prescricao", "clinico", "clinica", "clinicos", "clinicas", "historico",
    "relatorio", "relatorios", "avaliacao", "decisao", "medico", "medicos", "usuario",
    "usuarios", "versao", "versoes", "configuracao", "validacao", "jurisdicao", "orientacao",
    "execucao", "importacao", "revisao", "farmacologico", "principio", "audiencia",
    "psicotropico", "psicotropicos", "serotonergico", "serotonergicos", "litio",
    "extracao", "etaria", "identificavel", "padrao", "catalogo", "ampliavel", "modulo",
    "visao", "documentacao", "avancada", "especificos", "condicoes", "separacao", "seguranca",
)

def files_for(path: Path | None) -> list[Path]:
    roots = [path] if path else [ROOT / item for item in TARGETS]
    found: list[Path] = []
    for target in roots:
        if not target.exists():
            continue
        candidates = target.rglob("*") if target.is_dir() else [target]
        found.extend(p for p in candidates if p.is_file() and p.suffix in EXTENSIONS and not {"node_modules", "dist"} & set(p.parts))
    return sorted(set(found))

def visible_line(path: Path, line: str, in_fence: bool) -> bool:
    if in_fence or "text-quality: allow" in line:
        return False
    if path.suffix == ".md":
        return True
    if path.suffix in {".ts", ".tsx"}:
        return bool(re.search(r">[^<{]+<|title=|placeholder=|label=|description=|message=|text:", line))
    return bool(re.search(r"detail=|title=|description=|recommendation=|message=|educational_notice=", line))

def check(path: Path | None = None) -> list[str]:
    allow_path = ROOT / "scripts/text-quality-allowlist.json"
    if not allow_path.exists():
        return [f"Allowlist obrigatória não encontrada: {allow_path}"]
    json.loads(allow_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for file in files_for(path):
        relative = file.relative_to(ROOT) if file.is_relative_to(ROOT) else file
        try:
            text = file.read_text(encoding="utf-8", errors="strict")
        except UnicodeError as exc:
            errors.append(f"UTF-8 inválido em {relative}: {exc}")
            continue
        if file.resolve() != Path(__file__).resolve():
            for marker in MOJIBAKE:
                if marker in text:
                    errors.append(f"Mojibake em {relative}: {marker!r}")
        in_fence = False
        for number, line in enumerate(text.splitlines(), 1):
            if file.suffix == ".md" and line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if not visible_line(file, line, in_fence):
                continue
            scan = re.sub(r"`[^`]*`|https?://\S+", "", line)
            if re.search(r"[A-Za-zÀ-ÿ]+\?[A-Za-zÀ-ÿ?]+", scan):
                errors.append(f"Possível caractere corrompido em {relative}:{number}")
            for word in FORBIDDEN:
                if re.search(rf"(?i)(?<![A-Za-z0-9_]){re.escape(word)}(?![A-Za-z0-9_])", scan):
                    errors.append(f"Termo sem acento em {relative}:{number}: '{word}'")
    return sorted(set(errors))

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path)
    args = parser.parse_args()
    errors = check(args.path.resolve() if args.path else None)
    if errors:
        print("\n".join(f"Erro: {error}" for error in errors))
        return 1
    print("Qualidade textual OK.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
