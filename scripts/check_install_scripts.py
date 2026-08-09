from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "frontend" / "package-lock.json"
POLICY = Path(__file__).with_name("install-script-policy.json")


def main() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    expected = json.loads(POLICY.read_text(encoding="utf-8"))
    packages = lock.get("packages", {})
    observed = {
        path: metadata.get("version")
        for path, metadata in packages.items()
        if metadata.get("hasInstallScript") is True
    }
    if observed != expected:
        missing = sorted(set(expected) - set(observed))
        unexpected = sorted(set(observed) - set(expected))
        changed = sorted(
            path
            for path in set(expected) & set(observed)
            if expected[path] != observed[path]
        )
        raise SystemExit(
            "Install-script inventory changed; review before install. "
            f"missing={missing}, unexpected={unexpected}, version_changed={changed}"
        )
    print("Install-script inventory OK: exact package paths and versions approved.")


if __name__ == "__main__":
    main()
