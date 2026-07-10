from __future__ import annotations

import csv
import io
import json
from typing import Any


def export_csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    normalized = [_flatten(row) for row in rows]
    fieldnames = sorted({key for row in normalized for key in row}) or ["empty"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in normalized:
        writer.writerow(row)
    return output.getvalue().encode("utf-8-sig")


def _flatten(value: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, item in value.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, dict):
            flattened.update(_flatten(item, name))
        elif isinstance(item, list):
            flattened[name] = json.dumps(item, ensure_ascii=False, default=str)
        else:
            flattened[name] = item
    return flattened
