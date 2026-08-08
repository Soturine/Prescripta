from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
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
    for package, item in report.get("vulnerabilities", {}).items():
        if item.get("severity") not in {"high", "critical"}:
            continue
        advisory_ids = {
            str(via.get("url", "")).rsplit("/", 1)[-1]
            for via in item.get("via", [])
            if isinstance(via, dict) and via.get("url")
        }
        advisory_label = ", ".join(sorted(advisory_ids)) or "advisory não identificado"
        unexpected.append(f"{package}: {advisory_label}")
    if unexpected:
        print("Vulnerabilidades npm não aceitas:")
        print("\n".join(f"- {item}" for item in unexpected))
        return 1
    print("npm audit: sem vulnerabilidades high/critical e sem exceções ativas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
