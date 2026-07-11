from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from app.database.models import AuditEventModel, PatientModel, UserModel
from app.repositories.audit_repository import AuditRepository
from app.schemas.patient_history_schema import PatientClinicalDocumentCreate
from app.services.dose_intelligence import DoseIntelligenceService
from app.services.patient_history_service import (
    DuplicateClinicalDocumentError,
    PatientHistoryService,
)
from app.services.prescribing_policy import PrescribingPolicyService
from app.services.psychotropic_safety import PsychotropicSafetyService


def test_audit_filters_and_paginates_in_sql(db_session: Session):
    for index in range(6):
        db_session.add(
            AuditEventModel(
                action="prescription.check" if index % 2 == 0 else "patient.update",
                resource_type="prescription" if index % 2 == 0 else "patient",
                resource_id=str(index),
                details={"specialty": "psychiatry" if index % 2 == 0 else "general"},
            )
        )
    db_session.commit()
    result = AuditRepository(db_session).list_filtered(
        action="prescription", specialty="psychiatry", page=2, page_size=1, sort="asc"
    )
    assert len(result) == 1
    assert result[0].action == "prescription.check"
    items, total = AuditRepository(db_session).list_filtered(
        action="prescription", specialty="psychiatry", page=2, page_size=1, include_total=True
    )
    assert len(items) == 1
    assert total == 3


def test_clinical_document_duplicate_is_explicit(db_session: Session):
    patient = PatientModel(name="Paciente Demo", weight_kg=70)
    user = UserModel(
        name="Médico Demo",
        email="doctor@demo.local",
        hashed_password="not-a-real-secret",
        role="medico",
    )
    db_session.add_all([patient, user])
    db_session.commit()
    payload = PatientClinicalDocumentCreate(
        title="Laudo fictício", raw_text="Conteúdo estritamente demonstrativo."
    )
    service = PatientHistoryService(db_session)
    service.create_document(patient, payload, user)
    with pytest.raises(DuplicateClinicalDocumentError):
        service.create_document(patient, payload, user)


def test_dose_requires_source_and_separates_daily_procedure_and_cumulative_limits():
    patient = {"weight_kg": 70, "height_cm": 170}
    service = DoseIntelligenceService()
    missing_source = service.evaluate(
        {"calculation_basis": "fixed", "dose_unit": "mg", "fixed_dose": 10}, patient
    )
    assert missing_source.status == "insufficient_rule"
    assert missing_source.calculated_dose is None
    result = service.evaluate(
        {
            "calculation_basis": "fixed",
            "dose_unit": "mg",
            "fixed_dose": 10,
            "max_daily": 100,
            "max_per_procedure": 60,
            "max_cumulative": 250,
            "source_refs": ["demo:rule:1"],
            "validation_status": "pending_review",
        },
        patient,
        {"dose_mg": 50, "frequency_per_day": 2, "duration_days": 3},
    )
    assert result.status == "above_cumulative_maximum"
    assert result.inputs_used["prescribed_per_administration"] == 50
    assert result.inputs_used["prescribed_daily_dose"] == 100
    assert result.inputs_used["prescribed_cumulative_dose"] == 300


def test_psychotropic_signals_have_stable_unique_keys():
    patient = SimpleNamespace(
        current_medications=["morfina", "morfina"],
        comorbidities=[],
        mental_health_factors=[],
        reproductive_gynecologic_factors=[],
        renal_condition=None,
        hepatic_condition=None,
        cardiac_condition=None,
        clinical_notes=None,
        pregnancy_or_lactation=None,
        diabetes=False,
        age=40,
    )
    signals = PsychotropicSafetyService().evaluate(
        SimpleNamespace(active_ingredient="diazepam"), patient
    )
    keys = [signal.deduplication_key for signal in signals]
    assert len(keys) == len(set(keys))
    assert any(signal.code == "BENZODIAZEPINE_OPIOID" for signal in signals)


def test_expired_demo_policy_warns_without_becoming_legal_block():
    result = PrescribingPolicyService().evaluate(
        {
            "role": "medico",
            "specialty_code": "psychiatry",
            "credential_verification_status": "demo_unverified",
        },
        {
            "policy_type": "demo_policy",
            "policy_strength": "warning_only",
            "policy_validation_status": "pending_review",
            "policy_effective_until": datetime.now(UTC) - timedelta(days=1),
        },
    )
    assert any("expirada" in warning for warning in result.warnings)
    assert result.legal_regulatory_notes == []
    assert result.status == "allowed_with_warning"
