from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "frontend" / "package-lock.json"

EXPECTED = {
    "node_modules/esbuild": "0.28.1",
    "node_modules/fsevents": "2.3.3",
    "node_modules/playwright/node_modules/fsevents": "2.3.2",
}


def main() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    packages = lock.get("packages", {})
    observed = {
        path: metadata.get("version")
        for path, metadata in packages.items()
        if metadata.get("hasInstallScript") is True
    }
    if observed != EXPECTED:
        missing = sorted(set(EXPECTED) - set(observed))
        unexpected = sorted(set(observed) - set(EXPECTED))
        changed = sorted(
            path
            for path in set(EXPECTED) & set(observed)
            if EXPECTED[path] != observed[path]
        )
        raise SystemExit(
            "Install-script inventory changed; review before install. "
            f"missing={missing}, unexpected={unexpected}, version_changed={changed}"
        )
    print("Install-script inventory OK: exact package paths and versions approved.")


if __name__ == "__main__":
    main()
