from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from app.services.normalizer import normalize_text


class MatchKind(StrEnum):
    EXACT = "exact"
    ALIAS = "alias"
    CODE = "code"
    SUBSTRING = "substring"
    SUGGESTION = "suggestion"
    NONE = "none"


@dataclass(frozen=True)
class TerminologyMatch:
    matched: bool
    kind: MatchKind
    canonical_value: str | None = None


class TerminologyService:
    """Single matching policy for clinical terminology.

    Only exact normalized values, explicit aliases, or equal canonical codes are
    accepted as clinical matches. Substring/fuzzy results are suggestions and
    must never trigger a deterministic alert by themselves.
    """

    def match(
        self,
        candidate: str | None,
        target: str | None,
        *,
        aliases: Mapping[str, str] | None = None,
        candidate_code: str | None = None,
        target_code: str | None = None,
    ) -> TerminologyMatch:
        if candidate_code and target_code and candidate_code == target_code:
            return TerminologyMatch(True, MatchKind.CODE, candidate_code)

        normalized_candidate = normalize_text(candidate)
        normalized_target = normalize_text(target)
        if not normalized_candidate or not normalized_target:
            return TerminologyMatch(False, MatchKind.NONE)
        if normalized_candidate == normalized_target:
            return TerminologyMatch(True, MatchKind.EXACT, normalized_target)

        normalized_aliases = {
            normalize_text(alias): normalize_text(canonical)
            for alias, canonical in (aliases or {}).items()
        }
        candidate_canonical = normalized_aliases.get(
            normalized_candidate, normalized_candidate
        )
        target_canonical = normalized_aliases.get(normalized_target, normalized_target)
        if candidate_canonical == target_canonical:
            return TerminologyMatch(True, MatchKind.ALIAS, target_canonical)

        if (
            normalized_candidate in normalized_target
            or normalized_target in normalized_candidate
        ):
            return TerminologyMatch(False, MatchKind.SUBSTRING)
        return TerminologyMatch(False, MatchKind.NONE)

    def any_confirmed_match(
        self,
        candidates: Iterable[str] | None,
        targets: Iterable[str] | None,
        *,
        aliases: Mapping[str, str] | None = None,
    ) -> bool:
        return any(
            self.match(candidate, target, aliases=aliases).matched
            for candidate in candidates or []
            for target in targets or []
        )


terminology = TerminologyService()
