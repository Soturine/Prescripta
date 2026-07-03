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
    max_duration_days: int | None = None
    max_cumulative_dose_mg: float | None = None
    condition_specific_limits: dict | None = None
    renal_caution: bool = False
    hepatic_caution: bool = False
    cardiac_caution: bool = False
    gastrointestinal_caution: bool = False
    elderly_caution: bool = False
    metabolism_organs: list[str] | None = None
    elimination_organs: list[str] | None = None
    organs_involved: list[str] | None = None
    relevant_adverse_effects: list[str] | None = None
    structured_contraindications: list[str] | None = None
    therapeutic_action: str | None = None
    alternative_group: str | None = None
    related_medications: list[str] | None = None
    knowledge_source: str | None = None
    active_ingredient_id: int | None = None
    commercial_aliases: list[str] | None = None
    therapeutic_classes: list[str] | None = None
    source_jurisdiction: str = "BR"
    evidence_source_type: str = "demo_seed"
    validation_status: str = "demo"
    concentration: str | None = None
    pharmaceutical_form: str | None = None
    evidence_source_url: str | None = None

    @classmethod
    def from_record(cls, record: Any) -> "Medication":
        return cls(
            id=record.id,
            active_ingredient_id=record.active_ingredient_id,
            brand_name=record.brand_name,
            active_ingredient=record.active_ingredient,
            commercial_aliases=list(record.commercial_aliases or []),
            therapeutic_class=record.therapeutic_class,
            therapeutic_classes=list(record.therapeutic_classes or []),
            source_jurisdiction=record.source_jurisdiction,
            evidence_source_type=record.evidence_source_type,
            validation_status=record.validation_status,
            concentration=record.concentration,
            pharmaceutical_form=record.pharmaceutical_form,
            evidence_source_url=record.evidence_source_url,
            max_daily_dose_mg=record.max_daily_dose_mg,
            max_duration_days=record.max_duration_days,
            max_cumulative_dose_mg=record.max_cumulative_dose_mg,
            condition_specific_limits=dict(record.condition_specific_limits or {}),
            allowed_routes=list(record.allowed_routes or []),
            contraindications=list(record.contraindications or []),
            renal_caution=record.renal_caution,
            hepatic_caution=record.hepatic_caution,
            cardiac_caution=record.cardiac_caution,
            gastrointestinal_caution=record.gastrointestinal_caution,
            elderly_caution=record.elderly_caution,
            metabolism_organs=list(record.metabolism_organs or []),
            elimination_organs=list(record.elimination_organs or []),
            organs_involved=list(record.organs_involved or []),
            relevant_adverse_effects=list(record.relevant_adverse_effects or []),
            structured_contraindications=list(record.structured_contraindications or []),
            therapeutic_action=record.therapeutic_action,
            alternative_group=record.alternative_group,
            related_medications=list(record.related_medications or []),
            knowledge_source=record.knowledge_source,
            notes=record.notes,
        )
