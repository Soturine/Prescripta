export type ReportNarrative = {
  executive_summary: string;
  professional_explanation: string;
  patient_guidance: string;
  evidence_summary: string;
  missing_data_note: string;
  functional_context_note: string;
  reconciliation_summary: string;
  safety_counseling_summary: string;
  limitations_note: string;
  human_review_note: string;
  source_note: string;
  confidence: number;
  requires_human_review: boolean;
  warnings: string[];
  cited_source_ids: string[];
};

export type DecisionTimelineItem = {
  order: number;
  title: string;
  status: string;
  at?: string | null;
  details?: Record<string, unknown>;
};

export type DecisionEvidenceItem = {
  code?: string;
  severity?: string;
  rule_id?: string;
  source_id?: string;
  source_name?: string;
  jurisdiction?: string;
  validation_status?: string;
  evidence_summary?: string;
  evidence_type?: string;
  confidence?: string;
  review_status?: string;
};

export type ReportPreview = {
  title: string;
  report_type: string;
  report_mode: string;
  template_version: string;
  prescripta_version: string;
  evidence_bundle_hash: string;
  evidence_bundle: Record<string, unknown>;
  narrative: ReportNarrative;
  narrative_metadata: {
    provider: string;
    model: string | null;
    prompt_version: string;
    ai_used: boolean;
    fallback_used: boolean;
    status: string;
    response_time_ms: number | null;
    error_summary: string | null;
  };
  timeline: DecisionTimelineItem[];
  evidence: DecisionEvidenceItem[];
  html: string;
};

export type GeneratedReport = {
  id: number;
  report_type: string;
  target_type: string;
  target_id: string;
  generated_by_user_id: number | null;
  generated_at: string;
  template_version: string;
  prescripta_version: string;
  evidence_bundle_hash: string;
  ai_provider: string | null;
  ai_model: string | null;
  ai_prompt_version: string | null;
  ai_used: boolean;
  fallback_used: boolean;
  anonymized: boolean;
  file_hash: string | null;
  status: string;
  metadata_json: Record<string, unknown>;
};

export type AuditFilters = {
  user?: string;
  user_role?: string;
  patient?: string;
  medication?: string;
  active_ingredient?: string;
  protocol?: string;
  protocol_category?: string;
  protocol_severity?: string;
  protocol_version?: string;
  execution?: string;
  report_type?: string;
  action?: string;
  resource_type?: string;
  risk_level?: string;
  status?: string;
  severity?: string;
  ai_provider?: string;
  ai_model?: string;
  fallback_used?: boolean;
  source?: string;
  jurisdiction?: string;
  date_from?: string;
  date_to?: string;
  text?: string;
  sort?: "asc" | "desc";
  page?: number;
  page_size?: number;
};
