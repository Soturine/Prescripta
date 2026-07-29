import type { Capability } from "./user";

export type PatientAccessGrant = {
  id: number;
  patient_id: number;
  user_id: number;
  institution_id: string;
  capability: Capability;
  purpose: string;
  reason: string | null;
  starts_at: string;
  expires_at: string | null;
  revoked_at: string | null;
  status: string;
  care_episode_id: string | null;
};

export type CareTeamMembership = {
  id: number;
  patient_id: number;
  user_id: number;
  institution_id: string;
  team_code: string;
  care_role: string;
  capabilities: Capability[];
  purpose: string;
  starts_at: string;
  expires_at: string | null;
  revoked_at: string | null;
};
