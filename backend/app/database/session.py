from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.database import models  # noqa: F401

    local_environment = settings.environment.lower() in {
        "development",
        "dev",
        "local",
        "test",
        "testing",
    }
    if not local_environment:
        _verify_migration_head()
        return
    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        _ensure_sqlite_v04_columns()


def _verify_migration_head() -> None:
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    expected = ScriptDirectory.from_config(config).get_current_head()
    with engine.connect() as connection:
        current = MigrationContext.configure(connection).get_current_revision()
    if current != expected:
        raise RuntimeError(
            f"Schema não migrado: revisão atual={current!r}, revisão esperada={expected!r}."
        )


def _ensure_sqlite_v04_columns() -> None:
    column_specs = {
        "patients": {
            "institution_id": "VARCHAR(100) NOT NULL DEFAULT 'demo'",
            "created_by_user_id": "INTEGER",
            "phone": "VARCHAR(80)",
            "email": "VARCHAR(220)",
            "mother_name": "VARCHAR(160)",
            "renal_condition": "VARCHAR(120)",
            "hepatic_condition": "VARCHAR(120)",
            "cardiac_condition": "VARCHAR(120)",
            "gastrointestinal_history": "VARCHAR(160)",
            "hypertension": "BOOLEAN NOT NULL DEFAULT 0",
            "diabetes": "BOOLEAN NOT NULL DEFAULT 0",
            "pregnancy_or_lactation": "BOOLEAN",
            "mental_health_factors": "JSON DEFAULT '[]'",
            "reproductive_gynecologic_factors": "JSON DEFAULT '[]'",
            "adverse_reactions": "JSON DEFAULT '[]'",
            "clinical_notes": "TEXT",
            "clinical_profile_reviewed_at": "DATETIME",
            "clinical_profile_completeness_score": "FLOAT NOT NULL DEFAULT 0",
            "sex_for_dosing_calculation": "VARCHAR(20)",
        },
        "users": {
            "institution_id": "VARCHAR(100) NOT NULL DEFAULT 'demo'",
            "mfa_enabled": "BOOLEAN NOT NULL DEFAULT 0",
            "mfa_secret_encrypted": "VARCHAR(512)",
        },
        "medications": {
            "active_ingredient_id": "INTEGER",
            "commercial_aliases": "JSON DEFAULT '[]'",
            "therapeutic_classes": "JSON DEFAULT '[]'",
            "source_jurisdiction": "VARCHAR(20) NOT NULL DEFAULT 'BR'",
            "evidence_source_type": "VARCHAR(80) NOT NULL DEFAULT 'demo_seed'",
            "validation_status": "VARCHAR(40) NOT NULL DEFAULT 'demo'",
            "concentration": "VARCHAR(120)",
            "pharmaceutical_form": "VARCHAR(120)",
            "evidence_source_url": "VARCHAR(500)",
            "max_duration_days": "INTEGER",
            "dose_mg_per_kg": "FLOAT",
            "dose_by_weight_enabled": "BOOLEAN NOT NULL DEFAULT 0",
            "dose_dimension": "VARCHAR(40) NOT NULL DEFAULT 'per_administration'",
            "max_daily_dose_unit": "VARCHAR(40) NOT NULL DEFAULT 'mg'",
            "max_per_procedure_unit": "VARCHAR(40)",
            "max_rate": "FLOAT",
            "rate_unit": "VARCHAR(40)",
            "max_cumulative_dose_mg": "FLOAT",
            "continuous_use": "BOOLEAN NOT NULL DEFAULT 0",
            "monitoring_required": "BOOLEAN NOT NULL DEFAULT 0",
            "monitoring_notes": "TEXT",
            "condition_specific_limits": "JSON DEFAULT '{}'",
            "renal_caution": "BOOLEAN NOT NULL DEFAULT 0",
            "hepatic_caution": "BOOLEAN NOT NULL DEFAULT 0",
            "cardiac_caution": "BOOLEAN NOT NULL DEFAULT 0",
            "gastrointestinal_caution": "BOOLEAN NOT NULL DEFAULT 0",
            "elderly_caution": "BOOLEAN NOT NULL DEFAULT 0",
            "mechanism_of_action": "TEXT",
            "absorption_notes": "TEXT",
            "distribution_notes": "TEXT",
            "metabolism_organs": "JSON DEFAULT '[]'",
            "elimination_organs": "JSON DEFAULT '[]'",
            "renal_elimination_level": "VARCHAR(40) NOT NULL DEFAULT 'nao_informado'",
            "hepatic_metabolism_level": "VARCHAR(40) NOT NULL DEFAULT 'nao_informado'",
            "cyp_interactions": "JSON DEFAULT '[]'",
            "pharmacodynamic_notes": "TEXT",
            "pharmacokinetic_notes": "TEXT",
            "clinical_interpretation": "TEXT",
            "neuropsychiatric_cautions": "JSON DEFAULT '[]'",
            "reproductive_cautions": "JSON DEFAULT '[]'",
            "organs_involved": "JSON DEFAULT '[]'",
            "relevant_adverse_effects": "JSON DEFAULT '[]'",
            "structured_contraindications": "JSON DEFAULT '[]'",
            "therapeutic_action": "VARCHAR(180)",
            "alternative_group": "VARCHAR(120)",
            "related_medications": "JSON DEFAULT '[]'",
            "knowledge_source": "VARCHAR(220)",
        },
        "prescription_audits": {
            "duration_days": "INTEGER",
            "indication": "VARCHAR(180)",
            "dose_input": "JSON DEFAULT '{}'",
            "clinical_decision": "JSON DEFAULT '{}'",
            "clinical_snapshot": "JSON DEFAULT '{}'",
            "snapshot_hash": "VARCHAR(64)",
            "hash_algorithm": "VARCHAR(80)",
            "snapshot_schema_version": "VARCHAR(80)",
            "correlation_id": "VARCHAR(80)",
        },
    }
    with engine.begin() as connection:
        for table_name, specs in column_specs.items():
            existing = {
                row[1] for row in connection.execute(text(f"PRAGMA table_info({table_name})"))
            }
            for column_name, column_spec in specs.items():
                if column_name not in existing:
                    connection.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_spec}")
                    )
