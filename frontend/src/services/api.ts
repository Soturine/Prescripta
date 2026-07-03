import axios from "axios";

import type { AuditRecord, DashboardSummary } from "../types/audit";
import type { LoginPayload, LoginResponse } from "../types/auth";
import type {
  ActiveIngredient,
  AnvisaLookupResponse,
  ClinicalVocabularyEntry,
  MedicationCatalogSearchResult,
} from "../types/catalog";
import type { Medication, MedicationPayload } from "../types/medication";
import type {
  ClinicalContextGraph,
  Patient,
  PatientIdentifier,
  PatientIdentifierPayload,
  PatientPayload,
  QuickTriagePayload,
} from "../types/patient";
import type {
  CdsCheckPayload,
  CdsCheckResult,
  ClinicalImportBatch,
  ImportConsentPayload,
} from "../types/integration";
import type {
  PrescriptionCheckPayload,
  PrescriptionCheckResult,
  PrescriptionExplanationPayload,
  PrescriptionExplanationResult,
} from "../types/prescription";
import type { User, UserCreatePayload, UserRole } from "../types/user";

const baseURL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";
export const AUTH_TOKEN_KEY = "prescripta_access_token";

export const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

const storedToken = localStorage.getItem(AUTH_TOKEN_KEY);
if (storedToken) {
  api.defaults.headers.common.Authorization = `Bearer ${storedToken}`;
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuthToken();
      window.dispatchEvent(new Event("prescripta:auth-expired"));
    }
    return Promise.reject(error);
  },
);

export function setAuthToken(token: string) {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  api.defaults.headers.common.Authorization = `Bearer ${token}`;
}

export function clearAuthToken() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  delete api.defaults.headers.common.Authorization;
}

export async function login(payload: LoginPayload) {
  const response = await api.post<LoginResponse>("/auth/login", payload);
  return response.data;
}

export async function fetchMe() {
  const response = await api.get<User>("/auth/me");
  return response.data;
}

export async function fetchDashboard() {
  const response = await api.get<DashboardSummary>("/dashboard");
  return response.data;
}

export async function fetchPatients() {
  const response = await api.get<Patient[]>("/patients");
  return response.data;
}

export async function fetchPatient(id: number) {
  const response = await api.get<Patient>(`/patients/${id}`);
  return response.data;
}

export async function fetchPatientClinicalContext(id: number) {
  const response = await api.get<ClinicalContextGraph>(`/patients/${id}/clinical-context`);
  return response.data;
}

export async function createPatient(payload: PatientPayload) {
  const response = await api.post<Patient>("/patients", payload);
  return response.data;
}

export async function updatePatient(id: number, payload: PatientPayload) {
  const response = await api.put<Patient>(`/patients/${id}`, payload);
  return response.data;
}

export async function fetchPatientIdentifiers(id: number) {
  const response = await api.get<PatientIdentifier[]>(`/patients/${id}/identifiers`);
  return response.data;
}

export async function createPatientIdentifier(id: number, payload: PatientIdentifierPayload) {
  const response = await api.post<PatientIdentifier>(`/patients/${id}/identifiers`, payload);
  return response.data;
}

export async function quickTriagePatient(id: number, payload: QuickTriagePayload) {
  const response = await api.patch<Patient>(`/patients/${id}/quick-triage`, payload);
  return response.data;
}

export async function fetchMedications() {
  const response = await api.get<Medication[]>("/medications");
  return response.data;
}

export async function fetchActiveIngredients() {
  const response = await api.get<ActiveIngredient[]>("/medication-catalog/active-ingredients");
  return response.data;
}

export async function searchMedicationCatalog(query: string) {
  const response = await api.get<MedicationCatalogSearchResult[]>("/medication-catalog/search", {
    params: { q: query },
  });
  return response.data;
}

export async function fetchClinicalVocabulary(category?: string) {
  const response = await api.get<ClinicalVocabularyEntry[]>("/clinical-vocabulary", {
    params: category ? { category } : undefined,
  });
  return response.data;
}

export async function lookupAnvisaSource(query: string) {
  const response = await api.get<AnvisaLookupResponse>("/medication-sources/anvisa/search", {
    params: { q: query },
  });
  return response.data;
}

export async function createMedication(payload: MedicationPayload) {
  const response = await api.post<Medication>("/medications", payload);
  return response.data;
}

export async function updateMedication(id: number, payload: MedicationPayload) {
  const response = await api.put<Medication>(`/medications/${id}`, payload);
  return response.data;
}

export async function checkPrescription(payload: PrescriptionCheckPayload) {
  const response = await api.post<PrescriptionCheckResult>("/prescriptions/check", payload);
  return response.data;
}

export async function explainPrescription(payload: PrescriptionExplanationPayload) {
  const response = await api.post<PrescriptionExplanationResult>(
    "/prescriptions/explain",
    payload,
  );
  return response.data;
}

export async function fetchAudit() {
  const response = await api.get<AuditRecord[]>("/audit");
  return response.data;
}

export async function fetchClinicalImports() {
  const response = await api.get<ClinicalImportBatch[]>("/integrations/imports");
  return response.data;
}

export async function fetchClinicalImport(id: number) {
  const response = await api.get<ClinicalImportBatch>(`/integrations/imports/${id}`);
  return response.data;
}

export async function importClinicalJson(
  consent: ImportConsentPayload,
  payload: Record<string, unknown>,
) {
  const response = await api.post<ClinicalImportBatch>("/integrations/json/import", {
    ...consent,
    payload,
  });
  return response.data;
}

export async function importClinicalFhir(
  consent: ImportConsentPayload,
  bundle: Record<string, unknown>,
) {
  const response = await api.post<ClinicalImportBatch>("/integrations/fhir/import-bundle", {
    ...consent,
    bundle,
  });
  return response.data;
}

export async function importClinicalCsv(consent: ImportConsentPayload, csv_text: string) {
  const response = await api.post<ClinicalImportBatch>("/integrations/csv/import", {
    ...consent,
    csv_text,
  });
  return response.data;
}

export async function acceptClinicalImport(id: number) {
  const response = await api.post<ClinicalImportBatch>(`/integrations/imports/${id}/accept`);
  return response.data;
}

export async function rejectClinicalImport(id: number, reason: string | null) {
  const response = await api.post<ClinicalImportBatch>(`/integrations/imports/${id}/reject`, {
    reason,
  });
  return response.data;
}

export async function checkCdsPrescription(payload: CdsCheckPayload) {
  const response = await api.post<CdsCheckResult>("/cds/prescription-check", payload);
  return response.data;
}

export async function fetchUsers() {
  const response = await api.get<User[]>("/users");
  return response.data;
}

export async function createUser(payload: UserCreatePayload) {
  const response = await api.post<User>("/users", payload);
  return response.data;
}

export async function updateUserStatus(id: number, is_active: boolean) {
  const response = await api.patch<User>(`/users/${id}/status`, { is_active });
  return response.data;
}

export async function updateUserRole(id: number, role: UserRole) {
  const response = await api.patch<User>(`/users/${id}/role`, { role });
  return response.data;
}
