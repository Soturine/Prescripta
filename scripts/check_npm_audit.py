from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
ALLOWED_ADVISORIES = {
    "GHSA-qwww-vcr4-c8h2": {
        "expires": date(2026, 8, 15),
        "packages": {"react-router", "react-router-dom"},
    }
}


def main() -> int:
    npm = shutil.which("npm")
    if not npm:
        print("npm não encontrado.")
        return 2
    completed = subprocess.run(
        [npm, "audit", "--json"],
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        check=False,
    )
    report = json.loads(completed.stdout)
    unexpected: list[str] = []
    today = date.today()
    for package, item in report.get("vulnerabilities", {}).items():
        if item.get("severity") not in {"high", "critical"}:
            continue
        advisory_ids = {
            str(via.get("url", "")).rsplit("/", 1)[-1]
            for via in item.get("via", [])
            if isinstance(via, dict) and via.get("url")
        }
        if not advisory_ids:
            continue
        for advisory_id in advisory_ids:
            allowed = ALLOWED_ADVISORIES.get(advisory_id)
            if (
                not allowed
                or package not in allowed["packages"]
                or today > allowed["expires"]
            ):
                unexpected.append(f"{package}: {advisory_id}")
    if unexpected:
        print("Vulnerabilidades npm não aceitas:")
        print("\n".join(f"- {item}" for item in unexpected))
        return 1
    print("npm audit: sem risco high/critical inesperado; exceção temporária validada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
