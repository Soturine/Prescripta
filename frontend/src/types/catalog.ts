export type ActiveIngredient = {
  id: number;
  dcb_name: string;
  normalized_name: string;
  synonyms: string[];
  therapeutic_classes: string[];
  common_brands: string[];
  jurisdiction: string;
  source: string;
  validation_status: string;
  created_at: string;
  updated_at: string;
};

export type DrugProduct = {
  id: number;
  active_ingredient_id: number;
  commercial_name: string;
  manufacturer: string | null;
  concentration: string | null;
  pharmaceutical_form: string | null;
  allowed_routes: string[];
  anvisa_registration_number: string | null;
  bula_url: string | null;
  source: string;
  validation_status: string;
  created_at: string;
  updated_at: string;
};

export type MedicationKnowledgeSource = {
  id: number;
  active_ingredient_id: number | null;
  drug_product_id: number | null;
  source_name: string;
  source_type: string;
  jurisdiction: string;
  source_url: string | null;
  retrieved_at: string | null;
  version: string | null;
  evidence_sections: string[];
  confidence_level: string;
  validation_status: string;
  reviewer: string | null;
  created_at: string;
  updated_at: string;
};

export type ClinicalVocabularyEntry = {
  id: number;
  category: string;
  code: string;
  label: string;
  normalized_label: string;
  severity_weight: number;
  description: string | null;
  is_active: boolean;
};

export type MedicationCatalogSearchResult = {
  query: string;
  match_type: "active_ingredient" | "brand_alias" | string;
  active_ingredient: ActiveIngredient;
  matched_brands: string[];
  drug_products: DrugProduct[];
  knowledge_sources: MedicationKnowledgeSource[];
};

export type AnvisaLookupResponse = {
  query: string;
  source: string;
  jurisdiction: string;
  status: string;
  active_ingredient: string | null;
  commercial_matches: string[];
  source_url: string;
  validation_status: string;
  guidance: string;
};
