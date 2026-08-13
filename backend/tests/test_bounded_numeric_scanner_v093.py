from __future__ import annotations

import json

import pytest

from app.services.ai_task_router import AITaskError, AITaskRouter
from app.services.bounded_numeric_scanner import (
    NumericScanBudgetExceeded,
    NumericScanPolicy,
    scan_ascii_numbers,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("RR -1.25 and 2e-3 plus +4E2", {"-1.25", "2e-3", "+4E2"}),
        ("id123 x_45 67abc", set()),
        ("550e8400-e29b-41d4-a716-446655440000", set()),
        ("v1.2.3 hash9f86d081", set()),
        ("nan inf NaN ١٢٣ 12,5", set()),
        ("1.1.1.1", set()),
        ("+-+-12 --7 ++8", {"-12", "-7", "+8"}),
    ],
)
def test_scanner_contract(value: str, expected: set[str]) -> None:
    assert scan_ascii_numbers(value) == expected


def test_scanner_is_bounded_for_adversarial_payloads() -> None:
    policy = NumericScanPolicy(max_chars=100_000, max_tokens=2_048)
    assert scan_ascii_numbers("9" * 100_000, policy) == {"9" * 100_000}
    assert scan_ascii_numbers("!" * 100_000, policy) == set()
    assert scan_ascii_numbers("+-" * 50_000, policy) == set()
    with pytest.raises(NumericScanBudgetExceeded, match="character_budget"):
        scan_ascii_numbers("0" * 100_001, policy)
    with pytest.raises(NumericScanBudgetExceeded, match="token_budget"):
        scan_ascii_numbers(" ".join("1" for _ in range(2_050)), policy)


def test_router_budget_and_nested_json_are_fail_closed() -> None:
    nested = json.loads('{"items":["RR 1.25", {"ci":"0.9 to 1.7"}]}')
    assert AITaskRouter._numbers(nested) == {"1.25", "0.9", "1.7"}
    with pytest.raises(AITaskError, match="budget num"):
        AITaskRouter._numbers("7" * 65_537)
