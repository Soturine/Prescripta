from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import quote_plus

from sqlalchemy.orm import Session

from app.database.models import ActiveIngredientModel, MedicationKnowledgeSourceModel
from app.repositories.catalog_repository import MedicationCatalogRepository
from app.services.medication_catalog import MedicationCatalogService


class AnvisaMedicationLookupService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.catalog_repository = MedicationCatalogRepository(db)
        self.catalog_service = MedicationCatalogService(self.catalog_repository)

    def search_local_first(self, query: str) -> dict:
        local_results = self.catalog_service.search_by_active_ingredient_or_brand(query)
        source_url = self.build_anvisa_bulario_search_url(query)
        if local_results:
            first = local_results[0]
            ingredient = first["active_ingredient"]
            return {
                "query": query,
                "source": "anvisa_bulario",
                "jurisdiction": "BR",
                "status": "local_match",
                "active_ingredient": ingredient.dcb_name,
                "commercial_matches": first["matched_brands"] or ingredient.common_brands,
                "source_url": source_url,
                "validation_status": ingredient.validation_status,
                "guidance": (
                    "Registro encontrado no catalogo local. A consulta externa fica assistida "
                    "por link oficial e deve permanecer pendente de revisao quando criada."
                ),
            }
        return {
            "query": query,
            "source": "anvisa_bulario",
            "jurisdiction": "BR",
            "status": "assisted_lookup",
            "active_ingredient": None,
            "commercial_matches": [],
            "source_url": source_url,
            "validation_status": "pending_review",
            "guidance": (
                "Nenhuma API publica oficial foi assumida nesta versao. Use o link assistido "
                "para consulta no Bulario/Anvisa e revise manualmente antes de validar."
            ),
        }

    def build_anvisa_bulario_search_url(self, query: str) -> str:
        return f"https://consultas.anvisa.gov.br/#/bulario/q/?nomeProduto={quote_plus(query)}"

    def lookup_dcb_reference(self, query: str) -> dict:
        return {
            "query": query,
            "source": "DCB",
            "jurisdiction": "BR",
            "status": "manual_reference_required",
            "source_url": "https://www.gov.br/anvisa/pt-br/assuntos/farmacopeia/dcb",
            "validation_status": "pending_review",
        }

    def create_pending_review_record(self, result: dict) -> ActiveIngredientModel:
        ingredient = ActiveIngredientModel(
            dcb_name=result.get("active_ingredient") or result["query"],
            normalized_name=self.catalog_service.normalize_medication_name(
                result.get("active_ingredient") or result["query"]
            ),
            synonyms=[],
            therapeutic_classes=[],
            common_brands=list(result.get("commercial_matches") or []),
            jurisdiction="BR",
            source="anvisa_bulario",
            validation_status="pending_review",
        )
        self.db.add(ingredient)
        self.db.commit()
        self.db.refresh(ingredient)
        return ingredient

    def cache_lookup_result(self, result: dict) -> MedicationKnowledgeSourceModel:
        source = MedicationKnowledgeSourceModel(
            source_name="Anvisa Bulario Eletronico",
            source_type="anvisa_bulario",
            jurisdiction="BR",
            source_url=result["source_url"],
            retrieved_at=datetime.now(UTC),
            version="v0.5.0-assisted-link",
            evidence_sections=["consulta assistida"],
            confidence_level="pending_review",
            validation_status=result.get("validation_status", "pending_review"),
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source
