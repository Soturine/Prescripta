#!/usr/bin/env python3
"""Executa gates, envia a main e aguarda CI verde antes da tag."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


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
):
    run(sys.executable, f"scripts/{checker}")
run(sys.executable, "-m", "ruff", "check", ".", "--no-cache", cwd=ROOT / "backend")
run(
    sys.executable,
    "-m",
    "pytest",
    "--maxfail=1",
    f"--basetemp={ROOT / '.tmp' / 'pytest'}",
    cwd=ROOT / "backend",
)
run("npm", "ci", cwd=ROOT / "frontend")
run("npm", "run", "lint", cwd=ROOT / "frontend")
run("npm", "run", "typecheck", cwd=ROOT / "frontend")
run("npm", "run", "test", "--", "--run", cwd=ROOT / "frontend")
run("npm", "run", "build", cwd=ROOT / "frontend")
run("git", "diff", "--check")

sha = run("git", "rev-parse", "HEAD", capture=True)
run("git", "fetch", "origin")
if run("git", "rev-parse", "origin/main", capture=True) != sha:
    raise SystemExit("origin/main avançou; faça rebase e repita todos os gates.")
run("git", "push", "origin", "main")
for _ in range(60):
    raw = run(
        "gh",
        "run",
        "list",
        "--workflow",
        "ci.yml",
        "--commit",
        sha,
        "--json",
        "databaseId,status,conclusion,url",
        "--limit",
        "1",
        capture=True,
    )
    runs = json.loads(raw or "[]")
    if runs and runs[0]["status"] == "completed":
        item = runs[0]
        if item["conclusion"] != "success":
            raise SystemExit(f"CI falhou: {item['url']}")
        print(f"CI verde para v{VERSION}: {item['url']}\nA tag pode ser criada.")
        sys.exit(0)
    time.sleep(10)
raise SystemExit("Timeout aguardando GitHub Actions; não crie a tag.")
