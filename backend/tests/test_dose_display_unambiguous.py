"""NEW-13: textos de dose sem notação científica, arredondamento ou ambiguidade decimal.

Inspirado na classe de falha do alerta Anvisa de tecnovigilância 4614 (Tasy EMR, 2024: número
decimal exibido sem o zero antes da vírgula). Antes, `Decimal.normalize()` gerava
"Dose diária calculada: 1.2E+3 mg. Limite cadastrado: 1E+3 mg".
"""

from __future__ import annotations

import re
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from app.domain.dose_units import format_clinical_decimal
from app.domain.medication import Medication
from app.domain.prescription import PrescriptionInput
from app.services.dose_calculator import check_max_daily_dose

DECIMALS = st.decimals(
    min_value=Decimal("0.000001"),
    max_value=Decimal("1000000"),
    places=6,
    allow_nan=False,
    allow_infinity=False,
)


@given(DECIMALS)
def test_display_round_trips_exactly_without_exponent(value: Decimal) -> None:
    text = format_clinical_decimal(value)
    assert "E" not in text.upper()
    assert "." not in text  # sem separador de milhar nem ponto decimal em pt-BR
    assert re.fullmatch(r"\d+(,\d*[1-9])?", text), text  # zero à esquerda; sem zero à direita
    assert Decimal(text.replace(",", ".")) == value  # nenhum arredondamento


def test_examples() -> None:
    assert format_clinical_decimal(Decimal("1E+3")) == "1000"
    assert format_clinical_decimal(Decimal("0.0625")) == "0,0625"
    assert format_clinical_decimal(0.5) == "0,5"
    assert format_clinical_decimal(Decimal("5.000")) == "5"


def test_daily_dose_alert_text_is_plain() -> None:
    medication = Medication(
        id=1,
        brand_name="Demo",
        active_ingredient="demo",
        therapeutic_class="teste",
        max_daily_dose_mg=1000,
        allowed_routes=["oral"],
        contraindications=[],
    )
    [alert] = check_max_daily_dose(
        medication, PrescriptionInput(dose_mg=600, frequency_per_day=2, route="oral")
    )
    assert "Dose diária calculada: 1200 mg" in alert.description
    assert "Limite cadastrado: 1000 mg" in alert.description
    assert "E+" not in alert.description
