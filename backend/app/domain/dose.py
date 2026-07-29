from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any


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
    UNSUPPORTED = "unsupported"


MASS_TO_MG: dict[str, Decimal] = {
    "g": Decimal("1000"),
    "mg": Decimal("1"),
    "mcg": Decimal("0.001"),
    "ug": Decimal("0.001"),
    "\u00b5g": Decimal("0.001"),
    "ng": Decimal("0.000001"),
}
VOLUME_TO_ML: dict[str, Decimal] = {"l": Decimal("1000"), "ml": Decimal("1")}


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


def normalize_unit(value: str | None) -> str:
    return str(value or "").strip().lower().replace("\u03bc", "\u00b5")


def convert_mass(value: Decimal, from_unit: str, to_unit: str) -> Decimal | None:
    source = MASS_TO_MG.get(normalize_unit(from_unit))
    target = MASS_TO_MG.get(normalize_unit(to_unit))
    if source is None or target is None:
        return None
    return value * source / target


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

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", decimal_value(self.amount))
        object.__setattr__(self, "amount_unit", normalize_unit(self.amount_unit))
        object.__setattr__(
            self,
            "administration_kind",
            AdministrationKind(self.administration_kind),
        )
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
        if self.frequency_per_day is not None and self.frequency_per_day <= 0:
            raise ValueError("Frequência deve ser maior que zero.")
        if self.administration_kind == AdministrationKind.CONTINUOUS and not self.rate_value:
            raise ValueError("Infusão contínua exige taxa explícita.")
        if bool(self.concentration_value) != bool(self.concentration_unit):
            raise ValueError("Concentração exige valor e unidade.")
        if bool(self.volume) != bool(self.volume_unit):
            raise ValueError("Volume exige valor e unidade.")
        if bool(self.rate_value) != bool(self.rate_unit):
            raise ValueError("Taxa exige valor e unidade.")

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
        )

    @property
    def dimension(self) -> DoseDimension:
        if self.rate_value is not None or self.administration_kind == AdministrationKind.CONTINUOUS:
            return DoseDimension.RATE
        if self.procedure_context:
            return DoseDimension.PROCEDURE
        if self.amount_unit in MASS_TO_MG:
            return DoseDimension.PER_ADMINISTRATION
        return DoseDimension.UNSUPPORTED

    def amount_as(self, unit: str) -> Decimal | None:
        return convert_mass(self.amount, self.amount_unit, unit)

    @property
    def amount_mg(self) -> Decimal | None:
        return self.amount_as("mg")

    @property
    def daily_mass_mg(self) -> Decimal | None:
        if self.dimension in {DoseDimension.RATE, DoseDimension.PROCEDURE}:
            return None
        amount_mg = self.amount_mg
        if amount_mg is None or self.frequency_per_day is None:
            return None
        return amount_mg * self.frequency_per_day

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key, value in list(payload.items()):
            if isinstance(value, Decimal):
                payload[key] = str(value)
            elif isinstance(value, StrEnum):
                payload[key] = value.value
        payload["dimension"] = self.dimension.value
        payload["amount_mg"] = str(self.amount_mg) if self.amount_mg is not None else None
        payload["daily_mass_mg"] = (
            str(self.daily_mass_mg) if self.daily_mass_mg is not None else None
        )
        return payload
