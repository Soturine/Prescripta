from __future__ import annotations

from app.services.normalizer import dedupe_terms, normalize_text


def normalize_medication_payload(values: dict) -> dict:
    normalized = dict(values)
    for field in (
        "allowed_routes",
        "contraindications",
        "metabolism_organs",
        "elimination_organs",
        "organs_involved",
        "relevant_adverse_effects",
        "structured_contraindications",
        "related_medications",
    ):
        if field in normalized and normalized[field] is not None:
            normalized[field] = dedupe_terms(normalized[field])

    for field in ("therapeutic_class", "therapeutic_action", "alternative_group"):
        if field in normalized and normalized[field]:
            normalized[field] = normalize_text(normalized[field])

    condition_limits = normalized.get("condition_specific_limits")
    if isinstance(condition_limits, dict):
        normalized["condition_specific_limits"] = {
            normalize_text(str(key)): value for key, value in condition_limits.items()
        }
    return normalized
