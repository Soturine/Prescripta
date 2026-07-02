from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class Patient:
    id: int | None
    name: str
    birth_date: date | None
    age: int | None
    weight_kg: float
    height_cm: float | None
    allergies: list[str]
    comorbidities: list[str]
    current_medications: list[str]

    @property
    def computed_age(self) -> int | None:
        if self.age is not None:
            return self.age
        if self.birth_date is None:
            return None

        today = date.today()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years

    @classmethod
    def from_record(cls, record: Any) -> "Patient":
        return cls(
            id=record.id,
            name=record.name,
            birth_date=record.birth_date,
            age=record.age,
            weight_kg=record.weight_kg,
            height_cm=record.height_cm,
            allergies=list(record.allergies or []),
            comorbidities=list(record.comorbidities or []),
            current_medications=list(record.current_medications or []),
        )
