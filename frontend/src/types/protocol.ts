export type ProtocolWarningLevel = "info" | "attention" | "high" | "critical";

export type ProtocolContextField = {
  name: string;
  label: string;
  field_type: "number" | "text" | "boolean" | "select" | "multiselect";
  required: boolean;
  unit?: string | null;
  helper?: string | null;
  options: string[];
};

export type ProtocolStep = {
  order: number;
  title: string;
  action: string;
  explanation: string;
  warning_level: ProtocolWarningLevel;
  requires_human_judgment: boolean;
  evidence_ref: string;
};

export type ProtocolCalculator = {
  id: string;
  label: string;
  description: string;
  input_fields: string[];
  source_note: string;
  requires_human_confirmation: boolean;
};

export type EmergencyProtocol = {
  id: string;
  slug: string;
  title: string;
  category: string;
  summary: string;
  clinical_goal: string;
  severity_level: ProtocolWarningLevel;
  audience: string;
  jurisdiction: string;
  source_name: string;
  source_url?: string | null;
  source_version?: string | null;
  validation_status: string;
  last_reviewed_at: string;
  disclaimer: string;
  red_flags: string[];
  immediate_measures: string[];
  medication_references: string[];
  cautions: string[];
  referral_criteria: string[];
  monitoring: string[];
  documentation_items: string[];
  do_not_apply_when: string[];
  human_judgment_points: string[];
  safety_notes: string[];
  context_fields: ProtocolContextField[];
  calculators: ProtocolCalculator[];
  steps: ProtocolStep[];
};

export type ProtocolCalculatedValue = {
  label: string;
  value: string;
  formula: string;
  source_ref: string;
  warning: string;
  requires_human_confirmation: boolean;
};

export type ProtocolEvidence = {
  evidence_ref: string;
  source_name: string;
  source_url?: string | null;
  source_version?: string | null;
  summary: string;
  validation_status: string;
};

export type ProtocolContext = Record<string, string | number | boolean | string[] | null>;

export type ProtocolRunPayload = {
  patient_id?: number | null;
  context: ProtocolContext;
  selected_step_orders?: number[];
  notes?: string | null;
};

export type ProtocolRunResult = {
  run_id: number;
  audit_event_id?: number | null;
  protocol_id: string;
  protocol_version: string;
  title: string;
  status: string;
  warning_level: ProtocolWarningLevel;
  patient_id?: number | null;
  patient_context_summary: Record<string, unknown>;
  triage_flags: string[];
  calculated_values: ProtocolCalculatedValue[];
  timeline: Array<Record<string, unknown>>;
  evidence: ProtocolEvidence[];
  audit_notice: string;
  educational_notice: string;
};

export type ProtocolExplainPayload = {
  context: ProtocolContext;
  run_id?: number | null;
  question?: string | null;
};

export type ProtocolExplainResult = {
  provider: string;
  model?: string | null;
  used_fallback: boolean;
  protocol_id: string;
  simple_explanation: string;
  professional_summary: string;
  safety_note: string;
  cited_evidence_refs: string[];
  structure_locked: boolean;
  educational_notice: string;
};

export type ProtocolReportPreview = {
  title: string;
  protocol_id: string;
  protocol_version?: string | null;
  run_id?: number | null;
  generated_report_id?: number | null;
  generated_at: string;
  report_lines: string[];
  report_payload: Record<string, unknown>;
  timeline: Array<Record<string, unknown>>;
  evidence: ProtocolEvidence[];
};
