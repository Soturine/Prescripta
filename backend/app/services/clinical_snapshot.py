from __future__ import annotations

from typing import Any

from app.domain.clinical_decision import ClinicalDecisionEnvelope
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput, PrescriptionResult
from app.services.canonical_json import CANONICAL_HASH_ALGORITHM, canonical_sha256

CLINICAL_SNAPSHOT_SCHEMA = "prescripta-clinical-snapshot-v1"


def build_clinical_snapshot(
    *,
    patient: Patient,
    medication: Medication,
    prescription: PrescriptionInput,
    result: PrescriptionResult,
    decision: ClinicalDecisionEnvelope,
    dose_intelligence: dict[str, Any],
    psychotropic_safety: list[dict[str, Any]],
    prescribing_policy: dict[str, Any],
    rag_evidence: list[dict[str, Any]],
    patient_knowledge_bundle: dict[str, Any],
) -> dict[str, Any]:
    """Captura somente o contexto efetivamente usado, sem identificadores diretos."""
    snapshot = {
        "schema_version": CLINICAL_SNAPSHOT_SCHEMA,
        "captured_at": decision.evaluated_at.isoformat(),
        "patient": {
            "patient_id": patient.id,
            "age_at_evaluation": patient.computed_age,
            "weight_kg": patient.weight_kg,
            "height_cm": patient.height_cm,
            "sex_for_dosing_calculation": patient.sex_for_dosing_calculation,
            "allergies": list(patient.allergies),
            "comorbidities": list(patient.comorbidities),
            "current_medications": list(patient.current_medications),
            "renal_condition": patient.renal_condition,
            "hepatic_condition": patient.hepatic_condition,
            "cardiac_condition": patient.cardiac_condition,
            "gastrointestinal_history": patient.gastrointestinal_history,
            "hypertension": patient.hypertension,
            "diabetes": patient.diabetes,
            "pregnancy_or_lactation": patient.pregnancy_or_lactation,
            "mental_health_factors": list(patient.mental_health_factors or []),
            "reproductive_gynecologic_factors": list(
                patient.reproductive_gynecologic_factors or []
            ),
            "adverse_reactions": list(patient.adverse_reactions or []),
            "clinical_profile_completeness_score": patient.clinical_profile_completeness_score,
        },
        "medication": {
            "medication_id": medication.id,
            "active_ingredient_id": medication.active_ingredient_id,
            "brand_name": medication.brand_name,
            "active_ingredient": medication.active_ingredient,
            "therapeutic_class": medication.therapeutic_class,
            "source_jurisdiction": medication.source_jurisdiction,
            "evidence_source_type": medication.evidence_source_type,
            "validation_status": medication.validation_status,
            "source_version": medication.source_version,
            "dose_rule_validation_status": medication.dose_rule_validation_status,
            "dose_source_refs": list(medication.dose_source_refs or []),
            "policy_validation_status": medication.policy_validation_status,
            "policy_source_refs": list(medication.policy_source_refs or []),
            "policy_version": medication.policy_version,
            "limits": {
                "max_daily_dose_mg": medication.max_daily_dose_mg,
                "max_daily_dose_unit": medication.max_daily_dose_unit,
                "max_per_procedure": medication.max_per_procedure,
                "max_per_procedure_unit": medication.max_per_procedure_unit,
                "max_rate": medication.max_rate,
                "rate_unit": medication.rate_unit,
                "max_duration_days": medication.max_duration_days,
                "max_cumulative_dose_mg": medication.max_cumulative_dose_mg,
            },
        },
        "prescription": {
            "dose": prescription.effective_dose.to_dict(),
            "route": prescription.route,
            "duration_days": prescription.duration_days,
            "indication": prescription.indication,
        },
        "decision": decision.to_dict(),
        "legacy_result": {
            "status": result.status.value,
            "risk_level": result.risk_level.value,
            "recommendation": result.recommendation,
            "alerts": [alert.to_dict() for alert in result.alerts],
            "dose_summary": result.dose_summary,
            "compatibility": result.compatibility,
        },
        "modules": {
            "dose_intelligence": dose_intelligence,
            "psychotropic_safety": psychotropic_safety,
            "prescribing_policy": prescribing_policy,
        },
        "rag_evidence": rag_evidence,
        "knowledge_context": {
            "missing_data": list(patient_knowledge_bundle.get("missing_data") or []),
            "data_sources": list(patient_knowledge_bundle.get("data_sources") or []),
        },
    }
    return snapshot


def clinical_snapshot_hash(snapshot: dict[str, Any]) -> tuple[str, str]:
    return CANONICAL_HASH_ALGORITHM, canonical_sha256(snapshot)
