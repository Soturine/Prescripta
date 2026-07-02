from unicodedata import category, normalize


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    decomposed = normalize("NFKD", value)
    without_marks = "".join(char for char in decomposed if category(char) != "Mn")
    return " ".join(without_marks.casefold().strip().split())


def any_token_matches(candidates: list[str], targets: list[str]) -> bool:
    normalized_candidates = [normalize_text(candidate) for candidate in candidates if candidate]
    normalized_targets = [normalize_text(target) for target in targets if target]

    for candidate in normalized_candidates:
        for target in normalized_targets:
            if candidate == target or candidate in target or target in candidate:
                return True
    return False
