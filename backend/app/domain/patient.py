from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class Patient:
    id: int | None
    name: str
    birth_date: date | None
    age: int | None
    weight_kg: float
    height_cm: float | None
    phone: str | None = None
    email: str | None = None
    mother_name: str | None = None
    allergies: list[str] = field(default_factory=list)
    comorbidities: list[str] = field(default_factory=list)
    current_medications: list[str] = field(default_factory=list)
    renal_condition: str | None = None
    hepatic_condition: str | None = None
    cardiac_condition: str | None = None
    gastrointestinal_history: str | None = None
    hypertension: bool = False
    diabetes: bool = False
    pregnancy_or_lactation: bool | None = None
    mental_health_factors: list[str] | None = None
    reproductive_gynecologic_factors: list[str] | None = None
    adverse_reactions: list[str] | None = None
    clinical_notes: str | None = None
    clinical_profile_reviewed_at: datetime | None = None
    clinical_profile_completeness_score: float = 0

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
            phone=getattr(record, "phone", None),
            email=getattr(record, "email", None),
            mother_name=getattr(record, "mother_name", None),
            allergies=list(record.allergies or []),
            comorbidities=list(record.comorbidities or []),
            current_medications=list(record.current_medications or []),
            renal_condition=record.renal_condition,
            hepatic_condition=record.hepatic_condition,
            cardiac_condition=record.cardiac_condition,
            gastrointestinal_history=record.gastrointestinal_history,
            hypertension=record.hypertension,
            diabetes=record.diabetes,
            pregnancy_or_lactation=record.pregnancy_or_lactation,
            mental_health_factors=list(getattr(record, "mental_health_factors", []) or []),
            reproductive_gynecologic_factors=list(
                getattr(record, "reproductive_gynecologic_factors", []) or []
            ),
            adverse_reactions=list(record.adverse_reactions or []),
            clinical_notes=record.clinical_notes,
            clinical_profile_reviewed_at=record.clinical_profile_reviewed_at,
            clinical_profile_completeness_score=record.clinical_profile_completeness_score or 0,
        )
