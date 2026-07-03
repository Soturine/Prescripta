from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ActiveIngredientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dcb_name: str
    normalized_name: str
    synonyms: list[str]
    therapeutic_classes: list[str]
    common_brands: list[str]
    jurisdiction: str
    source: str
    validation_status: str
    created_at: datetime
    updated_at: datetime


class DrugProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    active_ingredient_id: int
    commercial_name: str
    manufacturer: str | None = None
    concentration: str | None = None
    pharmaceutical_form: str | None = None
    allowed_routes: list[str]
    anvisa_registration_number: str | None = None
    bula_url: str | None = None
    source: str
    validation_status: str
    created_at: datetime
    updated_at: datetime


class MedicationKnowledgeSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    active_ingredient_id: int | None = None
    drug_product_id: int | None = None
    source_name: str
    source_type: str
    jurisdiction: str
    source_url: str | None = None
    retrieved_at: datetime | None = None
    version: str | None = None
    evidence_sections: list[str]
    confidence_level: str
    validation_status: str
    reviewer: str | None = None
    created_at: datetime
    updated_at: datetime


class ClinicalVocabularyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    code: str
    label: str
    normalized_label: str
    severity_weight: int
    description: str | None = None
    is_active: bool


class MedicationCatalogSearchResult(BaseModel):
    query: str
    match_type: str
    active_ingredient: ActiveIngredientRead
    matched_brands: list[str] = Field(default_factory=list)
    drug_products: list[DrugProductRead] = Field(default_factory=list)
    knowledge_sources: list[MedicationKnowledgeSourceRead] = Field(default_factory=list)


class AnvisaLookupResponse(BaseModel):
    query: str
    source: str
    jurisdiction: str
    status: str
    active_ingredient: str | None = None
    commercial_matches: list[str] = Field(default_factory=list)
    source_url: str
    validation_status: str
    guidance: str
