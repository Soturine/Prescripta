from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

from app.domain.dose_units import (
    Quantity,
    UnitDimension,
    canonical_target,
    convert_value,
    multiply_concentration_by_volume,
    normalize_unit,
    parse_unit,
    remove_body_basis,
    volume_rate_to_mass_rate,
)


class AdministrationKind(StrEnum):
    BOLUS = "bolus"
    INTERMITTENT = "intermittent"
    CONTINUOUS = "continuous"
    PRN = "prn"


class DoseDimension(StrEnum):
    PER_ADMINISTRATION = "per_administration"
    DAILY = "daily"
    RATE = "rate"
    PROCEDURE = "procedure"
    CUMULATIVE = "cumulative"
    PRN_CEILING = "prn_ceiling"
    UNSUPPORTED = "unsupported"


MASS_TO_MG: dict[str, Decimal] = {
    "g": Decimal("1000"),
    "mg": Decimal("1"),
    "mcg": Decimal("0.001"),
    "ng": Decimal("0.000001"),
}
VOLUME_TO_ML: dict[str, Decimal] = {
    "l": Decimal("1000"),
    "ml": Decimal("1"),
    "ul": Decimal("0.001"),
}


def decimal_value(value: Decimal | int | float | str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        converted = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Quantidade inválida: {value!r}") from exc
    if not converted.is_finite() or converted <= 0:
        raise ValueError("Quantidades clínicas devem ser finitas e maiores que zero.")
    return converted


def convert_mass(value: Decimal, from_unit: str, to_unit: str) -> Decimal | None:
    return convert_value(value, from_unit, to_unit)


@dataclass(frozen=True)
class MedicationDoseInput:
    amount: Decimal
    amount_unit: str
    administration_kind: AdministrationKind = AdministrationKind.INTERMITTENT
    concentration_value: Decimal | None = None
    concentration_unit: str | None = None
    volume: Decimal | None = None
    volume_unit: str | None = None
    rate_value: Decimal | None = None
    rate_unit: str | None = None
    frequency_per_day: int | None = None
    interval_value: Decimal | None = None
    interval_unit: str | None = None
    duration_value: Decimal | None = None
    duration_unit: str | None = None
    route: str | None = None
    site: str | None = None
    procedure_context: str | None = None
    prn: bool = False
    max_administrations_per_day: int | None = None
    source_id: str | None = None
    source_version: str | None = None
    precision: str = "0.0001"
    rounding_policy: str = "prescripta-half-even-v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", decimal_value(self.amount))
        object.__setattr__(self, "amount_unit", normalize_unit(self.amount_unit))
        kind = AdministrationKind(self.administration_kind)
        if self.prn and kind != AdministrationKind.PRN:
            kind = AdministrationKind.PRN
        object.__setattr__(self, "administration_kind", kind)
        object.__setattr__(self, "prn", kind == AdministrationKind.PRN)
        for name in (
            "concentration_value",
            "volume",
            "rate_value",
            "interval_value",
            "duration_value",
        ):
            object.__setattr__(self, name, decimal_value(getattr(self, name)))
        for name in (
            "concentration_unit",
            "volume_unit",
            "rate_unit",
            "interval_unit",
            "duration_unit",
        ):
            if getattr(self, name) is not None:
                object.__setattr__(self, name, normalize_unit(getattr(self, name)))
        self._validate_contract()

    def _validate_contract(self) -> None:
        if self.frequency_per_day is not None and self.frequency_per_day <= 0:
            raise ValueError("Frequência deve ser maior que zero.")
        if self.max_administrations_per_day is not None and self.max_administrations_per_day <= 0:
            raise ValueError("O teto de administrações deve ser maior que zero.")
        if self.administration_kind == AdministrationKind.CONTINUOUS and not self.rate_value:
            raise ValueError("Infusão contínua exige taxa explícita.")
        if self.prn and self.frequency_per_day is not None:
            raise ValueError("PRN não aceita frequência programada; informe apenas o teto diário.")
        for value, unit, label in (
            (self.concentration_value, self.concentration_unit, "Concentração"),
            (self.volume, self.volume_unit, "Volume"),
            (self.rate_value, self.rate_unit, "Taxa"),
            (self.interval_value, self.interval_unit, "Intervalo"),
            (self.duration_value, self.duration_unit, "Duração"),
        ):
            if (value is None) != (unit is None):
                raise ValueError(f"{label} exige valor e unidade.")
        if self.concentration_unit and (
            parse_unit(self.concentration_unit) is None
            or parse_unit(self.concentration_unit).dimension != UnitDimension.CONCENTRATION
        ):
            raise ValueError("Unidade de concentração incompatível.")
        if self.volume_unit and (
            parse_unit(self.volume_unit) is None
            or parse_unit(self.volume_unit).dimension != UnitDimension.VOLUME
        ):
            raise ValueError("Unidade de volume incompatível.")
        if self.interval_unit and (
            parse_unit(self.interval_unit) is None
            or parse_unit(self.interval_unit).dimension != UnitDimension.TIME
        ):
            raise ValueError("Unidade de intervalo incompatível.")
        if self.duration_unit and (
            parse_unit(self.duration_unit) is None
            or parse_unit(self.duration_unit).dimension != UnitDimension.TIME
        ):
            raise ValueError("Unidade de duração incompatível.")
        if self.frequency_per_day is not None and self.interval_value is not None:
            hours = convert_value(self.interval_value, self.interval_unit or "", "h")
            inferred = Decimal("24") / hours if hours else None
            if inferred is None or inferred != Decimal(self.frequency_per_day):
                raise ValueError("Frequência e intervalo representam esquemas divergentes.")

    @classmethod
    def legacy_mg(
        cls,
        *,
        dose_mg: float,
        frequency_per_day: int,
        route: str,
        duration_days: int | None,
    ) -> MedicationDoseInput:
        return cls(
            amount=decimal_value(dose_mg),
            amount_unit="mg",
            administration_kind=AdministrationKind.INTERMITTENT,
            frequency_per_day=frequency_per_day,
            duration_value=decimal_value(duration_days),
            duration_unit="day" if duration_days is not None else None,
            route=route,
            source_id="legacy:dose_mg",
            source_version="deprecated-v1",
        )

    @property
    def dimension(self) -> DoseDimension:
        if self.rate_value is not None or self.administration_kind == AdministrationKind.CONTINUOUS:
            return DoseDimension.RATE
        if self.procedure_context:
            return DoseDimension.PROCEDURE
        if self.prn:
            return DoseDimension.PRN_CEILING
        amount = parse_unit(self.amount_unit)
        if amount and amount.dimension in {UnitDimension.MASS, UnitDimension.VOLUME}:
            return DoseDimension.PER_ADMINISTRATION
        return DoseDimension.UNSUPPORTED

    @property
    def administration_mass(self) -> Quantity | None:
        direct = Quantity(self.amount, self.amount_unit)
        direct_definition = parse_unit(self.amount_unit)
        derived = None
        if (
            self.concentration_value
            and self.concentration_unit
            and self.volume
            and self.volume_unit
        ):
            derived = multiply_concentration_by_volume(
                Quantity(self.concentration_value, self.concentration_unit),
                Quantity(self.volume, self.volume_unit),
            )
        if direct_definition and direct_definition.dimension == UnitDimension.MASS:
            direct_mg = direct.converted_to("mg")
            if derived is not None and direct_mg is not None and direct_mg.value != derived.value:
                return None
            return direct_mg
        if direct_definition and direct_definition.dimension == UnitDimension.VOLUME:
            if not self.concentration_value or not self.concentration_unit:
                return None
            if self.volume is not None and self.volume_unit is not None:
                explicit_volume = Quantity(self.volume, self.volume_unit).converted_to(
                    self.amount_unit
                )
                if explicit_volume is None or explicit_volume.value != self.amount:
                    return None
            return multiply_concentration_by_volume(
                Quantity(self.concentration_value, self.concentration_unit), direct
            )
        return derived

    def amount_as(self, unit: str) -> Decimal | None:
        mass = self.administration_mass
        converted = mass.converted_to(unit) if mass else None
        return converted.value if converted else None

    @property
    def amount_mg(self) -> Decimal | None:
        return self.amount_as("mg")

    @property
    def inferred_frequency_per_day(self) -> Decimal | None:
        if self.frequency_per_day is not None:
            return Decimal(self.frequency_per_day)
        if self.interval_value is None or self.interval_unit is None:
            return None
        hours = convert_value(self.interval_value, self.interval_unit, "h")
        if hours is None or hours <= 0:
            return None
        return Decimal("24") / hours

    @property
    def duration_days(self) -> Decimal | None:
        if self.duration_value is None or self.duration_unit is None:
            return None
        return convert_value(self.duration_value, self.duration_unit, "day")

    @property
    def daily_mass_mg(self) -> Decimal | None:
        excluded = {DoseDimension.RATE, DoseDimension.PROCEDURE, DoseDimension.PRN_CEILING}
        if self.dimension in excluded:
            return None
        amount_mg = self.amount_mg
        frequency = self.inferred_frequency_per_day
        if amount_mg is None or frequency is None:
            return None
        return amount_mg * frequency

    @property
    def daily_mass_upper_mg(self) -> Decimal | None:
        if not self.prn or self.max_administrations_per_day is None:
            return None
        amount_mg = self.amount_mg
        return None if amount_mg is None else amount_mg * self.max_administrations_per_day

    @property
    def cumulative_mass_mg(self) -> Decimal | None:
        daily = self.daily_mass_mg
        duration = self.duration_days
        return None if daily is None or duration is None else daily * duration

    @property
    def cumulative_mass_upper_mg(self) -> Decimal | None:
        daily = self.daily_mass_upper_mg
        duration = self.duration_days
        return None if daily is None or duration is None else daily * duration

    def rate_as(
        self,
        target_unit: str,
        *,
        weight_kg: Decimal | None = None,
        body_surface_m2: Decimal | None = None,
    ) -> Decimal | None:
        if self.rate_value is None or self.rate_unit is None:
            return None
        rate = Quantity(self.rate_value, self.rate_unit)
        definition = parse_unit(self.rate_unit)
        if definition is None:
            return None
        if definition.dimension == UnitDimension.VOLUME_RATE:
            if not self.concentration_value or not self.concentration_unit:
                return None
            mass_rate = volume_rate_to_mass_rate(
                rate,
                Quantity(self.concentration_value, self.concentration_unit),
                target_unit=target_unit,
            )
            return mass_rate.value if mass_rate else None
        absolute = remove_body_basis(
            rate,
            weight_kg=weight_kg,
            body_surface_m2=body_surface_m2,
        )
        if absolute is None:
            return None
        converted = absolute.converted_to(target_unit)
        return converted.value if converted else None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key, value in list(payload.items()):
            if isinstance(value, Decimal):
                payload[key] = str(value)
            elif isinstance(value, StrEnum):
                payload[key] = value.value
        amount_definition = parse_unit(self.amount_unit)
        payload.update(
            {
                "dimension": self.dimension.value,
                "amount_dimension": (
                    amount_definition.dimension.value if amount_definition else "unknown"
                ),
                "amount_mg": str(self.amount_mg) if self.amount_mg is not None else None,
                "frequency_per_day_inferred": (
                    str(self.inferred_frequency_per_day)
                    if self.inferred_frequency_per_day is not None
                    else None
                ),
                "daily_mass_mg": (
                    str(self.daily_mass_mg) if self.daily_mass_mg is not None else None
                ),
                "daily_mass_upper_mg": (
                    str(self.daily_mass_upper_mg)
                    if self.daily_mass_upper_mg is not None
                    else None
                ),
                "duration_days_normalized": (
                    str(self.duration_days) if self.duration_days is not None else None
                ),
                "cumulative_mass_mg": (
                    str(self.cumulative_mass_mg)
                    if self.cumulative_mass_mg is not None
                    else None
                ),
                "canonical_amount_unit": canonical_target(self.amount_unit),
            }
        )
        return payload
