from __future__ import annotations

from datetime import UTC, datetime

from app.services.controlled_vocabulary import normalize_patient_clinical_fields
from app.services.normalizer import dedupe_terms

REQUIRED_PROFILE_ITEMS = (
    "allergies",
    "current_medications",
    "adverse_reactions",
    "renal_condition",
    "hepatic_condition",
    "cardiac_condition",
    "gastrointestinal_history",
    "hypertension",
    "diabetes",
    "mental_health_factors",
    "reproductive_gynecologic_factors",
)


def clinical_profile_score(values: dict) -> float:
    completed = 0
    for item in REQUIRED_PROFILE_ITEMS:
        value = values.get(item)
        if isinstance(value, list):
            completed += int(bool(value))
        elif isinstance(value, bool):
            completed += 1
        else:
            completed += int(bool(value))
    return round((completed / len(REQUIRED_PROFILE_ITEMS)) * 100, 2)


def clinical_profile_badge(score: float) -> str:
    if score >= 75:
        return "Perfil clínico completo"
    if score >= 45:
        return "Revisar histórico"
    return "Perfil clínico incompleto"


def normalize_patient_payload(values: dict) -> dict:
    normalized = normalize_patient_clinical_fields(values)
    for field in (
        "allergies",
        "comorbidities",
        "current_medications",
        "adverse_reactions",
    ):
        if field in normalized and normalized[field] is not None:
            normalized[field] = dedupe_terms(normalized[field])

    score_values = {
        "allergies": normalized.get("allergies", []),
        "current_medications": normalized.get("current_medications", []),
        "adverse_reactions": normalized.get("adverse_reactions", []),
        "renal_condition": normalized.get("renal_condition"),
        "hepatic_condition": normalized.get("hepatic_condition"),
        "cardiac_condition": normalized.get("cardiac_condition"),
        "gastrointestinal_history": normalized.get("gastrointestinal_history"),
        "hypertension": bool(normalized.get("hypertension", False)),
        "diabetes": bool(normalized.get("diabetes", False)),
        "mental_health_factors": normalized.get("mental_health_factors", []),
        "reproductive_gynecologic_factors": normalized.get("reproductive_gynecologic_factors", []),
    }
    normalized["clinical_profile_completeness_score"] = clinical_profile_score(score_values)
    return normalized


def reviewed_now() -> datetime:
    return datetime.now(UTC)
