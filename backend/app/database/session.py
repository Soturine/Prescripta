from collections.abc import Generator

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

    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        _ensure_sqlite_v04_columns()


def _ensure_sqlite_v04_columns() -> None:
    column_specs = {
        "patients": {
            "renal_condition": "VARCHAR(120)",
            "hepatic_condition": "VARCHAR(120)",
            "cardiac_condition": "VARCHAR(120)",
            "gastrointestinal_history": "VARCHAR(160)",
            "hypertension": "BOOLEAN NOT NULL DEFAULT 0",
            "diabetes": "BOOLEAN NOT NULL DEFAULT 0",
            "pregnancy_or_lactation": "BOOLEAN",
            "adverse_reactions": "JSON DEFAULT '[]'",
            "clinical_notes": "TEXT",
            "clinical_profile_reviewed_at": "DATETIME",
            "clinical_profile_completeness_score": "FLOAT NOT NULL DEFAULT 0",
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
            "max_cumulative_dose_mg": "FLOAT",
            "condition_specific_limits": "JSON DEFAULT '{}'",
            "renal_caution": "BOOLEAN NOT NULL DEFAULT 0",
            "hepatic_caution": "BOOLEAN NOT NULL DEFAULT 0",
            "cardiac_caution": "BOOLEAN NOT NULL DEFAULT 0",
            "gastrointestinal_caution": "BOOLEAN NOT NULL DEFAULT 0",
            "elderly_caution": "BOOLEAN NOT NULL DEFAULT 0",
            "metabolism_organs": "JSON DEFAULT '[]'",
            "elimination_organs": "JSON DEFAULT '[]'",
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
