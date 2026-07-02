export type Patient = {
  id: number;
  name: string;
  birth_date: string | null;
  age: number | null;
  weight_kg: number;
  height_cm: number | null;
  allergies: string[];
  comorbidities: string[];
  current_medications: string[];
};

export type PatientPayload = Omit<Patient, "id">;
