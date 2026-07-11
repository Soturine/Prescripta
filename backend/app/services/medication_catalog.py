from __future__ import annotations

from app.database.models import ActiveIngredientModel
from app.repositories.catalog_repository import MedicationCatalogRepository
from app.services.normalizer import normalize_text
from app.services.source_policy import sort_sources_by_jurisdiction


class MedicationCatalogService:
    def __init__(self, repository: MedicationCatalogRepository) -> None:
        self.repository = repository

    def normalize_medication_name(self, name: str | None) -> str:
        return normalize_text(name)

    def search_by_active_ingredient_or_brand(self, query: str) -> list[dict]:
        normalized_query = self.normalize_medication_name(query)
        if not normalized_query:
            return []

        results: list[dict] = []
        for ingredient in self.repository.list_active_ingredients():
            match_type = self._match_type(ingredient, normalized_query)
            products = self.repository.list_drug_products(ingredient.id)
            matched_brands = [
                product.commercial_name
                for product in products
                if self._matches_text(product.commercial_name, normalized_query)
            ]
            if not match_type and matched_brands:
                match_type = "brand_alias"
            if not match_type:
                continue

            sources = sort_sources_by_jurisdiction(
                self.repository.list_sources(active_ingredient_id=ingredient.id),
                jurisdiction_getter=lambda item: item.jurisdiction,
            )
            if not matched_brands:
                matched_brands = [
                    brand
                    for brand in ingredient.common_brands or []
                    if self._matches_text(brand, normalized_query)
                ]
            results.append(
                {
                    "query": query,
                    "match_type": match_type,
                    "active_ingredient": ingredient,
                    "matched_brands": matched_brands,
                    "drug_products": products,
                    "knowledge_sources": sources,
                }
            )
        return results

    def resolve_active_ingredient(self, query: str) -> ActiveIngredientModel | None:
        results = self.search_by_active_ingredient_or_brand(query)
        if not results:
            return None
        return results[0]["active_ingredient"]

    def find_alias_matches(self, query: str) -> list[str]:
        normalized_query = self.normalize_medication_name(query)
        if not normalized_query:
            return []
        matches: list[str] = []
        for ingredient in self.repository.list_active_ingredients():
            for alias in [*(ingredient.synonyms or []), *(ingredient.common_brands or [])]:
                if self._matches_text(alias, normalized_query):
                    matches.append(alias)
        return sorted(set(matches))

    def _match_type(
        self,
        ingredient: ActiveIngredientModel,
        normalized_query: str,
    ) -> str | None:
        names = [
            ingredient.dcb_name,
            ingredient.normalized_name,
            *(ingredient.synonyms or []),
        ]
        if any(self._matches_text(name, normalized_query) for name in names):
            return "active_ingredient"
        if any(
            self._matches_text(brand, normalized_query) for brand in ingredient.common_brands or []
        ):
            return "brand_alias"
        return None

    def _matches_text(self, value: str, normalized_query: str) -> bool:
        normalized_value = self.normalize_medication_name(value)
        return normalized_query == normalized_value or normalized_query in normalized_value
