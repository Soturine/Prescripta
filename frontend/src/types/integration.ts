export type ClinicalSourceRecord = {
  id: number;
  batch_id: number;
  record_type: string;
  source_payload: Record<string, unknown>;
  mapped_payload: Record<string, unknown>;
  confidence: number;
  accepted_by_user: boolean;
  rejected_reason: string | null;
  created_at: string;
};

export type ClinicalImportBatch = {
  id: number;
  source_system: string;
  source_type: string;
  imported_by: number | null;
  patient_id: number | null;
  consent_id: number | null;
  status: "pending_review" | "accepted" | "rejected" | "failed";
  imported_at: string;
  finished_at: string | null;
  errors: string[];
  records: ClinicalSourceRecord[];
  educational_notice: string;
};

export type ImportConsentPayload = {
  consent_confirmed: boolean;
  purpose: string;
  authorized_by: string;
  source_system: string;
  patient_id: number | null;
};

export type CdsCheckPayload = {
  patient: Record<string, unknown>;
  medication_request: Record<string, unknown>;
  allergies: string[];
  conditions: string[];
  current_medications: string[];
  observations: Array<Record<string, unknown>>;
  persist: boolean;
};

export type CdsCheckResult = {
  status: string;
  risk_level: string;
  alerts: Array<{
    code: string;
    title: string;
    description: string;
    severity: string;
    recommendation: string;
  }>;
  cards: Array<{
    summary: string;
    indicator: string;
    detail: string;
    source: Record<string, unknown>;
  }>;
  audit_id: string;
  educational_notice: string;
};
