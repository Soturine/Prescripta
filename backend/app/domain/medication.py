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
    continuous_use: bool = False
    monitoring_required: bool = False
    monitoring_notes: str | None = None
    condition_specific_limits: dict | None = None
    renal_caution: bool = False
    hepatic_caution: bool = False
    cardiac_caution: bool = False
    gastrointestinal_caution: bool = False
    elderly_caution: bool = False
    mechanism_of_action: str | None = None
    absorption_notes: str | None = None
    distribution_notes: str | None = None
    metabolism_organs: list[str] | None = None
    elimination_organs: list[str] | None = None
    renal_elimination_level: str = "nao_informado"
    hepatic_metabolism_level: str = "nao_informado"
    cyp_interactions: list[str] | None = None
    pharmacodynamic_notes: str | None = None
    pharmacokinetic_notes: str | None = None
    clinical_interpretation: str | None = None
    neuropsychiatric_cautions: list[str] | None = None
    reproductive_cautions: list[str] | None = None
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
    dose_mg_per_kg: float | None = None
    dose_by_weight_enabled: bool = False
    usual_dose_low: float | None = None
    usual_dose_high: float | None = None
    max_single_dose: float | None = None
    max_per_procedure: float | None = None
    dose_calculation_basis: str = "fixed"
    dose_unit: str = "mg"
    dose_rule_validation_status: str = "pending_review"
    dose_source_refs: list[str] | None = None
    controlled_substance: bool = False
    controlled_substance_list: str | None = None
    prescription_form_type: str | None = None
    high_alert_category: str | None = None
    recommended_specialty_codes: list[str] | None = None
    required_specialty_codes: list[str] | None = None
    requires_second_review: bool = False
    requires_institutional_protocol: bool = False
    policy_type: str = "demo_policy"
    policy_strength: str = "warning_only"
    policy_validation_status: str = "pending_review"
    policy_source_refs: list[str] | None = None
    psychotropic_class: str | None = None
    psychotropic_profile: dict | None = None

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
            dose_mg_per_kg=getattr(record, "dose_mg_per_kg", None),
            dose_by_weight_enabled=bool(getattr(record, "dose_by_weight_enabled", False)),
            usual_dose_low=getattr(record, "usual_dose_low", None),
            usual_dose_high=getattr(record, "usual_dose_high", None),
            max_single_dose=getattr(record, "max_single_dose", None),
            max_per_procedure=getattr(record, "max_per_procedure", None),
            dose_calculation_basis=getattr(record, "dose_calculation_basis", "fixed"),
            dose_unit=getattr(record, "dose_unit", "mg"),
            dose_rule_validation_status=getattr(
                record, "dose_rule_validation_status", "pending_review"
            ),
            dose_source_refs=list(getattr(record, "dose_source_refs", []) or []),
            controlled_substance=bool(getattr(record, "controlled_substance", False)),
            controlled_substance_list=getattr(record, "controlled_substance_list", None),
            prescription_form_type=getattr(record, "prescription_form_type", None),
            high_alert_category=getattr(record, "high_alert_category", None),
            recommended_specialty_codes=list(
                getattr(record, "recommended_specialty_codes", []) or []
            ),
            required_specialty_codes=list(getattr(record, "required_specialty_codes", []) or []),
            requires_second_review=bool(getattr(record, "requires_second_review", False)),
            requires_institutional_protocol=bool(
                getattr(record, "requires_institutional_protocol", False)
            ),
            policy_type=getattr(record, "policy_type", "demo_policy"),
            policy_strength=getattr(record, "policy_strength", "warning_only"),
            policy_validation_status=getattr(record, "policy_validation_status", "pending_review"),
            policy_source_refs=list(getattr(record, "policy_source_refs", []) or []),
            psychotropic_class=getattr(record, "psychotropic_class", None),
            psychotropic_profile=dict(getattr(record, "psychotropic_profile", {}) or {}),
            max_daily_dose_mg=record.max_daily_dose_mg,
            max_duration_days=record.max_duration_days,
            max_cumulative_dose_mg=record.max_cumulative_dose_mg,
            continuous_use=getattr(record, "continuous_use", False),
            monitoring_required=getattr(record, "monitoring_required", False),
            monitoring_notes=getattr(record, "monitoring_notes", None),
            condition_specific_limits=dict(record.condition_specific_limits or {}),
            allowed_routes=list(record.allowed_routes or []),
            contraindications=list(record.contraindications or []),
            renal_caution=record.renal_caution,
            hepatic_caution=record.hepatic_caution,
            cardiac_caution=record.cardiac_caution,
            gastrointestinal_caution=record.gastrointestinal_caution,
            elderly_caution=record.elderly_caution,
            mechanism_of_action=getattr(record, "mechanism_of_action", None),
            absorption_notes=getattr(record, "absorption_notes", None),
            distribution_notes=getattr(record, "distribution_notes", None),
            metabolism_organs=list(record.metabolism_organs or []),
            elimination_organs=list(record.elimination_organs or []),
            renal_elimination_level=getattr(record, "renal_elimination_level", "nao_informado"),
            hepatic_metabolism_level=getattr(record, "hepatic_metabolism_level", "nao_informado"),
            cyp_interactions=list(getattr(record, "cyp_interactions", []) or []),
            pharmacodynamic_notes=getattr(record, "pharmacodynamic_notes", None),
            pharmacokinetic_notes=getattr(record, "pharmacokinetic_notes", None),
            clinical_interpretation=getattr(record, "clinical_interpretation", None),
            neuropsychiatric_cautions=list(getattr(record, "neuropsychiatric_cautions", []) or []),
            reproductive_cautions=list(getattr(record, "reproductive_cautions", []) or []),
            organs_involved=list(record.organs_involved or []),
            relevant_adverse_effects=list(record.relevant_adverse_effects or []),
            structured_contraindications=list(record.structured_contraindications or []),
            therapeutic_action=record.therapeutic_action,
            alternative_group=record.alternative_group,
            related_medications=list(record.related_medications or []),
            knowledge_source=record.knowledge_source,
            notes=record.notes,
        )
