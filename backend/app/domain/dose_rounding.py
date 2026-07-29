from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

DISPLAY_QUANTUM = Decimal("0.0001")
ROUNDING_POLICY_VERSION = "prescripta-half-even-v1"


def present_decimal(value: Decimal | None, quantum: Decimal = DISPLAY_QUANTUM) -> float | None:
    if value is None:
        return None
    return float(value.quantize(quantum, rounding=ROUND_HALF_EVEN))
