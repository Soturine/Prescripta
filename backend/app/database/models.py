from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class PatientModel(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
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
    adverse_reactions: Mapped[list[str]] = mapped_column(JSON, default=list)
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_profile_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    clinical_profile_completeness_score: Mapped[float] = mapped_column(
        Float, default=0, nullable=False
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
    max_daily_dose_mg: Mapped[float] = mapped_column(Float, nullable=False)
    max_duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_cumulative_dose_mg: Mapped[float | None] = mapped_column(Float, nullable=True)
    condition_specific_limits: Mapped[dict] = mapped_column(JSON, default=dict)
    allowed_routes: Mapped[list[str]] = mapped_column(JSON, default=list)
    contraindications: Mapped[list[str]] = mapped_column(JSON, default=list)
    renal_caution: Mapped[bool] = mapped_column(default=False, nullable=False)
    hepatic_caution: Mapped[bool] = mapped_column(default=False, nullable=False)
    cardiac_caution: Mapped[bool] = mapped_column(default=False, nullable=False)
    gastrointestinal_caution: Mapped[bool] = mapped_column(default=False, nullable=False)
    elderly_caution: Mapped[bool] = mapped_column(default=False, nullable=False)
    metabolism_organs: Mapped[list[str]] = mapped_column(JSON, default=list)
    elimination_organs: Mapped[list[str]] = mapped_column(JSON, default=list)
    organs_involved: Mapped[list[str]] = mapped_column(JSON, default=list)
    relevant_adverse_effects: Mapped[list[str]] = mapped_column(JSON, default=list)
    structured_contraindications: Mapped[list[str]] = mapped_column(JSON, default=list)
    therapeutic_action: Mapped[str | None] = mapped_column(String(180), nullable=True)
    alternative_group: Mapped[str | None] = mapped_column(String(120), nullable=True)
    related_medications: Mapped[list[str]] = mapped_column(JSON, default=list)
    knowledge_source: Mapped[str | None] = mapped_column(String(220), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


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
    dose_mg: Mapped[float] = mapped_column(Float, nullable=False)
    frequency_per_day: Mapped[int] = mapped_column(Integer, nullable=False)
    route: Mapped[str] = mapped_column(String(80), nullable=False)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    indication: Mapped[str | None] = mapped_column(String(180), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(40), nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    alerts: Mapped[list[dict]] = mapped_column(JSON, default=list)


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
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    risk_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
