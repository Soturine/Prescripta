from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MedicationBase(BaseModel):
    active_ingredient_id: int | None = Field(default=None, gt=0)
    brand_name: str = Field(min_length=2, max_length=160)
    active_ingredient: str = Field(min_length=2, max_length=160)
    commercial_aliases: list[str] = Field(default_factory=list)
    therapeutic_class: str = Field(min_length=2, max_length=160)
    therapeutic_classes: list[str] = Field(default_factory=list)
    source_jurisdiction: str = Field(default="BR", max_length=20)
    evidence_source_type: str = Field(default="demo_seed", max_length=80)
    validation_status: str = Field(default="demo", max_length=40)
    concentration: str | None = Field(default=None, max_length=120)
    pharmaceutical_form: str | None = Field(default=None, max_length=120)
    evidence_source_url: str | None = Field(default=None, max_length=500)
    max_daily_dose_mg: float = Field(gt=0)
    dose_mg_per_kg: float | None = Field(default=None, gt=0)
    dose_by_weight_enabled: bool = False
    usual_dose_low: float | None = Field(default=None, ge=0)
    usual_dose_high: float | None = Field(default=None, ge=0)
    max_single_dose: float | None = Field(default=None, gt=0)
    max_per_procedure: float | None = Field(default=None, gt=0)
    dose_calculation_basis: str = "fixed"
    dose_unit: str = "mg"
    dose_rule_validation_status: str = "pending_review"
    dose_source_refs: list[str] = Field(default_factory=list)
    controlled_substance: bool = False
    controlled_substance_list: str | None = None
    prescription_form_type: str | None = None
    high_alert_category: str | None = None
    recommended_specialty_codes: list[str] = Field(default_factory=list)
    required_specialty_codes: list[str] = Field(default_factory=list)
    requires_second_review: bool = False
    requires_institutional_protocol: bool = False
    policy_type: str = "demo_policy"
    policy_strength: str = "warning_only"
    policy_validation_status: str = "pending_review"
    policy_source_refs: list[str] = Field(default_factory=list)
    policy_version: str = "v8.6.0-demo"
    source_version: str | None = None
    institution_id: str | None = None
    policy_effective_from: datetime | None = None
    policy_effective_until: datetime | None = None
    override_allowed: bool = False
    override_reason_required: bool = True
    second_reviewer_role: str | None = None
    psychotropic_class: str | None = None
    psychotropic_profile: dict = Field(default_factory=dict)
    max_duration_days: int | None = Field(default=None, gt=0, le=365)
    max_cumulative_dose_mg: float | None = Field(default=None, gt=0)
    continuous_use: bool = False
    monitoring_required: bool = False
    monitoring_notes: str | None = None
    condition_specific_limits: dict[str, float] = Field(default_factory=dict)
    allowed_routes: list[str] = Field(default_factory=list, min_length=1)
    contraindications: list[str] = Field(default_factory=list)
    renal_caution: bool = False
    hepatic_caution: bool = False
    cardiac_caution: bool = False
    gastrointestinal_caution: bool = False
    elderly_caution: bool = False
    mechanism_of_action: str | None = None
    absorption_notes: str | None = None
    distribution_notes: str | None = None
    metabolism_organs: list[str] = Field(default_factory=list)
    elimination_organs: list[str] = Field(default_factory=list)
    renal_elimination_level: str = Field(default="nao_informado", max_length=40)
    hepatic_metabolism_level: str = Field(default="nao_informado", max_length=40)
    cyp_interactions: list[str] = Field(default_factory=list)
    pharmacodynamic_notes: str | None = None
    pharmacokinetic_notes: str | None = None
    clinical_interpretation: str | None = None
    neuropsychiatric_cautions: list[str] = Field(default_factory=list)
    reproductive_cautions: list[str] = Field(default_factory=list)
    organs_involved: list[str] = Field(default_factory=list)
    relevant_adverse_effects: list[str] = Field(default_factory=list)
    structured_contraindications: list[str] = Field(default_factory=list)
    therapeutic_action: str | None = Field(default=None, max_length=180)
    alternative_group: str | None = Field(default=None, max_length=120)
    related_medications: list[str] = Field(default_factory=list)
    knowledge_source: str | None = Field(default=None, max_length=220)
    notes: str | None = None


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(BaseModel):
    active_ingredient_id: int | None = Field(default=None, gt=0)
    brand_name: str | None = Field(default=None, min_length=2, max_length=160)
    active_ingredient: str | None = Field(default=None, min_length=2, max_length=160)
    commercial_aliases: list[str] | None = None
    therapeutic_class: str | None = Field(default=None, min_length=2, max_length=160)
    therapeutic_classes: list[str] | None = None
    source_jurisdiction: str | None = Field(default=None, max_length=20)
    evidence_source_type: str | None = Field(default=None, max_length=80)
    validation_status: str | None = Field(default=None, max_length=40)
    concentration: str | None = Field(default=None, max_length=120)
    pharmaceutical_form: str | None = Field(default=None, max_length=120)
    evidence_source_url: str | None = Field(default=None, max_length=500)
    max_daily_dose_mg: float | None = Field(default=None, gt=0)
    dose_mg_per_kg: float | None = Field(default=None, gt=0)
    dose_by_weight_enabled: bool | None = None
    usual_dose_low: float | None = Field(default=None, ge=0)
    usual_dose_high: float | None = Field(default=None, ge=0)
    max_single_dose: float | None = Field(default=None, gt=0)
    max_per_procedure: float | None = Field(default=None, gt=0)
    dose_calculation_basis: str | None = None
    dose_unit: str | None = None
    dose_rule_validation_status: str | None = None
    dose_source_refs: list[str] | None = None
    controlled_substance: bool | None = None
    controlled_substance_list: str | None = None
    prescription_form_type: str | None = None
    high_alert_category: str | None = None
    recommended_specialty_codes: list[str] | None = None
    required_specialty_codes: list[str] | None = None
    requires_second_review: bool | None = None
    requires_institutional_protocol: bool | None = None
    policy_type: str | None = None
    policy_strength: str | None = None
    policy_validation_status: str | None = None
    policy_source_refs: list[str] | None = None
    policy_version: str | None = None
    source_version: str | None = None
    institution_id: str | None = None
    policy_effective_from: datetime | None = None
    policy_effective_until: datetime | None = None
    override_allowed: bool | None = None
    override_reason_required: bool | None = None
    second_reviewer_role: str | None = None
    psychotropic_class: str | None = None
    psychotropic_profile: dict | None = None
    max_duration_days: int | None = Field(default=None, gt=0, le=365)
    max_cumulative_dose_mg: float | None = Field(default=None, gt=0)
    continuous_use: bool | None = None
    monitoring_required: bool | None = None
    monitoring_notes: str | None = None
    condition_specific_limits: dict[str, float] | None = None
    allowed_routes: list[str] | None = None
    contraindications: list[str] | None = None
    renal_caution: bool | None = None
    hepatic_caution: bool | None = None
    cardiac_caution: bool | None = None
    gastrointestinal_caution: bool | None = None
    elderly_caution: bool | None = None
    mechanism_of_action: str | None = None
    absorption_notes: str | None = None
    distribution_notes: str | None = None
    metabolism_organs: list[str] | None = None
    elimination_organs: list[str] | None = None
    renal_elimination_level: str | None = Field(default=None, max_length=40)
    hepatic_metabolism_level: str | None = Field(default=None, max_length=40)
    cyp_interactions: list[str] | None = None
    pharmacodynamic_notes: str | None = None
    pharmacokinetic_notes: str | None = None
    clinical_interpretation: str | None = None
    neuropsychiatric_cautions: list[str] | None = None
    reproductive_cautions: list[str] | None = None
    organs_involved: list[str] | None = None
    relevant_adverse_effects: list[str] | None = None
    structured_contraindications: list[str] | None = None
    therapeutic_action: str | None = Field(default=None, max_length=180)
    alternative_group: str | None = Field(default=None, max_length=120)
    related_medications: list[str] | None = None
    knowledge_source: str | None = Field(default=None, max_length=220)
    notes: str | None = None


class MedicationRead(MedicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
