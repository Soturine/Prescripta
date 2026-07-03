export type Medication = {
  id: number;
  brand_name: string;
  active_ingredient: string;
  therapeutic_class: string;
  max_daily_dose_mg: number;
  max_duration_days: number | null;
  max_cumulative_dose_mg: number | null;
  condition_specific_limits: Record<string, number>;
  allowed_routes: string[];
  contraindications: string[];
  renal_caution: boolean;
  hepatic_caution: boolean;
  cardiac_caution: boolean;
  gastrointestinal_caution: boolean;
  elderly_caution: boolean;
  metabolism_organs: string[];
  elimination_organs: string[];
  organs_involved: string[];
  relevant_adverse_effects: string[];
  structured_contraindications: string[];
  therapeutic_action: string | null;
  alternative_group: string | null;
  related_medications: string[];
  knowledge_source: string | null;
  notes: string | null;
};

export type MedicationPayload = Omit<Medication, "id">;
