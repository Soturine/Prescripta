from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Medication:
    id: int | None
    brand_name: str
    active_ingredient: str
    therapeutic_class: str
    max_daily_dose_mg: float
    allowed_routes: list[str]
    contraindications: list[str]
    notes: str | None = None

    @classmethod
    def from_record(cls, record: Any) -> "Medication":
        return cls(
            id=record.id,
            brand_name=record.brand_name,
            active_ingredient=record.active_ingredient,
            therapeutic_class=record.therapeutic_class,
            max_daily_dose_mg=record.max_daily_dose_mg,
            allowed_routes=list(record.allowed_routes or []),
            contraindications=list(record.contraindications or []),
            notes=record.notes,
        )
