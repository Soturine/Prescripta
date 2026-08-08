export type PharmacyIntervention = {
  id: number;
  institution_id: string;
  patient_id: number;
  medication_id: number | null;
  pharmacist_user_id: number;
  intervention_type: string;
  severity: string;
  priority: string;
  problem: string;
  recommendation: string;
  source_refs: string[];
  dose_snapshot: Record<string, unknown>;
  status: string;
  idempotency_key: string;
  version: number;
  cosignature_required: boolean;
  cosigned_by_user_id: number | null;
  accepted: boolean | null;
  resolution: string | null;
  created_at: string;
  updated_at: string;
};

export type PharmacyInterventionPayload = {
  patient_id: number;
  medication_id?: number | null;
  intervention_type: string;
  severity: "low" | "moderate" | "high" | "critical";
  priority: "routine" | "priority" | "urgent";
  problem: string;
  recommendation: string;
  source_refs: string[];
  dose_snapshot: Record<string, unknown>;
  idempotency_key: string;
  cosignature_required?: boolean;
};
