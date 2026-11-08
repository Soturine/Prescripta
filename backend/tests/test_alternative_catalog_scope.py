"""Alternativas: catálogo inteiro (NEW-04) e avaliação honesta para revisão humana (NEW-11).

Antes: só os 50 primeiros cadastros eram considerados, e cada candidato era avaliado pelo
RiskEngine isolado, com a dose do medicamento original, podendo aparecer como `liberado`.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.database.models import MedicationModel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.repositories.medication_repository import MedicationRepository
from app.services.alternative_service import AlternativeService

USER = SimpleNamespace(
    role="medico", specialty_code="medicina_geral", credential_verification_status="verified"
)


def _record(brand: str, group: str, **extra: object) -> MedicationModel:
    values: dict[str, object] = {
        "brand_name": brand,
        "active_ingredient": brand.lower(),
        "therapeutic_class": f"classe própria de {brand}",
        "alternative_group": group,
        "max_daily_dose_mg": 1000,
        "allowed_routes": ["oral"],
        "contraindications": [],
    }
    values.update(extra)
    return MedicationModel(**values)


def _patient() -> Patient:
    return Patient(
        id=1,
        name="Paciente fictício",
        birth_date=None,
        age=40,
        weight_kg=70,
        height_cm=170,
        allergies=[],
        comorbidities=[],
        current_medications=[],
    )


def _options(db, original, dose_mg: float) -> list[dict]:
    return AlternativeService(MedicationRepository(db)).evaluated_options(
        _patient(),
        Medication.from_record(original),
        PrescriptionInput(dose_mg=dose_mg, frequency_per_day=1, route="oral"),
        should_include=True,
        user=USER,
    )


def test_alternatives_consider_the_whole_catalog(db_session) -> None:
    original = _record("Aaa Original", "grupo-alvo")
    db_session.add(original)
    db_session.add_all(_record(f"Filler {index:03d}", f"outro-{index}") for index in range(520))
    late_alternative = _record("Zzz Alternativa", "grupo-alvo")
    db_session.add(late_alternative)
    db_session.commit()

    options = _options(db_session, original, 10)

    assert [option["medication_id"] for option in options] == [late_alternative.id]


def test_alternative_is_never_released_and_dose_is_not_inherited(db_session) -> None:
    original = _record("Original", "grupo-alvo")
    alternative = _record("Alternativa", "grupo-alvo", max_daily_dose_mg=10)
    db_session.add_all([original, alternative])
    db_session.commit()

    for dose in (1, 5000):  # dose do ORIGINAL: baixa (antes: "liberado") e absurda
        [option] = _options(db_session, original, dose)
        assert option["status"] == "atencao"
        assert option["review_status"] == "candidate_for_human_review"
        assert option["dose_assessment"] == "not_evaluated_for_alternative"
        assert option["decision_status"] != "evaluated_no_issue"
        assert not any(alert["code"].startswith(("MAX_", "DOSE")) for alert in option["top_alerts"])


def test_screening_findings_still_block(db_session) -> None:
    original = _record("Original", "grupo-alvo")
    alternative = _record("Alergenica", "grupo-alvo")
    db_session.add_all([original, alternative])
    db_session.commit()
    patient = _patient()
    patient.allergies.append("alergenica")

    [option] = AlternativeService(MedicationRepository(db_session)).evaluated_options(
        patient,
        Medication.from_record(original),
        PrescriptionInput(dose_mg=10, frequency_per_day=1, route="oral"),
        should_include=True,
        user=USER,
    )
    assert option["status"] == "bloqueado"
    assert any("ALLERG" in alert["code"] for alert in option["top_alerts"])


def test_ranking_is_by_similarity_then_name(db_session) -> None:
    original = _record(
        "Original", "grupo-alvo", therapeutic_action="analgesia", related_medications=["aaa rel"]
    )
    related = _record("Aaa Rel", "outro")
    same_action = _record("Bbb Acao", "outro-2", therapeutic_action="analgesia")
    same_group_z = _record("Zzz Grupo", "grupo-alvo")
    same_group_m = _record("Mmm Grupo", "grupo-alvo")
    db_session.add_all([original, related, same_action, same_group_z, same_group_m])
    db_session.commit()

    options = _options(db_session, original, 10)

    assert [option["name"] for option in options] == [
        "Mmm Grupo",
        "Zzz Grupo",
        "Bbb Acao",
        "Aaa Rel",
    ]
    assert [option["similarity_kind"] for option in options] == [
        "alternative_group",
        "alternative_group",
        "therapeutic_action",
        "related",
    ]


def test_placeholder_class_is_not_similarity(db_session) -> None:
    """NEW-20: classe-marcador do seed agrupava antibiótico, anestésico e antidepressivo."""
    placeholder = "demo pendente de revisão"
    original = _record("Analgesico Demo", "", therapeutic_class=placeholder)
    original.alternative_group = None
    unrelated = _record("Amoxicilina Demo", "", therapeutic_class=placeholder)
    unrelated.alternative_group = None
    same_class = _record("Analgesico Irmao", "", therapeutic_class="classe analgésica sintética")
    same_class.alternative_group = None
    db_session.add_all([original, unrelated, same_class])
    db_session.commit()

    assert _options(db_session, original, 10) == []

    original.therapeutic_class = "classe analgésica sintética"
    db_session.commit()
    [option] = _options(db_session, original, 10)
    assert option["name"] == "Analgesico Irmao"
    assert option["similarity_kind"] == "therapeutic_class"
