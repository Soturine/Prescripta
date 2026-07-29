from app.services.normalizer import normalize_text as normalize_text
from app.services.terminology import terminology

__all__ = ["any_token_matches", "normalize_text"]


def any_token_matches(candidates: list[str], targets: list[str]) -> bool:
    return terminology.any_confirmed_match(candidates, targets)
