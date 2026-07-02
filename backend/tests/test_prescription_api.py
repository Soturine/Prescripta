from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_prescription_check_endpoint_blocks_allergy_and_writes_audit() -> None:
    client = TestClient(app)
    patient_response = client.post(
        "/api/patients",
        json={
            "name": "Paciente API",
            "age": 42,
            "weight_kg": 72,
            "height_cm": 171,
            "allergies": ["ibuprofeno"],
            "comorbidities": [],
            "current_medications": [],
        },
    )
    medication_response = client.post(
        "/api/medications",
        json={
            "brand_name": "Ibuvida",
            "active_ingredient": "ibuprofeno",
            "therapeutic_class": "anti-inflamatorio",
            "max_daily_dose_mg": 2400,
            "allowed_routes": ["oral"],
            "contraindications": [],
            "notes": "Teste",
        },
    )

    response = client.post(
        "/api/prescriptions/check",
        json={
            "patient_id": patient_response.json()["id"],
            "medication_id": medication_response.json()["id"],
            "dose_mg": 400,
            "frequency_per_day": 2,
            "route": "oral",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "bloqueado"
    assert payload["risk_level"] == "critico"
    assert payload["human_review_required"] is True
    assert payload["audit_id"] > 0

    audit_response = client.get("/api/audit")
    assert audit_response.status_code == 200
    assert len(audit_response.json()) == 1
