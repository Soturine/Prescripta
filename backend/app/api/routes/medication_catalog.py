from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.repositories.catalog_repository import MedicationCatalogRepository
from app.schemas.catalog_schema import (
    ActiveIngredientRead,
    AnvisaLookupResponse,
    ClinicalVocabularyRead,
    MedicationCatalogSearchResult,
)
from app.services.anvisa_lookup_service import AnvisaMedicationLookupService
from app.services.medication_catalog import MedicationCatalogService

router = APIRouter(tags=["medication-catalog"])
DbSession = Annotated[Session, Depends(get_db)]
CatalogReader = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM)),
]


@router.get(
    "/medication-catalog/search",
    response_model=list[MedicationCatalogSearchResult],
)
def search_medication_catalog(
    q: Annotated[str, Query(min_length=2)],
    db: DbSession,
    _current_user: CatalogReader,
) -> list[MedicationCatalogSearchResult]:
    repository = MedicationCatalogRepository(db)
    return MedicationCatalogService(repository).search_by_active_ingredient_or_brand(q)


@router.get(
    "/medication-catalog/active-ingredients",
    response_model=list[ActiveIngredientRead],
)
def list_active_ingredients(
    db: DbSession,
    _current_user: CatalogReader,
) -> list[ActiveIngredientRead]:
    return MedicationCatalogRepository(db).list_active_ingredients()


@router.get(
    "/medication-catalog/active-ingredients/{active_ingredient_id}",
    response_model=ActiveIngredientRead,
)
def get_active_ingredient(
    active_ingredient_id: int,
    db: DbSession,
    _current_user: CatalogReader,
) -> ActiveIngredientRead:
    ingredient = MedicationCatalogRepository(db).get_active_ingredient(active_ingredient_id)
    if ingredient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Princípio ativo não encontrado.",
        )
    return ingredient


@router.get(
    "/clinical-vocabulary",
    response_model=list[ClinicalVocabularyRead],
)
def list_clinical_vocabulary(
    db: DbSession,
    _current_user: CatalogReader,
    category: str | None = None,
) -> list[ClinicalVocabularyRead]:
    return MedicationCatalogRepository(db).list_vocabulary(category=category)


@router.get(
    "/medication-sources/anvisa/search",
    response_model=AnvisaLookupResponse,
)
def search_anvisa_sources(
    q: Annotated[str, Query(min_length=2)],
    db: DbSession,
    _current_user: CatalogReader,
) -> AnvisaLookupResponse:
    return AnvisaMedicationLookupService(db).search_local_first(q)
