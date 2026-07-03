from __future__ import annotations

from app.services.normalizer import dedupe_terms, normalize_text


def normalize_medication_payload(values: dict) -> dict:
    normalized = dict(values)
    for field in (
        "allowed_routes",
        "contraindications",
        "therapeutic_classes",
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

    if "active_ingredient" in normalized and normalized["active_ingredient"]:
        normalized["active_ingredient"] = normalize_text(normalized["active_ingredient"])

    if "commercial_aliases" in normalized and normalized["commercial_aliases"] is not None:
        normalized["commercial_aliases"] = _dedupe_preserving_label(
            normalized["commercial_aliases"]
        )

    if (
        "therapeutic_classes" in normalized
        and not normalized.get("therapeutic_classes")
        and normalized.get("therapeutic_class")
    ):
        normalized["therapeutic_classes"] = [normalized["therapeutic_class"]]

    if "source_jurisdiction" in normalized and normalized["source_jurisdiction"]:
        normalized["source_jurisdiction"] = str(normalized["source_jurisdiction"]).upper()

    for field in ("evidence_source_type", "validation_status"):
        if field in normalized and normalized[field]:
            normalized[field] = normalize_text(str(normalized[field])).replace(" ", "_")

    condition_limits = normalized.get("condition_specific_limits")
    if isinstance(condition_limits, dict):
        normalized["condition_specific_limits"] = {
            normalize_text(str(key)): value for key, value in condition_limits.items()
        }
    return normalized


def _dedupe_preserving_label(values: list[str] | None) -> list[str]:
    seen: set[str] = set()
    labels: list[str] = []
    for value in values or []:
        label = str(value).strip()
        normalized = normalize_text(label)
        if not label or normalized in seen:
            continue
        seen.add(normalized)
        labels.append(label)
    return labels
