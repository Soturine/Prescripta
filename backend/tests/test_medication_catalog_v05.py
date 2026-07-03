from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database.seed import seed_demo_data
from app.domain.alert import RiskLevel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.repositories.catalog_repository import MedicationCatalogRepository
from app.schemas.prescription_schema import (
    AlertRead,
    PrescriptionExplainMedication,
    PrescriptionExplainPatient,
    PrescriptionExplainRequest,
)
from app.services.ai_explainer import AIExplainer
from app.services.anvisa_lookup_service import AnvisaMedicationLookupService
from app.services.controlled_vocabulary import normalize_patient_clinical_fields
from app.services.medication_catalog import MedicationCatalogService
from app.services.risk_engine import RiskEngine


def _seeded_catalog(db_session: Session) -> MedicationCatalogService:
    seed_demo_data(db_session)
    return MedicationCatalogService(MedicationCatalogRepository(db_session))


def test_brand_alias_search_resolves_novalgina_to_dipirona(db_session: Session) -> None:
    catalog = _seeded_catalog(db_session)

    results = catalog.search_by_active_ingredient_or_brand("Novalgina")

    assert results
    assert results[0]["match_type"] == "brand_alias"
    assert results[0]["active_ingredient"].dcb_name == "dipirona"
    assert "Novalgina" in results[0]["active_ingredient"].common_brands
    assert results[0]["active_ingredient"].jurisdiction == "BR"


def test_dipirona_and_required_aliases_share_same_active_ingredient(
    db_session: Session,
) -> None:
    catalog = _seeded_catalog(db_session)
    dipirona = catalog.resolve_active_ingredient("dipirona")
    assert dipirona is not None

    for alias in ["Novalgina", "Anador", "Dorflex", "Neosaldina", "Lisador"]:
        resolved = catalog.resolve_active_ingredient(alias)
        assert resolved is not None
        assert resolved.id == dipirona.id


def test_controlled_clinical_fields_replace_generic_values() -> None:
    normalized = normalize_patient_clinical_fields(
        {
            "renal_condition": "renal",
            "cardiac_condition": "cardiaco",
            "gastrointestinal_history": "gastrointestinal",
        }
    )

    assert normalized["renal_condition"] == "funcao_renal_a_revisar"
    assert normalized["cardiac_condition"] == "risco_cardiovascular_a_revisar"
    assert (
        normalized["gastrointestinal_history"]
        == "historico_gastrointestinal_a_revisar"
    )


def test_anvisa_lookup_uses_local_catalog_first_and_assisted_link_fallback(
    db_session: Session,
) -> None:
    seed_demo_data(db_session)
    service = AnvisaMedicationLookupService(db_session)

    local = service.search_local_first("Novalgina")
    unknown = service.search_local_first("Medicamento Sem Cadastro")

    assert local["status"] == "local_match"
    assert local["active_ingredient"] == "dipirona"
    assert local["jurisdiction"] == "BR"
    assert "consultas.anvisa.gov.br" in local["source_url"]
    assert unknown["status"] == "assisted_lookup"
    assert unknown["validation_status"] == "pending_review"


def test_brazilian_sources_have_priority_over_us_in_br_context(db_session: Session) -> None:
    catalog = _seeded_catalog(db_session)

    results = catalog.search_by_active_ingredient_or_brand("dipirona")
    jurisdictions = [source.jurisdiction for source in results[0]["knowledge_sources"]]

    assert jurisdictions[0] == "BR"
    assert "US" in jurisdictions
    assert jurisdictions.index("BR") < jurisdictions.index("US")


def test_rag_returns_evidence_with_jurisdiction_metadata() -> None:
    hits = RiskEngine().evaluate(
        _patient(renal_condition="funcao_renal_a_revisar"),
        _medication(),
        _prescription(),
    )
    assert hits.status.value in {"liberado", "atencao", "bloqueado"}

    from app.knowledge.rag_service import ClinicalRAGService

    evidence = ClinicalRAGService().retrieve_for_prescription(
        _patient(renal_condition="funcao_renal_a_revisar"),
        _medication(active_ingredient="dipirona", brand_name="Novalgina Demo"),
        _prescription(),
    )

    assert evidence
    assert any(item["jurisdiction"] == "BR" for item in evidence)
    assert all("validation_status" in item for item in evidence)


def test_ai_mentions_external_source_as_secondary_without_changing_decision() -> None:
    payload = _explain_request(
        rag_evidence=[
            {
                "source": "external.md",
                "source_name": "Referencia internacional demonstrativa",
                "jurisdiction": "US",
                "evidence_type": "external_reference",
                "validation_status": "demo",
            }
        ]
    )

    result = AIExplainer(Settings(ai_provider="fallback")).explain(
        payload,
        requester_role="medico",
    )

    assert result.prescription_status == "bloqueado"
    assert result.risk_level == "critico"
    assert "Fontes internacionais" in result.technical_summary


def test_risk_engine_keeps_critical_blocks() -> None:
    result = RiskEngine().evaluate(
        _patient(allergies=["dipirona"]),
        _medication(active_ingredient="dipirona", brand_name="Novalgina Demo"),
        _prescription(),
    )

    assert result.status.value == "bloqueado"
    assert result.risk_level == RiskLevel.CRITICAL


def _patient(**overrides: Any) -> Patient:
    values = {
        "id": 1,
        "name": "Paciente v05",
        "birth_date": None,
        "age": 60,
        "weight_kg": 70,
        "height_cm": 170,
        "allergies": [],
        "comorbidities": [],
        "current_medications": [],
        "renal_condition": None,
        "hepatic_condition": None,
        "cardiac_condition": None,
        "gastrointestinal_history": None,
        "hypertension": False,
        "diabetes": False,
        "pregnancy_or_lactation": None,
        "adverse_reactions": [],
        "clinical_notes": None,
        "clinical_profile_reviewed_at": None,
        "clinical_profile_completeness_score": 80,
    }
    values.update(overrides)
    return Patient(**values)


def _medication(**overrides: Any) -> Medication:
    values = {
        "id": 1,
        "active_ingredient_id": 1,
        "brand_name": "Ibuvida",
        "active_ingredient": "ibuprofeno",
        "commercial_aliases": ["Ibuvida", "Ibuvvida"],
        "therapeutic_class": "anti-inflamatorio nao esteroidal",
        "therapeutic_classes": ["anti-inflamatorio nao esteroidal"],
        "source_jurisdiction": "BR",
        "evidence_source_type": "manual_curated",
        "validation_status": "pending_review",
        "max_daily_dose_mg": 2400,
        "allowed_routes": ["oral"],
        "contraindications": [],
        "renal_caution": True,
        "gastrointestinal_caution": True,
        "organs_involved": ["renal", "gastrointestinal"],
    }
    values.update(overrides)
    return Medication(**values)


def _prescription() -> PrescriptionInput:
    return PrescriptionInput(
        dose_mg=500,
        frequency_per_day=2,
        route="oral",
        duration_days=3,
        indication="dor",
        professional_notes=None,
    )


def _explain_request(rag_evidence: list[dict]) -> PrescriptionExplainRequest:
    return PrescriptionExplainRequest(
        patient=PrescriptionExplainPatient(
            id=1,
            name="Paciente Fonte",
            birth_date=None,
            age=70,
            weight_kg=80,
            height_cm=170,
            allergies=["dipirona"],
            comorbidities=[],
            current_medications=[],
        ),
        medication=PrescriptionExplainMedication(
            id=1,
            brand_name="Novalgina Demo",
            active_ingredient="dipirona",
            therapeutic_class="analgesico",
            max_daily_dose_mg=4000,
            allowed_routes=["oral"],
            contraindications=[],
        ),
        dose_mg=500,
        frequency_per_day=2,
        route="oral",
        status="bloqueado",
        risk_level="critico",
        alerts=[
            AlertRead(
                code="ALLERGY_BLOCK",
                title="Alergia relevante identificada",
                description="Alergia coincide com medicamento.",
                severity="critico",
                recommendation="Bloquear a prescricao.",
            )
        ],
        recommendation="Nao prosseguir sem revisao humana.",
        human_review_required=True,
        user_profile="medico",
        rag_evidence=rag_evidence,
    )
