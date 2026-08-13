from __future__ import annotations

from dataclasses import dataclass


class NumericScanBudgetExceeded(ValueError):
    pass


@dataclass(frozen=True)
class NumericScanPolicy:
    max_chars: int = 65_536
    max_tokens: int = 2_048


_ASCII_IDENTIFIER = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
)
_HEX = frozenset("0123456789abcdefABCDEF")
_DEFAULT_POLICY = NumericScanPolicy()


def _is_uuid_at(value: str, start: int) -> bool:
    if start + 36 > len(value):
        return False
    for offset in range(36):
        char = value[start + offset]
        if offset in {8, 13, 18, 23}:
            if char != "-":
                return False
        elif char not in _HEX:
            return False
    before_ok = start == 0 or value[start - 1] not in _ASCII_IDENTIFIER
    after = start + 36
    after_ok = after == len(value) or value[after] not in _ASCII_IDENTIFIER
    return before_ok and after_ok


def scan_ascii_numbers(value: str, policy: NumericScanPolicy = _DEFAULT_POLICY) -> set[str]:
    """Return bounded ASCII numeric tokens in one forward pass.

    The grammar is ``[+-]? DIGIT+ ('.' DIGIT+)? ([eE] [+-]? DIGIT+)?``.
    Identifier-adjacent tokens, Unicode numerics, comma decimals, NaN and infinity
    are intentionally excluded. The scanner is O(n) and never backtracks.
    """
    if len(value) > policy.max_chars:
        raise NumericScanBudgetExceeded("numeric_scan_character_budget_exceeded")

    found: set[str] = set()
    token_count = 0
    index = 0
    length = len(value)
    while index < length:
        if _is_uuid_at(value, index):
            index += 36
            continue
        start = index
        if value[index] in "+-":
            index += 1
        if index >= length or not ("0" <= value[index] <= "9"):
            index = start + 1
            continue

        integer_start = index
        while index < length and "0" <= value[index] <= "9":
            index += 1
        if index < length and value[index] == ".":
            decimal_mark = index
            index += 1
            decimal_start = index
            while index < length and "0" <= value[index] <= "9":
                index += 1
            if index == decimal_start:
                index = decimal_mark

        exponent_mark = index
        if index < length and value[index] in "eE":
            index += 1
            if index < length and value[index] in "+-":
                index += 1
            exponent_start = index
            while index < length and "0" <= value[index] <= "9":
                index += 1
            if index == exponent_start:
                index = exponent_mark

        before_ok = start == 0 or value[start - 1] not in _ASCII_IDENTIFIER
        after_ok = index == length or value[index] not in _ASCII_IDENTIFIER
        if start >= 2 and value[start - 1] in ".," and value[start - 2].isdigit():
            before_ok = False
        if index + 1 < length and value[index] in ".," and value[index + 1].isdigit():
            after_ok = False
        if before_ok and after_ok:
            token_count += 1
            found.add(value[start:index])
            if token_count > policy.max_tokens:
                raise NumericScanBudgetExceeded("numeric_scan_token_budget_exceeded")
        elif index == integer_start:
            index = start + 1
    return found
