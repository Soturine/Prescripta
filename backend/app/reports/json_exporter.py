from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.reports.schemas import PRESCRIPTA_VERSION


def export_json_bytes(kind: str, data: dict[str, Any]) -> bytes:
    payload = {
        "export_type": kind,
        "export_version": PRESCRIPTA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "data": data,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")
