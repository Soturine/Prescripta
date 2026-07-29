from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction


class UnitDimension(StrEnum):
    MASS = "mass"
    VOLUME = "volume"
    TIME = "time"
    SURFACE = "surface"
    CONCENTRATION = "mass_per_volume"
    MASS_RATE = "mass_per_time"
    VOLUME_RATE = "volume_per_time"
    MASS_PER_BODY = "mass_per_body_mass"
    MASS_PER_SURFACE = "mass_per_surface"
    MASS_PER_BODY_RATE = "mass_per_body_mass_per_time"
    MASS_PER_SURFACE_RATE = "mass_per_surface_per_time"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class UnitDefinition:
    canonical: str
    factor: Fraction
    exponents: tuple[int, int, int, int, int]

    @property
    def dimension(self) -> UnitDimension:
        dimensions = {
            (1, 0, 0, 0, 0): UnitDimension.MASS,
            (0, 1, 0, 0, 0): UnitDimension.VOLUME,
            (0, 0, 1, 0, 0): UnitDimension.TIME,
            (0, 0, 0, 0, 1): UnitDimension.SURFACE,
            (1, -1, 0, 0, 0): UnitDimension.CONCENTRATION,
            (1, 0, -1, 0, 0): UnitDimension.MASS_RATE,
            (0, 1, -1, 0, 0): UnitDimension.VOLUME_RATE,
            (1, 0, 0, -1, 0): UnitDimension.MASS_PER_BODY,
            (1, 0, 0, 0, -1): UnitDimension.MASS_PER_SURFACE,
            (1, 0, -1, -1, 0): UnitDimension.MASS_PER_BODY_RATE,
            (1, 0, -1, 0, -1): UnitDimension.MASS_PER_SURFACE_RATE,
        }
        return dimensions.get(self.exponents, UnitDimension.UNKNOWN)


@dataclass(frozen=True)
class Quantity:
    value: Decimal
    unit: str

    def converted_to(self, target_unit: str) -> Quantity | None:
        converted = convert_value(self.value, self.unit, target_unit)
        return None if converted is None else Quantity(converted, normalize_unit(target_unit))


_TOKEN_DEFINITIONS: dict[str, tuple[Fraction, tuple[int, int, int, int, int]]] = {
    "g": (Fraction(1000), (1, 0, 0, 0, 0)),
    "mg": (Fraction(1), (1, 0, 0, 0, 0)),
    "mcg": (Fraction(1, 1000), (1, 0, 0, 0, 0)),
    "ng": (Fraction(1, 1000000), (1, 0, 0, 0, 0)),
    "l": (Fraction(1000), (0, 1, 0, 0, 0)),
    "ml": (Fraction(1), (0, 1, 0, 0, 0)),
    "ul": (Fraction(1, 1000), (0, 1, 0, 0, 0)),
    "s": (Fraction(1, 3600), (0, 0, 1, 0, 0)),
    "min": (Fraction(1, 60), (0, 0, 1, 0, 0)),
    "h": (Fraction(1), (0, 0, 1, 0, 0)),
    "day": (Fraction(24), (0, 0, 1, 0, 0)),
    "m2": (Fraction(1), (0, 0, 0, 0, 1)),
}


def normalize_unit(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    normalized = normalized.replace("μ", "µ").replace("µg", "mcg").replace("ug", "mcg")
    normalized = normalized.replace("²", "2").replace(" ", "")
    normalized = normalized.replace("por", "/")
    aliases = {
        "litro": "l",
        "litros": "l",
        "hora": "h",
        "horas": "h",
        "hr": "h",
        "dia": "day",
        "dias": "day",
        "d": "day",
        "seg": "s",
        "sec": "s",
        "minuto": "min",
        "minutos": "min",
    }
    return "/".join(aliases.get(part, part) for part in normalized.split("/"))


def parse_unit(value: str | None) -> UnitDefinition | None:
    normalized = normalize_unit(value)
    if not normalized or not re.fullmatch(r"[a-z0-9]+(?:/[a-z0-9]+)*", normalized):
        return None
    parts = normalized.split("/")
    factor = Fraction(1)
    exponents = [0, 0, 0, 0, 0]
    for index, token in enumerate(parts):
        sign = 1 if index == 0 else -1
        if token == "kg" and index > 0:
            token_factor = Fraction(1)
            token_exponents = (0, 0, 0, 1, 0)
        elif token == "kg":
            token_factor = Fraction(1000000)
            token_exponents = (1, 0, 0, 0, 0)
        else:
            definition = _TOKEN_DEFINITIONS.get(token)
            if definition is None:
                return None
            token_factor, token_exponents = definition
        factor = factor * token_factor if sign == 1 else factor / token_factor
        for position, exponent in enumerate(token_exponents):
            exponents[position] += sign * exponent
    return UnitDefinition(normalized, factor, tuple(exponents))


def convert_value(
    value: Decimal,
    source_unit: str,
    target_unit: str,
) -> Decimal | None:
    source = parse_unit(source_unit)
    target = parse_unit(target_unit)
    if source is None or target is None or source.exponents != target.exponents:
        return None
    ratio = source.factor / target.factor
    return value * ratio.numerator / ratio.denominator


def multiply_concentration_by_volume(
    concentration: Quantity,
    volume: Quantity,
    *,
    target_unit: str = "mg",
) -> Quantity | None:
    concentration_unit = parse_unit(concentration.unit)
    volume_unit = parse_unit(volume.unit)
    target = parse_unit(target_unit)
    if (
        concentration_unit is None
        or volume_unit is None
        or target is None
        or concentration_unit.dimension != UnitDimension.CONCENTRATION
        or volume_unit.dimension != UnitDimension.VOLUME
    ):
        return None
    base_value = _apply_factor(concentration.value, concentration_unit.factor)
    base_volume = _apply_factor(volume.value, volume_unit.factor)
    mass_in_mg = base_value * base_volume
    return Quantity(_remove_factor(mass_in_mg, target.factor), normalize_unit(target_unit))


def volume_rate_to_mass_rate(
    rate: Quantity,
    concentration: Quantity,
    *,
    target_unit: str,
) -> Quantity | None:
    rate_unit = parse_unit(rate.unit)
    concentration_unit = parse_unit(concentration.unit)
    target = parse_unit(target_unit)
    if (
        rate_unit is None
        or concentration_unit is None
        or target is None
        or rate_unit.dimension != UnitDimension.VOLUME_RATE
        or concentration_unit.dimension != UnitDimension.CONCENTRATION
        or target.dimension != UnitDimension.MASS_RATE
    ):
        return None
    mass_rate_in_mg_per_h = _apply_factor(rate.value, rate_unit.factor) * _apply_factor(
        concentration.value, concentration_unit.factor
    )
    return Quantity(
        _remove_factor(mass_rate_in_mg_per_h, target.factor),
        normalize_unit(target_unit),
    )


def _apply_factor(value: Decimal, factor: Fraction) -> Decimal:
    return value * factor.numerator / factor.denominator


def _remove_factor(value: Decimal, factor: Fraction) -> Decimal:
    return value * factor.denominator / factor.numerator


def remove_body_basis(
    quantity: Quantity,
    *,
    weight_kg: Decimal | None,
    body_surface_m2: Decimal | None,
) -> Quantity | None:
    definition = parse_unit(quantity.unit)
    if definition is None:
        return None
    unit = normalize_unit(quantity.unit)
    value = quantity.value
    parts = unit.split("/")
    if "kg" in parts[1:]:
        if weight_kg is None:
            return None
        parts.remove("kg")
        value *= weight_kg
    if "m2" in parts[1:]:
        if body_surface_m2 is None:
            return None
        parts.remove("m2")
        value *= body_surface_m2
    result_unit = "/".join(parts)
    return Quantity(value, result_unit)


def canonical_target(unit: str) -> str | None:
    definition = parse_unit(unit)
    if definition is None:
        return None
    targets = {
        UnitDimension.MASS: "mg",
        UnitDimension.VOLUME: "ml",
        UnitDimension.TIME: "h",
        UnitDimension.SURFACE: "m2",
        UnitDimension.CONCENTRATION: "mg/ml",
        UnitDimension.MASS_RATE: "mg/h",
        UnitDimension.VOLUME_RATE: "ml/h",
        UnitDimension.MASS_PER_BODY: "mg/kg",
        UnitDimension.MASS_PER_SURFACE: "mg/m2",
        UnitDimension.MASS_PER_BODY_RATE: "mg/kg/h",
        UnitDimension.MASS_PER_SURFACE_RATE: "mg/m2/h",
    }
    return targets.get(definition.dimension)
