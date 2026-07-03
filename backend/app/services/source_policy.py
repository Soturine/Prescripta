from __future__ import annotations

from collections.abc import Callable

BR_SOURCE_PRIORITY = {
    "BR": 0,
    "GLOBAL": 1,
    "EU": 2,
    "US": 3,
}

def source_priority(jurisdiction: str | None, context_jurisdiction: str = "BR") -> int:
    jurisdiction_value = (jurisdiction or "GLOBAL").upper()
    context_value = context_jurisdiction.upper()
    if jurisdiction_value == context_value:
        return 0
    if context_value == "BR":
        return BR_SOURCE_PRIORITY.get(jurisdiction_value, 9)
    return 1 if jurisdiction_value == "GLOBAL" else 5


def sort_sources_by_jurisdiction(
    sources: list,
    *,
    context_jurisdiction: str = "BR",
    jurisdiction_getter: Callable[[object], str | None],
) -> list:
    return sorted(
        sources,
        key=lambda source: source_priority(
            jurisdiction_getter(source),
            context_jurisdiction=context_jurisdiction,
        ),
    )
