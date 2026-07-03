from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

SYNONYMS = {
    "rim": "renal",
    "rins": "renal",
    "renal": "renal",
    "insuficiencia renal": "renal",
    "doenca renal": "renal",
    "problema renal": "renal",
    "figado": "hepatico",
    "fígado": "hepatico",
    "hepatico": "hepatico",
    "hepática": "hepatico",
    "hepatica": "hepatico",
    "problema hepatico": "hepatico",
    "cardiaco": "cardiaco",
    "cardiaca": "cardiaco",
    "coração": "cardiaco",
    "coracao": "cardiaco",
    "gastrite": "gastrointestinal",
    "ulcera": "gastrointestinal",
    "úlcera": "gastrointestinal",
    "sangramento gastrointestinal": "gastrointestinal",
    "estomago": "gastrointestinal",
    "estômago": "gastrointestinal",
    "pressao alta": "hipertensao",
    "pressão alta": "hipertensao",
    "hipertensão": "hipertensao",
    "hipertensao": "hipertensao",
    "diabetes": "diabetes",
    "diabete": "diabetes",
}


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    ascii_text = re.sub(r"[^a-zA-Z0-9]+", " ", ascii_text).strip().lower()
    ascii_text = re.sub(r"\s+", " ", ascii_text)
    return SYNONYMS.get(ascii_text, ascii_text)


def normalize_terms(values: Iterable[str] | None) -> list[str]:
    return [normalize_text(value) for value in values or [] if normalize_text(value)]


def dedupe_terms(values: Iterable[str] | None) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values or []:
        normalized = normalize_text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def has_any_match(values: Iterable[str] | None, candidates: Iterable[str] | None) -> bool:
    normalized_values = set(normalize_terms(values))
    normalized_candidates = set(normalize_terms(candidates))
    if not normalized_values or not normalized_candidates:
        return False
    return bool(normalized_values & normalized_candidates)


def merge_terms(existing: Iterable[str] | None, incoming: Iterable[str] | None) -> list[str]:
    return dedupe_terms([*(existing or []), *(incoming or [])])
