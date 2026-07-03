from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    ActiveIngredientModel,
    ClinicalVocabularyModel,
    DrugProductModel,
    MedicationKnowledgeSourceModel,
)


class MedicationCatalogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active_ingredients(self) -> list[ActiveIngredientModel]:
        return list(
            self.db.scalars(
                select(ActiveIngredientModel).order_by(ActiveIngredientModel.dcb_name)
            )
        )

    def get_active_ingredient(self, active_ingredient_id: int) -> ActiveIngredientModel | None:
        return self.db.get(ActiveIngredientModel, active_ingredient_id)

    def find_active_by_normalized_name(self, normalized_name: str) -> ActiveIngredientModel | None:
        return self.db.scalar(
            select(ActiveIngredientModel).where(
                ActiveIngredientModel.normalized_name == normalized_name
            )
        )

    def list_drug_products(
        self, active_ingredient_id: int | None = None
    ) -> list[DrugProductModel]:
        statement = select(DrugProductModel).order_by(DrugProductModel.commercial_name)
        if active_ingredient_id is not None:
            statement = statement.where(
                DrugProductModel.active_ingredient_id == active_ingredient_id
            )
        return list(self.db.scalars(statement))

    def list_sources(
        self,
        active_ingredient_id: int | None = None,
        drug_product_id: int | None = None,
    ) -> list[MedicationKnowledgeSourceModel]:
        statement = select(MedicationKnowledgeSourceModel).order_by(
            MedicationKnowledgeSourceModel.jurisdiction,
            MedicationKnowledgeSourceModel.source_name,
        )
        if active_ingredient_id is not None:
            statement = statement.where(
                MedicationKnowledgeSourceModel.active_ingredient_id == active_ingredient_id
            )
        if drug_product_id is not None:
            statement = statement.where(
                MedicationKnowledgeSourceModel.drug_product_id == drug_product_id
            )
        return list(self.db.scalars(statement))

    def list_vocabulary(self, category: str | None = None) -> list[ClinicalVocabularyModel]:
        statement = select(ClinicalVocabularyModel).where(
            ClinicalVocabularyModel.is_active.is_(True)
        )
        if category:
            statement = statement.where(ClinicalVocabularyModel.category == category)
        return list(
            self.db.scalars(
                statement.order_by(
                    ClinicalVocabularyModel.category,
                    ClinicalVocabularyModel.severity_weight,
                    ClinicalVocabularyModel.label,
                )
            )
        )
