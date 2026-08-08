from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
    inspect,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class PatientModel(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    institution_id: Mapped[str] = mapped_column(String(100), default="demo", nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    sex_for_dosing_calculation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    email: Mapped[str | None] = mapped_column(String(220), nullable=True)
    mother_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    allergies: Mapped[list[str]] = mapped_column(JSON, default=list)
    comorbidities: Mapped[list[str]] = mapped_column(JSON, default=list)
    current_medications: Mapped[list[str]] = mapped_column(JSON, default=list)
    renal_condition: Mapped[str | None] = mapped_column(String(120), nullable=True)
    hepatic_condition: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cardiac_condition: Mapped[str | None] = mapped_column(String(120), nullable=True)
    gastrointestinal_history: Mapped[str | None] = mapped_column(String(160), nullable=True)
    hypertension: Mapped[bool] = mapped_column(default=False, nullable=False)
    diabetes: Mapped[bool] = mapped_column(default=False, nullable=False)
    pregnancy_or_lactation: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    mental_health_factors: Mapped[list[str]] = mapped_column(JSON, default=list)
    reproductive_gynecologic_factors: Mapped[list[str]] = mapped_column(JSON, default=list)
    adverse_reactions: Mapped[list[str]] = mapped_column(JSON, default=list)
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_profile_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    clinical_profile_completeness_score: Mapped[float] = mapped_column(
        Float, default=0, nullable=False
    )


class PatientPsychologicalContextModel(Base):
    """Segmento confidencial; somente fatores minimizados são copiados ao paciente."""

    __tablename__ = "patient_psychological_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"), nullable=False, unique=True, index=True
    )
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False)
    medication_safety_factors: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    confidential_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    consent_status: Mapped[str] = mapped_column(
        String(40), default="policy_required", nullable=False
    )
    policy_reference: Mapped[str | None] = mapped_column(String(160), nullable=True)
    updated_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class ActiveIngredientModel(Base):
    __tablename__ = "active_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dcb_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    synonyms: Mapped[list[str]] = mapped_column(JSON, default=list)
    therapeutic_classes: Mapped[list[str]] = mapped_column(JSON, default=list)
    common_brands: Mapped[list[str]] = mapped_column(JSON, default=list)
    jurisdiction: Mapped[str] = mapped_column(String(20), default="BR", nullable=False)
    source: Mapped[str] = mapped_column(String(80), default="demo_seed", nullable=False)
    validation_status: Mapped[str] = mapped_column(String(40), default="demo", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class DrugProductModel(Base):
    __tablename__ = "drug_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    active_ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("active_ingredients.id"), nullable=False, index=True
    )
    commercial_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    manufacturer: Mapped[str | None] = mapped_column(String(160), nullable=True)
    concentration: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pharmaceutical_form: Mapped[str | None] = mapped_column(String(120), nullable=True)
    allowed_routes: Mapped[list[str]] = mapped_column(JSON, default=list)
    anvisa_registration_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    bula_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(String(80), default="demo_seed", nullable=False)
    validation_status: Mapped[str] = mapped_column(String(40), default="demo", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class MedicationKnowledgeSourceModel(Base):
    __tablename__ = "medication_knowledge_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    active_ingredient_id: Mapped[int | None] = mapped_column(
        ForeignKey("active_ingredients.id"), nullable=True, index=True
    )
    drug_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("drug_products.id"), nullable=True, index=True
    )
    source_name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(20), default="BR", nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidence_sections: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence_level: Mapped[str] = mapped_column(String(40), default="demo", nullable=False)
    validation_status: Mapped[str] = mapped_column(String(40), default="demo", nullable=False)
    reviewer: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class MedicationCounselingSummaryModel(Base):
    __tablename__ = "medication_counseling_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    active_ingredient_id: Mapped[int | None] = mapped_column(
        ForeignKey("active_ingredients.id"), nullable=True, index=True
    )
    medication_id: Mapped[int | None] = mapped_column(
        ForeignKey("medications.id"), nullable=True, index=True
    )
    source_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(20), default="BR", nullable=False)
    source_name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    validation_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    generated_by: Mapped[str] = mapped_column(
        String(40), default="fallback_deterministic", nullable=False
    )
    provider_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    confidence: Mapped[str] = mapped_column(String(40), default="low", nullable=False)
    requires_review: Mapped[bool] = mapped_column(default=True, nullable=False)
    main_adverse_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    patient_relevant_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    activity_warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    driving_warning: Mapped[bool] = mapped_column(default=False, nullable=False)
    machine_operation_warning: Mapped[bool] = mapped_column(default=False, nullable=False)
    work_at_height_warning: Mapped[bool] = mapped_column(default=False, nullable=False)
    fall_risk_warning: Mapped[bool] = mapped_column(default=False, nullable=False)
    sedation_attention_warning: Mapped[bool] = mapped_column(default=False, nullable=False)
    sleep_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    appetite_weight_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    mood_behavior_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    libido_sexual_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    neurologic_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    tremor_warning: Mapped[bool] = mapped_column(default=False, nullable=False)
    headache_warning: Mapped[bool] = mapped_column(default=False, nullable=False)
    temperature_regulation_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    blood_pressure_warning: Mapped[bool] = mapped_column(default=False, nullable=False)
    gastrointestinal_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    renal_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    hepatic_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    reproductive_contraceptive_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    red_flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    monitoring_required: Mapped[list[str]] = mapped_column(JSON, default=list)
    patient_friendly_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    professional_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    extracted_evidence: Mapped[list[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class ClinicalVocabularyModel(Base):
    __tablename__ = "clinical_vocabulary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(180), nullable=False)
    normalized_label: Mapped[str] = mapped_column(String(180), nullable=False)
    severity_weight: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class MedicationModel(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    active_ingredient_id: Mapped[int | None] = mapped_column(
        ForeignKey("active_ingredients.id"), nullable=True, index=True
    )
    brand_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    active_ingredient: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    commercial_aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    therapeutic_class: Mapped[str] = mapped_column(String(160), nullable=False)
    therapeutic_classes: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_jurisdiction: Mapped[str] = mapped_column(String(20), default="BR", nullable=False)
    evidence_source_type: Mapped[str] = mapped_column(
        String(80), default="demo_seed", nullable=False
    )
    validation_status: Mapped[str] = mapped_column(String(40), default="demo", nullable=False)
    concentration: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pharmaceutical_form: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidence_source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    max_daily_dose_mg: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    dose_dimension: Mapped[str] = mapped_column(
        String(40), default="per_administration", nullable=False
    )
    max_daily_dose_unit: Mapped[str] = mapped_column(String(40), default="mg", nullable=False)
    dose_mg_per_kg: Mapped[Decimal | None] = mapped_column(Numeric(24, 12), nullable=True)
    dose_by_weight_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    usual_dose_low: Mapped[Decimal | None] = mapped_column(Numeric(24, 12), nullable=True)
    usual_dose_high: Mapped[Decimal | None] = mapped_column(Numeric(24, 12), nullable=True)
    usual_dose_unit: Mapped[str] = mapped_column(String(40), default="mg", nullable=False)
    usual_range_scope: Mapped[str] = mapped_column(
        String(40), default="daily", nullable=False
    )
    max_single_dose: Mapped[Decimal | None] = mapped_column(Numeric(24, 12), nullable=True)
    max_single_dose_unit: Mapped[str] = mapped_column(String(40), default="mg", nullable=False)
    max_per_procedure: Mapped[Decimal | None] = mapped_column(Numeric(24, 12), nullable=True)
    max_per_procedure_unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    max_rate: Mapped[Decimal | None] = mapped_column(Numeric(24, 12), nullable=True)
    rate_unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    dose_calculation_basis: Mapped[str] = mapped_column(String(40), default="fixed", nullable=False)
    dose_unit: Mapped[str] = mapped_column(String(40), default="mg", nullable=False)
    dose_rule_validation_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False
    )
    dose_rule_version: Mapped[str] = mapped_column(
        String(80), default="demo_dose_2026-07-r1", nullable=False
    )
    dose_rounding_policy: Mapped[str] = mapped_column(
        String(80), default="prescripta-half-even-v1", nullable=False
    )
    dose_calculation_precision: Mapped[str] = mapped_column(
        String(20), default="0.0001", nullable=False
    )
    dose_source_refs: Mapped[list[str]] = mapped_column(JSON, default=list)
    controlled_substance: Mapped[bool] = mapped_column(default=False, nullable=False)
    controlled_substance_list: Mapped[str | None] = mapped_column(String(80), nullable=True)
    prescription_form_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    high_alert_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recommended_specialty_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    required_specialty_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    requires_second_review: Mapped[bool] = mapped_column(default=False, nullable=False)
    requires_institutional_protocol: Mapped[bool] = mapped_column(default=False, nullable=False)
    policy_type: Mapped[str] = mapped_column(String(60), default="demo_policy", nullable=False)
    policy_strength: Mapped[str] = mapped_column(String(40), default="warning_only", nullable=False)
    policy_validation_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False
    )
    policy_source_refs: Mapped[list[str]] = mapped_column(JSON, default=list)
    policy_version: Mapped[str] = mapped_column(
        String(40), default="demo_policy_2026-07-r1", nullable=False
    )
    source_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    institution_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    policy_effective_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    policy_effective_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    override_allowed: Mapped[bool] = mapped_column(default=False, nullable=False)
    override_reason_required: Mapped[bool] = mapped_column(default=True, nullable=False)
    second_reviewer_role: Mapped[str | None] = mapped_column(String(40), nullable=True)
    psychotropic_class: Mapped[str | None] = mapped_column(String(100), nullable=True)
    psychotropic_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    max_duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_cumulative_dose_mg: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 12), nullable=True
    )
    max_cumulative_dose_unit: Mapped[str] = mapped_column(
        String(40), default="mg", nullable=False
    )
    continuous_use: Mapped[bool] = mapped_column(default=False, nullable=False)
    monitoring_required: Mapped[bool] = mapped_column(default=False, nullable=False)
    monitoring_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition_specific_limits: Mapped[dict] = mapped_column(JSON, default=dict)
    allowed_routes: Mapped[list[str]] = mapped_column(JSON, default=list)
    contraindications: Mapped[list[str]] = mapped_column(JSON, default=list)
    renal_caution: Mapped[bool] = mapped_column(default=False, nullable=False)
    hepatic_caution: Mapped[bool] = mapped_column(default=False, nullable=False)
    cardiac_caution: Mapped[bool] = mapped_column(default=False, nullable=False)
    gastrointestinal_caution: Mapped[bool] = mapped_column(default=False, nullable=False)
    elderly_caution: Mapped[bool] = mapped_column(default=False, nullable=False)
    mechanism_of_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    absorption_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    distribution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metabolism_organs: Mapped[list[str]] = mapped_column(JSON, default=list)
    elimination_organs: Mapped[list[str]] = mapped_column(JSON, default=list)
    renal_elimination_level: Mapped[str] = mapped_column(
        String(40), default="nao_informado", nullable=False
    )
    hepatic_metabolism_level: Mapped[str] = mapped_column(
        String(40), default="nao_informado", nullable=False
    )
    cyp_interactions: Mapped[list[str]] = mapped_column(JSON, default=list)
    pharmacodynamic_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pharmacokinetic_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    neuropsychiatric_cautions: Mapped[list[str]] = mapped_column(JSON, default=list)
    reproductive_cautions: Mapped[list[str]] = mapped_column(JSON, default=list)
    organs_involved: Mapped[list[str]] = mapped_column(JSON, default=list)
    relevant_adverse_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    structured_contraindications: Mapped[list[str]] = mapped_column(JSON, default=list)
    therapeutic_action: Mapped[str | None] = mapped_column(String(180), nullable=True)
    alternative_group: Mapped[str | None] = mapped_column(String(120), nullable=True)
    related_medications: Mapped[list[str]] = mapped_column(JSON, default=list)
    knowledge_source: Mapped[str | None] = mapped_column(String(220), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class PatientIdentifierModel(Base):
    __tablename__ = "patient_identifiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    identifier_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    identifier_value_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    issuing_system: Mapped[str | None] = mapped_column(String(160), nullable=True)
    display_masked: Mapped[str] = mapped_column(String(80), nullable=False)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class PatientFunctionalProfileModel(Base):
    __tablename__ = "patient_functional_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"), nullable=False, unique=True, index=True
    )
    drives_regularly: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    professional_driver: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    operates_machinery: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    works_at_height: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    fall_risk_activity: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    night_shift: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    caregiver_responsibility: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    high_attention_activity: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    frequent_alcohol_use: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    history_of_falls: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    low_tolerance_to_sedation_or_dizziness: Mapped[bool | None] = mapped_column(
        default=None, nullable=True
    )
    source: Mapped[str] = mapped_column(String(80), default="manual", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class ClinicalImportBatchModel(Base):
    __tablename__ = "clinical_import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_system: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    imported_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), nullable=True)
    consent_id: Mapped[int | None] = mapped_column(ForeignKey("consent_records.id"), nullable=True)
    status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    errors: Mapped[list[str]] = mapped_column(JSON, default=list)


class ClinicalSourceRecordModel(Base):
    __tablename__ = "clinical_source_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("clinical_import_batches.id"), nullable=False, index=True
    )
    record_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    mapped_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    accepted_by_user: Mapped[bool] = mapped_column(default=False, nullable=False)
    rejected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class ClinicalReconciliationDecisionModel(Base):
    __tablename__ = "clinical_reconciliation_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("clinical_import_batches.id"), nullable=False, index=True
    )
    source_record_id: Mapped[int | None] = mapped_column(
        ForeignKey("clinical_source_records.id"), nullable=True, index=True
    )
    item_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    record_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    field_path: Mapped[str] = mapped_column(String(160), nullable=False)
    current_value: Mapped[dict] = mapped_column(JSON, default=dict)
    imported_value: Mapped[dict] = mapped_column(JSON, default=dict)
    source_system: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    badge: Mapped[str] = mapped_column(String(40), default="novo", nullable=False)
    suggestion: Mapped[str] = mapped_column(String(80), default="review_manually", nullable=False)
    decision: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class ConsentRecordModel(Base):
    __tablename__ = "consent_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), nullable=True)
    authorized_by: Mapped[str] = mapped_column(String(160), nullable=False)
    purpose: Mapped[str] = mapped_column(String(240), nullable=False)
    source_system: Mapped[str] = mapped_column(String(120), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IntegrationAuditLogModel(Base):
    __tablename__ = "integration_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), nullable=True)
    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("clinical_import_batches.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_system: Mapped[str] = mapped_column(String(120), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class AIProviderCredentialModel(Base):
    __tablename__ = "ai_provider_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    masked_api_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_persistent: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class AIProviderSettingsModel(Base):
    __tablename__ = "ai_provider_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), default="fallback", nullable=False)
    selected_model: Mapped[str | None] = mapped_column(String(160), nullable=True)
    enable_external_calls: Mapped[bool] = mapped_column(default=False, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    max_output_tokens: Mapped[int] = mapped_column(Integer, default=900, nullable=False)
    use_json_mode: Mapped[bool] = mapped_column(default=True, nullable=False)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class AIProviderModelCacheModel(Base):
    __tablename__ = "ai_provider_model_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(220), nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(JSON, default=list)
    context_window: Mapped[int | None] = mapped_column(Integer, nullable=True)
    supports_json: Mapped[bool] = mapped_column(default=False, nullable=False)
    supports_structured_output: Mapped[bool] = mapped_column(default=False, nullable=False)
    supports_tools: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_available: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="cache", nullable=False)
    refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class AIProviderRuntimeStateModel(Base):
    __tablename__ = "ai_provider_runtime_states"

    provider: Mapped[str] = mapped_column(String(40), primary_key=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    degraded_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class AIConfigurationAuditLogModel(Base):
    __tablename__ = "ai_configuration_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    model: Mapped[str | None] = mapped_column(String(160), nullable=True)
    external_calls_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    result: Mapped[str] = mapped_column(String(40), nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class SpecialtyModel(Base):
    __tablename__ = "specialties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    demo_only: Mapped[bool] = mapped_column(default=True, nullable=False)
    requires_rqe_for_real_use: Mapped[bool] = mapped_column(default=False, nullable=False)
    credential_verification_status: Mapped[str] = mapped_column(
        String(40), default="demo_unverified", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    profession: Mapped[str] = mapped_column(
        String(40), default="administration", nullable=False, index=True
    )
    capabilities: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    capability_policy_version: Mapped[str] = mapped_column(
        String(40), default="explicit-v1", nullable=False
    )
    institution_id: Mapped[str] = mapped_column(String(100), default="demo", nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    mfa_secret_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    specialty_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    specialty_codes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    credential_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    credential_code_demo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    credential_region: Mapped[str | None] = mapped_column(String(20), nullable=True)
    credential_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    institutional_policy: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sensitive_data_segments: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    crm_demo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    crm_uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    rqe_demo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    credential_verification_status: Mapped[str] = mapped_column(
        String(40), default="demo_unverified", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class PatientAccessGrantModel(Base):
    __tablename__ = "patient_access_grants"
    __table_args__ = (UniqueConstraint("patient_id", "user_id", "permission"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    permission: Mapped[str] = mapped_column(String(40), default="clinical", nullable=False)
    institution_id: Mapped[str] = mapped_column(String(100), default="demo", nullable=False)
    capability: Mapped[str] = mapped_column(
        String(80), default="patient.read", nullable=False, index=True
    )
    purpose: Mapped[str] = mapped_column(
        String(40), default="treatment", nullable=False, index=True
    )
    granted_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    revocation_reason: Mapped[str | None] = mapped_column(String(220), nullable=True)
    care_episode_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(220), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class CareTeamMembershipModel(Base):
    __tablename__ = "care_team_memberships"
    __table_args__ = (UniqueConstraint("patient_id", "user_id", "team_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    team_code: Mapped[str] = mapped_column(String(80), nullable=False)
    care_role: Mapped[str] = mapped_column(String(80), nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    purpose: Mapped[str] = mapped_column(String(40), default="treatment", nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    granted_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class CareEpisodeAssignmentModel(Base):
    __tablename__ = "care_episode_assignments"
    __table_args__ = (UniqueConstraint("episode_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    episode_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    capabilities: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    purpose: Mapped[str] = mapped_column(String(40), default="treatment", nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    granted_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class BreakGlassAccessModel(Base):
    __tablename__ = "break_glass_accesses"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    capability: Mapped[str] = mapped_column(String(80), nullable=False)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(30), default="pending_review", nullable=False, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    review_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    objects_accessed: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class LoginThrottleModel(Base):
    __tablename__ = "login_throttles"

    identifier_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PrescriptionAuditModel(Base):
    __tablename__ = "prescription_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), nullable=True)
    medication_id: Mapped[int | None] = mapped_column(ForeignKey("medications.id"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    user_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    user_email: Mapped[str | None] = mapped_column(String(220), nullable=True)
    patient_name: Mapped[str] = mapped_column(String(160), nullable=False)
    medication_name: Mapped[str] = mapped_column(String(160), nullable=False)
    dose_mg: Mapped[float | None] = mapped_column(Float, nullable=True)
    frequency_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    route: Mapped[str] = mapped_column(String(80), nullable=False)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    indication: Mapped[str | None] = mapped_column(String(180), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(40), nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    alerts: Mapped[list[dict]] = mapped_column(JSON, default=list)
    dose_intelligence: Mapped[dict] = mapped_column(JSON, default=dict)
    psychotropic_safety: Mapped[list[dict]] = mapped_column(JSON, default=list)
    prescribing_policy: Mapped[dict] = mapped_column(JSON, default=dict)
    dose_input: Mapped[dict] = mapped_column(JSON, default=dict)
    clinical_decision: Mapped[dict] = mapped_column(JSON, default=dict)
    clinical_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    snapshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    hash_algorithm: Mapped[str | None] = mapped_column(String(80), nullable=True)
    snapshot_schema_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)


class CDSIdempotencyModel(Base):
    __tablename__ = "cds_idempotency"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class DecisionOverrideModel(Base):
    __tablename__ = "decision_overrides"
    __table_args__ = (UniqueConstraint("prescription_audit_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prescription_audit_id: Mapped[int] = mapped_column(
        ForeignKey("prescription_audits.id"), nullable=False, index=True
    )
    requested_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(40), default="pending_second_review", nullable=False, index=True
    )
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    review_decision: Mapped[str | None] = mapped_column(String(40), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


@event.listens_for(PrescriptionAuditModel, "before_update")
def _preserve_immutable_clinical_snapshot(_mapper, _connection, target) -> None:
    state = inspect(target)
    immutable_fields = {
        "clinical_snapshot",
        "snapshot_hash",
        "hash_algorithm",
        "snapshot_schema_version",
        "clinical_decision",
        "correlation_id",
    }
    if any(state.attrs[field].history.has_changes() for field in immutable_fields):
        raise ValueError("O snapshot clínico e sua decisão são imutáveis.")


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    user_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    user_email: Mapped[str | None] = mapped_column(String(220), nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(40), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    risk_level: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    status: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class GeneratedReportModel(Base):
    __tablename__ = "generated_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    generated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    template_version: Mapped[str] = mapped_column(String(80), nullable=False)
    prescripta_version: Mapped[str] = mapped_column(String(40), nullable=False)
    evidence_bundle_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    ai_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(160), nullable=True)
    ai_prompt_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ai_used: Mapped[bool] = mapped_column(default=False, nullable=False)
    fallback_used: Mapped[bool] = mapped_column(default=True, nullable=False)
    anonymized: Mapped[bool] = mapped_column(default=False, nullable=False)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="generated", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class EmergencyProtocolVersionModel(Base):
    __tablename__ = "emergency_protocol_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    protocol_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(20), default="BR", nullable=False)
    source_name: Mapped[str] = mapped_column(String(220), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_version: Mapped[str | None] = mapped_column(String(160), nullable=True)
    validation_status: Mapped[str] = mapped_column(
        String(40), default="demo_curated", nullable=False, index=True
    )
    reviewed_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class EmergencyProtocolRunModel(Base):
    __tablename__ = "emergency_protocol_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    protocol_version_id: Mapped[int] = mapped_column(
        ForeignKey("emergency_protocol_versions.id"), nullable=False, index=True
    )
    protocol_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    protocol_title: Mapped[str] = mapped_column(String(180), nullable=False)
    protocol_category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    protocol_severity: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    protocol_version: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    audit_event_id: Mapped[int | None] = mapped_column(ForeignKey("audit_events.id"), nullable=True)
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    selected_step_orders: Mapped[list[int]] = mapped_column(JSON, default=list)
    patient_context_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    triage_flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    calculated_values: Mapped[list[dict]] = mapped_column(JSON, default=list)
    evidence_refs: Mapped[list[str]] = mapped_column(JSON, default=list)
    timeline: Mapped[list[dict]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(40), default="recorded", nullable=False, index=True)
    ai_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(160), nullable=True)
    fallback_used: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class EmergencyProtocolRunStepModel(Base):
    __tablename__ = "emergency_protocol_run_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("emergency_protocol_runs.id"), nullable=False, index=True
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    evidence_ref: Mapped[str] = mapped_column(String(120), nullable=False)
    checked: Mapped[bool] = mapped_column(default=False, nullable=False)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EmergencyProtocolRunReportModel(Base):
    __tablename__ = "emergency_protocol_run_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("emergency_protocol_runs.id"), nullable=False, index=True
    )
    generated_report_id: Mapped[int] = mapped_column(
        ForeignKey("generated_reports.id"), nullable=False, index=True
    )
    report_type: Mapped[str] = mapped_column(
        String(80), default="protocol_run_report", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class PatientClinicalTimelineEventModel(Base):
    __tablename__ = "patient_clinical_timeline_events"
    __table_args__ = (UniqueConstraint("institution_id", "source_ref"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    institution_id: Mapped[str] = mapped_column(
        String(100), default="demo", nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), default="manual", nullable=False)
    source_system: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_ref: Mapped[str | None] = mapped_column(String(220), nullable=True)
    concept_system: Mapped[str | None] = mapped_column(String(40), nullable=True)
    concept_code: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    concept_label: Mapped[str | None] = mapped_column(String(240), nullable=True)
    event_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    visibility_classification: Mapped[str] = mapped_column(
        String(40), default="clinical", nullable=False
    )
    validation_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class PatientClinicalDocumentModel(Base):
    __tablename__ = "patient_clinical_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(80), default="clinical_note", nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), default="manual_text", nullable=False)
    source_system: Mapped[str | None] = mapped_column(String(120), nullable=True)
    document_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    structured_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    extracted_entities: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    validation_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    review_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)


class PatientDocumentExtractionModel(Base):
    __tablename__ = "patient_document_extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("patient_clinical_documents.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(80), default="fallback", nullable=False)
    model: Mapped[str | None] = mapped_column(String(160), nullable=True)
    extracted_entities: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    validation_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    review_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class PatientMedicationHistoryModel(Base):
    __tablename__ = "patient_medication_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    medication_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    active_ingredient: Mapped[str | None] = mapped_column(String(160), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="historical", nullable=False)
    source_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("patient_clinical_documents.id"), nullable=True
    )
    validation_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class MedicationKnowledgeCurationModel(Base):
    __tablename__ = "medication_knowledge_curation_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    query: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(180), default="fonte_informada", nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_text_excerpt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    extracted_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    provider: Mapped[str] = mapped_column(String(80), default="fallback", nullable=False)
    model: Mapped[str | None] = mapped_column(String(160), nullable=True)
    validation_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    review_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class InstitutionalClinicalProtocolModel(Base):
    __tablename__ = "institutional_clinical_protocols"
    __table_args__ = (UniqueConstraint("institution_id", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False)
    program: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class InstitutionalClinicalProtocolVersionModel(Base):
    __tablename__ = "institutional_clinical_protocol_versions"
    __table_args__ = (UniqueConstraint("protocol_id", "version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    protocol_id: Mapped[int] = mapped_column(
        ForeignKey("institutional_clinical_protocols.id"), nullable=False, index=True
    )
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    review_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source_refs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    clinical_context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    eligible_professions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    required_capability: Mapped[str] = mapped_column(String(100), nullable=False)
    required_parameters: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    contraindications: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    requires_second_review: Mapped[bool] = mapped_column(default=False, nullable=False)
    second_reviewer_role: Mapped[str | None] = mapped_column(String(40), nullable=True)
    override_policy: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class ProtocolPrescribingScopeModel(Base):
    __tablename__ = "protocol_prescribing_scopes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    protocol_version_id: Mapped[int] = mapped_column(
        ForeignKey("institutional_clinical_protocol_versions.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    allowed_routes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    dose_min: Mapped[Decimal | None] = mapped_column(Numeric(24, 12), nullable=True)
    dose_max: Mapped[Decimal | None] = mapped_column(Numeric(24, 12), nullable=True)
    dose_unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    frequency_min_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frequency_max_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_age_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_age_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    max_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    constraints: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class ProtocolMedicationScopeModel(Base):
    __tablename__ = "protocol_medication_scopes"
    __table_args__ = (UniqueConstraint("protocol_version_id", "medication_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    protocol_version_id: Mapped[int] = mapped_column(
        ForeignKey("institutional_clinical_protocol_versions.id"), nullable=False, index=True
    )
    medication_id: Mapped[int] = mapped_column(
        ForeignKey("medications.id"), nullable=False, index=True
    )
    concept_set_ref: Mapped[str | None] = mapped_column(String(160), nullable=True)


class ProtocolConditionScopeModel(Base):
    __tablename__ = "protocol_condition_scopes"
    __table_args__ = (
        UniqueConstraint("protocol_version_id", "terminology_system", "condition_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    protocol_version_id: Mapped[int] = mapped_column(
        ForeignKey("institutional_clinical_protocol_versions.id"), nullable=False, index=True
    )
    terminology_system: Mapped[str] = mapped_column(String(80), nullable=False)
    terminology_version: Mapped[str] = mapped_column(String(80), nullable=False)
    condition_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(220), nullable=False)


class ProtocolCredentialRequirementModel(Base):
    __tablename__ = "protocol_credential_requirements"
    __table_args__ = (UniqueConstraint("protocol_version_id", "credential_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    protocol_version_id: Mapped[int] = mapped_column(
        ForeignKey("institutional_clinical_protocol_versions.id"), nullable=False, index=True
    )
    credential_type: Mapped[str] = mapped_column(String(80), nullable=False)
    credential_region: Mapped[str | None] = mapped_column(String(20), nullable=True)
    verification_required: Mapped[bool] = mapped_column(default=True, nullable=False)
    unexpired_required: Mapped[bool] = mapped_column(default=True, nullable=False)


class PharmacyInterventionModel(Base):
    __tablename__ = "pharmacy_interventions"
    __table_args__ = (UniqueConstraint("institution_id", "idempotency_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    prescription_audit_id: Mapped[int | None] = mapped_column(
        ForeignKey("prescription_audits.id"), nullable=True, index=True
    )
    medication_id: Mapped[int | None] = mapped_column(
        ForeignKey("medications.id"), nullable=True, index=True
    )
    pharmacist_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    intervention_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    source_refs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    dose_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cosignature_required: Mapped[bool] = mapped_column(default=False, nullable=False)
    cosigned_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    cosigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    accepted: Mapped[bool | None] = mapped_column(nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class PharmacyInterventionEventModel(Base):
    __tablename__ = "pharmacy_intervention_events"
    __table_args__ = (UniqueConstraint("intervention_id", "version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intervention_id: Mapped[int] = mapped_column(
        ForeignKey("pharmacy_interventions.id"), nullable=False, index=True
    )
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    to_status: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class MedicationReconciliationModel(Base):
    __tablename__ = "medication_reconciliations"
    __table_args__ = (UniqueConstraint("institution_id", "idempotency_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    pharmacist_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="in_review", nullable=False, index=True)
    source_refs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MedicationReconciliationItemModel(Base):
    __tablename__ = "medication_reconciliation_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reconciliation_id: Mapped[int] = mapped_column(
        ForeignKey("medication_reconciliations.id"), nullable=False, index=True
    )
    medication_id: Mapped[int | None] = mapped_column(
        ForeignKey("medications.id"), nullable=True, index=True
    )
    medication_name: Mapped[str] = mapped_column(String(180), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(220), nullable=False)
    discrepancy: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(40), default="needs_review", nullable=False, index=True
    )
    action: Mapped[str | None] = mapped_column(String(80), nullable=True)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    formulation: Mapped[str | None] = mapped_column(String(160), nullable=True)
    concentration: Mapped[str | None] = mapped_column(String(120), nullable=True)
    history: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class MedicationFormulationReviewModel(Base):
    __tablename__ = "medication_formulation_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    intervention_id: Mapped[int | None] = mapped_column(
        ForeignKey("pharmacy_interventions.id"), nullable=True, index=True
    )
    reconciliation_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("medication_reconciliation_items.id"), nullable=True, index=True
    )
    reviewer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    dose_input: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    formulation: Mapped[str] = mapped_column(String(160), nullable=False)
    concentration: Mapped[str] = mapped_column(String(120), nullable=False)
    rounding_policy: Mapped[str] = mapped_column(String(80), nullable=False)
    result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


def _uuid() -> str:
    return str(uuid4())


class ResearchStudyModel(Base):
    __tablename__ = "research_studies"
    __table_args__ = (UniqueConstraint("institution_id", "slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    research_question: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    design: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    current_protocol_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    demo_only: Mapped[bool] = mapped_column(default=True, nullable=False)
    data_source_classification: Mapped[str] = mapped_column(
        String(40), default="synthetic", nullable=False
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class StudyProtocolVersionModel(Base):
    __tablename__ = "study_protocol_versions"
    __table_args__ = (UniqueConstraint("study_id", "version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    study_id: Mapped[str] = mapped_column(
        ForeignKey("research_studies.id"), nullable=False, index=True
    )
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    population: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    exposure: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    comparator: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    outcome: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    index_date: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    washout: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    follow_up: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    censoring: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    inclusion: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    exclusion: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    covariates: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    missing_data_strategy: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    statistical_plan: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    limitations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source_refs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    authored_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class ConceptSetModel(Base):
    __tablename__ = "concept_sets"
    __table_args__ = (UniqueConstraint("institution_id", "name", "domain"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reviewer_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    current_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class ConceptSetVersionModel(Base):
    __tablename__ = "concept_set_versions"
    __table_args__ = (UniqueConstraint("concept_set_id", "version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    concept_set_id: Mapped[str] = mapped_column(
        ForeignKey("concept_sets.id"), nullable=False, index=True
    )
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(40), default="ai_suggested", nullable=False, index=True
    )
    terminology_versions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    include_descendants: Mapped[bool] = mapped_column(default=False, nullable=False)
    source_refs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    license_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    authored_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class ConceptSetMemberModel(Base):
    __tablename__ = "concept_set_members"
    __table_args__ = (
        UniqueConstraint("concept_set_version_id", "terminology_system", "concept_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    concept_set_version_id: Mapped[str] = mapped_column(
        ForeignKey("concept_set_versions.id"), nullable=False, index=True
    )
    terminology_system: Mapped[str] = mapped_column(String(40), nullable=False)
    terminology_version: Mapped[str] = mapped_column(String(80), nullable=False)
    concept_id: Mapped[str | None] = mapped_column(String(80))
    concept_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(240), nullable=False)
    excluded: Mapped[bool] = mapped_column(default=False, nullable=False)


class CohortDefinitionModel(Base):
    __tablename__ = "cohort_definitions"
    __table_args__ = (UniqueConstraint("study_id", "name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    study_id: Mapped[str] = mapped_column(
        ForeignKey("research_studies.id"), nullable=False, index=True
    )
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    current_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class CohortDefinitionVersionModel(Base):
    __tablename__ = "cohort_definition_versions"
    __table_args__ = (UniqueConstraint("cohort_definition_id", "version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    cohort_definition_id: Mapped[str] = mapped_column(
        ForeignKey("cohort_definitions.id"), nullable=False, index=True
    )
    study_id: Mapped[str] = mapped_column(
        ForeignKey("research_studies.id"), nullable=False, index=True
    )
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    definition: Mapped[dict] = mapped_column(JSON, nullable=False)
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    query_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    authored_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class CohortCriterionModel(Base):
    __tablename__ = "cohort_criteria"
    __table_args__ = (UniqueConstraint("cohort_version_id", "sequence"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    cohort_version_id: Mapped[str] = mapped_column(
        ForeignKey("cohort_definition_versions.id"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    group_type: Mapped[str] = mapped_column(String(20), nullable=False)
    criterion: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    operator: Mapped[str | None] = mapped_column(String(20))
    field: Mapped[str | None] = mapped_column(String(80))
    value: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    concept_set_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("concept_set_versions.id"), index=True
    )
    window: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    criterion_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class OutcomeDefinitionModel(Base):
    __tablename__ = "outcome_definitions"
    __table_args__ = (UniqueConstraint("study_id", "name", "version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    study_id: Mapped[str] = mapped_column(
        ForeignKey("research_studies.id"), nullable=False, index=True
    )
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False)
    domain: Mapped[str] = mapped_column(String(60), nullable=False)
    concept_set_version_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    event_qualification: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    observation_window: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    temporal_relationship: Mapped[str] = mapped_column(String(80), nullable=False)
    source_refs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    limitations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    review_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    authored_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class CovariateDefinitionModel(Base):
    __tablename__ = "covariate_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    study_id: Mapped[str] = mapped_column(
        ForeignKey("research_studies.id"), nullable=False, index=True
    )
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False)
    definition: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


class AnalysisPlanModel(Base):
    __tablename__ = "analysis_plans"
    __table_args__ = (UniqueConstraint("study_id", "version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    study_id: Mapped[str] = mapped_column(
        ForeignKey("research_studies.id"), nullable=False, index=True
    )
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    objectives: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    descriptive_metrics: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    subgroup_definitions: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    missing_data_approach: Mapped[str] = mapped_column(Text, nullable=False)
    methods: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    planned_outputs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    limitations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)
    authored_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


class CohortRunModel(Base):
    __tablename__ = "cohort_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    study_id: Mapped[str] = mapped_column(
        ForeignKey("research_studies.id"), nullable=False, index=True
    )
    cohort_version_id: Mapped[str] = mapped_column(
        ForeignKey("cohort_definition_versions.id"), nullable=False, index=True
    )
    protocol_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("study_protocol_versions.id"), index=True
    )
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    data_snapshot_marker: Mapped[str] = mapped_column(String(160), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    executed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_version_refs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False)
    attrition: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    analytics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(80), nullable=False)
    prescripta_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    run_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class CohortRunStepModel(Base):
    __tablename__ = "cohort_run_steps"
    __table_args__ = (UniqueConstraint("cohort_run_id", "sequence"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    cohort_run_id: Mapped[str] = mapped_column(
        ForeignKey("cohort_runs.id"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    criterion: Mapped[dict] = mapped_column(JSON, nullable=False)
    label: Mapped[str] = mapped_column(String(240), nullable=False)
    before_count: Mapped[int] = mapped_column(Integer, nullable=False)
    excluded_count: Mapped[int] = mapped_column(Integer, nullable=False)
    after_count: Mapped[int] = mapped_column(Integer, nullable=False)
    criterion_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class ResearchSnapshotModel(Base):
    __tablename__ = "research_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    cohort_run_id: Mapped[str] = mapped_column(
        ForeignKey("cohort_runs.id"), nullable=False, index=True
    )
    snapshot_type: Mapped[str] = mapped_column(String(60), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class EvidenceSourceModel(Base):
    __tablename__ = "evidence_sources"
    __table_args__ = (UniqueConstraint("institution_id", "identifier"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    identifier: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    url: Mapped[str | None] = mapped_column(String(500))
    publisher: Mapped[str | None] = mapped_column(String(220))
    jurisdiction: Mapped[str | None] = mapped_column(String(40))
    publication_date: Mapped[date | None] = mapped_column(Date)
    access_date: Mapped[date | None] = mapped_column(Date)
    source_version: Mapped[str | None] = mapped_column(String(120))
    review_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False, index=True
    )
    reviewer_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    license_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class EvidenceLinkModel(Base):
    __tablename__ = "evidence_links"
    __table_args__ = (
        UniqueConstraint("source_id", "target_type", "target_id", "relationship", "locator"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("evidence_sources.id"), nullable=False, index=True
    )
    target_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    relationship: Mapped[str] = mapped_column(String(80), nullable=False)
    locator: Mapped[str] = mapped_column(String(220), default="", nullable=False)
    review_status: Mapped[str] = mapped_column(
        String(40), default="pending_review", nullable=False
    )
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class DataQualityFindingModel(Base):
    __tablename__ = "data_quality_findings"
    __table_args__ = (
        UniqueConstraint("institution_id", "rule", "resource_type", "resource_id", "field"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    rule: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(160), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False, index=True)
    resolution: Mapped[str | None] = mapped_column(String(500))
    resolved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AIInteractionModel(Base):
    __tablename__ = "ai_interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    provider: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    model: Mapped[str | None] = mapped_column(String(160))
    provider_model_identifier: Mapped[str | None] = mapped_column(String(220))
    task_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    prompt_template_version: Mapped[str] = mapped_column(String(80), nullable=False)
    structured_schema_version: Mapped[str] = mapped_column(String(80), nullable=False)
    source_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    study_id: Mapped[str | None] = mapped_column(ForeignKey("research_studies.id"), index=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    output_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    fallback_used: Mapped[bool] = mapped_column(default=False, nullable=False)
    data_classification: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    human_review_status: Mapped[str] = mapped_column(
        String(40), default="needs_review", nullable=False, index=True
    )
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sanitized_error_class: Mapped[str | None] = mapped_column(String(120))
    usage_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    output_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


def _block_changes_after_review(target, reviewed_states: set[str], fields: set[str]) -> None:
    state = inspect(target)
    history = state.attrs.status.history
    previous_status = history.deleted[0] if history.deleted else target.status
    if previous_status in reviewed_states and any(
        state.attrs[field].history.has_changes() for field in fields
    ):
        raise ValueError("Conteúdo de versão revisada é imutável; crie uma nova versão.")


@event.listens_for(StudyProtocolVersionModel, "before_update")
def _immutable_reviewed_study_protocol(_mapper, _connection, target) -> None:
    _block_changes_after_review(
        target,
        {"reviewed_demo", "superseded", "archived"},
        {
            "population",
            "exposure",
            "comparator",
            "outcome",
            "index_date",
            "washout",
            "follow_up",
            "censoring",
            "inclusion",
            "exclusion",
            "covariates",
            "missing_data_strategy",
            "statistical_plan",
            "limitations",
            "source_refs",
            "definition_hash",
        },
    )


@event.listens_for(ConceptSetVersionModel, "before_update")
def _immutable_reviewed_concept_version(_mapper, _connection, target) -> None:
    _block_changes_after_review(
        target,
        {"human_reviewed", "approved_for_demo_study"},
        {
            "terminology_versions",
            "include_descendants",
            "source_refs",
            "license_metadata",
            "provenance",
            "definition_hash",
        },
    )


@event.listens_for(CohortDefinitionVersionModel, "before_update")
def _immutable_reviewed_cohort_version(_mapper, _connection, target) -> None:
    _block_changes_after_review(
        target,
        {"reviewed_demo", "superseded"},
        {"definition", "definition_hash", "query_cost"},
    )


@event.listens_for(CohortRunModel, "before_update")
def _immutable_cohort_run(_mapper, _connection, _target) -> None:
    raise ValueError("CohortRun é um snapshot imutável.")


@event.listens_for(ResearchSnapshotModel, "before_update")
def _immutable_research_snapshot(_mapper, _connection, _target) -> None:
    raise ValueError("ResearchSnapshot é imutável.")
