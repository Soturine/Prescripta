#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def changes(baseline: dict, candidate: dict) -> list[str]:
    found: list[str] = []
    for path, old_path in baseline.get("paths", {}).items():
        if path not in candidate.get("paths", {}):
            found.append(f"removed_path:{path}")
            continue
        for method in set(old_path) & HTTP_METHODS:
            if method not in candidate["paths"][path]:
                found.append(f"removed_operation:{method.upper()} {path}")
    old_schemas = baseline.get("components", {}).get("schemas", {})
    new_schemas = candidate.get("components", {}).get("schemas", {})
    for name, old_schema in old_schemas.items():
        if name not in new_schemas:
            found.append(f"removed_schema:{name}")
            continue
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schemas[name].get("required", []))
        for field in sorted(new_required - old_required):
            found.append(f"new_required_field:{name}.{field}")
        for field in sorted(set(old_schema.get("properties", {})) - set(new_schemas[name].get("properties", {}))):
            found.append(f"removed_field:{name}.{field}")
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--allowlist", type=Path)
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    detected = changes(baseline, candidate)
    allowed = []
    if args.allowlist:
        allowed = json.loads(args.allowlist.read_text(encoding="utf-8"))["allowed_breaks"]
    unexpected = sorted(set(detected) - set(allowed))
    stale = sorted(set(allowed) - set(detected))
    print(json.dumps({"detected": detected, "unexpected": unexpected, "stale": stale}, indent=2))
    return 1 if unexpected or stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
