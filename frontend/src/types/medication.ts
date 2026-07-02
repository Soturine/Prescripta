export type Medication = {
  id: number;
  brand_name: string;
  active_ingredient: string;
  therapeutic_class: string;
  max_daily_dose_mg: number;
  allowed_routes: string[];
  contraindications: string[];
  notes: string | null;
};

export type MedicationPayload = Omit<Medication, "id">;
