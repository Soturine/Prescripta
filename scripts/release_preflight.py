#!/usr/bin/env python3
"""Executa gates, envia a main sem force e aguarda CI/Security verdes antes da tag."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
NPM = "npm.cmd" if sys.platform == "win32" else "npm"
(ROOT / ".tmp").mkdir(exist_ok=True)


def run(*args: str, cwd: Path = ROOT, capture: bool = False) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=capture, check=False)
    if result.returncode:
        raise SystemExit(result.stderr or result.stdout or f"Falhou: {' '.join(args)}")
    return result.stdout.strip() if capture else ""


if run("git", "status", "--porcelain", capture=True):
    raise SystemExit("O worktree deve estar limpo.")
if run("git", "branch", "--show-current", capture=True) != "main":
    raise SystemExit("Execute somente na branch main.")

for checker in (
    "check_text_quality.py",
    "check_markdown_links.py",
    "check_assets.py",
    "check_version_consistency.py",
    "check_install_scripts.py",
    "check_npm_audit.py",
):
    run(sys.executable, f"scripts/{checker}")
run("node", "scripts/check_i18n_catalogs.mjs")
run(sys.executable, "-m", "ruff", "check", ".", "--no-cache", cwd=ROOT / "backend")
run(
    sys.executable,
    "-m",
    "pytest",
    "--cov=app",
    "--cov-branch",
    "--cov-report=term-missing",
    "--cov-report=json:coverage.json",
    "--cov-fail-under=0",
    f"--basetemp={ROOT / '.tmp' / 'pytest'}",
    cwd=ROOT / "backend",
)
run(
    sys.executable,
    "../scripts/check_coverage_ratchet.py",
    "coverage.json",
    "--combined",
    "82",
    "--branches",
    "65",
    cwd=ROOT / "backend",
)
run(NPM, "ci", cwd=ROOT / "frontend")
run(NPM, "run", "lint", cwd=ROOT / "frontend")
run(NPM, "run", "typecheck", cwd=ROOT / "frontend")
run(NPM, "run", "test:coverage", cwd=ROOT / "frontend")
run(NPM, "run", "build", cwd=ROOT / "frontend")
run(NPM, "run", "test:e2e", cwd=ROOT / "frontend")
run("git", "diff", "--check")

sha = run("git", "rev-parse", "HEAD", capture=True)
run("git", "fetch", "origin")
remote_sha = run("git", "rev-parse", "origin/main", capture=True)
ancestry = subprocess.run(
    ("git", "merge-base", "--is-ancestor", remote_sha, sha), cwd=ROOT, check=False
)
if ancestry.returncode:
    raise SystemExit(
        "origin/main não é ancestral do HEAD; integre a mudança remota sem force e repita os gates."
    )
run("git", "push", "origin", "main")
for _ in range(90):
    raw = run(
        "gh",
        "run",
        "list",
        "--commit",
        sha,
        "--json",
        "databaseId,status,conclusion,url,workflowName,headSha",
        "--limit",
        "20",
        capture=True,
    )
    runs = json.loads(raw or "[]")
    required = {
        item["workflowName"]: item
        for item in runs
        if item.get("headSha") == sha and item.get("workflowName") in {"CI", "Security", "Container"}
    }
    failed = [
        item for item in required.values()
        if item["status"] == "completed" and item["conclusion"] != "success"
    ]
    if failed:
        details = ", ".join(f"{item['workflowName']}: {item['url']}" for item in failed)
        raise SystemExit(f"Workflow obrigatório falhou: {details}")
    if set(required) == {"CI", "Security", "Container"} and all(
        item["status"] == "completed" and item["conclusion"] == "success"
        for item in required.values()
    ):
        evidence = "\n".join(
            f"- {name}: run {item['databaseId']} — {item['url']}"
            for name, item in sorted(required.items())
        )
        print(f"CI, Security e Container verdes para v{VERSION} no SHA {sha}:\n{evidence}\nA tag pode ser criada.")
        sys.exit(0)
    time.sleep(10)
raise SystemExit("Timeout aguardando CI, Security e Container no SHA final; não crie a tag.")
