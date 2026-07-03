from __future__ import annotations

import csv
from io import StringIO

from app.integrations.mapping.internal_mapper import InternalMapper


class CsvImporter:
    source_type = "csv"

    def __init__(self) -> None:
        self.mapper = InternalMapper()

    def import_text(self, text: str) -> list[dict]:
        records: list[dict] = []
        reader = csv.DictReader(StringIO(text))
        for row in reader:
            record_type = (row.get("record_type") or row.get("type") or "").strip().lower()
            value = row.get("value") or row.get("name") or row.get("medication") or ""
            if not value:
                continue
            if record_type in {"medication", "current_medication", "medicamento"}:
                mapped = self.mapper.medications([value])[0]
                mapped_type = "current_medication"
            elif record_type in {"condition", "condicao"}:
                mapped = self.mapper.conditions([value])[0]
                mapped_type = "condition"
            else:
                mapped = {
                    "original_value": value,
                    "normalized_value": value,
                    "requires_review": True,
                }
                mapped_type = record_type or "unknown"
            records.append(
                {
                    "record_type": mapped_type,
                    "source_payload": row,
                    "mapped_payload": mapped,
                    "confidence": float(mapped.get("confidence", 0.4)),
                }
            )
        return records
