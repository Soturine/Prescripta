import axios from "axios";

import type { AuditRecord, DashboardSummary } from "../types/audit";
import type {
  AICredentialPayload,
  AICredentialStatus,
  AIConnectionTestPayload,
  AIConnectionTestResult,
  AIModelListResponse,
  AIModelSelectPayload,
  AIProviderId,
  AIProviderInfo,
  AISettings,
} from "../types/aiSettings";
import type { LoginPayload, LoginResponse } from "../types/auth";
import type {
  ActiveIngredient,
  AnvisaLookupResponse,
  ClinicalVocabularyEntry,
  MedicationCatalogSearchResult,
} from "../types/catalog";
import type {
  AdverseEffectTaxonomyEntry,
  Medication,
  MedicationCounselingGeneratePayload,
  MedicationCounselingReviewPayload,
  MedicationCounselingSummary,
  MedicationPayload,
} from "../types/medication";
import type {
  ClinicalContextGraph,
  Patient,
  PatientFunctionalProfile,
  PatientFunctionalProfilePayload,
  PatientIdentifier,
  PatientIdentifierPayload,
  PatientPayload,
  QuickTriagePayload,
} from "../types/patient";
import type {
  CdsCheckPayload,
  CdsCheckResult,
  ClinicalImportBatch,
  ClinicalReconciliation,
  ClinicalReconciliationItem,
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

export async function fetchPatientFunctionalProfile(id: number) {
  const response = await api.get<PatientFunctionalProfile>(`/patients/${id}/functional-profile`);
  return response.data;
}

export async function updatePatientFunctionalProfile(
  id: number,
  payload: PatientFunctionalProfilePayload,
) {
  const response = await api.put<PatientFunctionalProfile>(
    `/patients/${id}/functional-profile`,
    payload,
  );
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

export async function fetchAdverseEffectTaxonomy() {
  const response = await api.get<AdverseEffectTaxonomyEntry[]>(
    "/medications/adverse-effect-taxonomy",
  );
  return response.data;
}

export async function fetchMedicationCounselingSummary(id: number) {
  const response = await api.get<MedicationCounselingSummary | null>(
    `/medications/${id}/counseling-summary`,
  );
  return response.data;
}

export async function generateMedicationCounselingSummary(
  id: number,
  payload: MedicationCounselingGeneratePayload = {},
) {
  const response = await api.post<MedicationCounselingSummary>(
    `/medications/${id}/counseling-summary/generate`,
    payload,
  );
  return response.data;
}

export async function reviewMedicationCounselingSummary(
  id: number,
  payload: MedicationCounselingReviewPayload,
) {
  const response = await api.post<MedicationCounselingSummary>(
    `/medications/${id}/counseling-summary/review`,
    payload,
  );
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

export async function fetchAIProviders() {
  const response = await api.get<AIProviderInfo[]>("/settings/ai/providers");
  return response.data;
}

export async function fetchCurrentAISettings() {
  const response = await api.get<AISettings>("/settings/ai/current");
  return response.data;
}

export async function fetchAIModels(provider: AIProviderId, refresh = false) {
  const response = await api.get<AIModelListResponse>("/settings/ai/models", {
    params: { provider, refresh },
  });
  return response.data;
}

export async function saveAICredential(payload: AICredentialPayload) {
  const response = await api.post<AICredentialStatus>("/settings/ai/credentials", payload);
  return response.data;
}

export async function deleteAICredential(provider: AIProviderId) {
  const response = await api.delete<AICredentialStatus>(`/settings/ai/credentials/${provider}`);
  return response.data;
}

export async function testAIConnection(payload: AIConnectionTestPayload) {
  const response = await api.post<AIConnectionTestResult>("/settings/ai/test", payload);
  return response.data;
}

export async function selectAIModel(payload: AIModelSelectPayload) {
  const response = await api.post<AISettings>("/settings/ai/select-model", payload);
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

export async function fetchClinicalReconciliation(id: number) {
  const response = await api.get<ClinicalReconciliation>(
    `/integrations/imports/${id}/reconciliation`,
  );
  return response.data;
}

export async function acceptClinicalReconciliationItem(
  batchId: number,
  itemId: string,
  justification: string | null,
) {
  const response = await api.post<ClinicalReconciliationItem>(
    `/integrations/imports/${batchId}/reconciliation/items/${encodeURIComponent(itemId)}/accept`,
    { justification },
  );
  return response.data;
}

export async function rejectClinicalReconciliationItem(
  batchId: number,
  itemId: string,
  justification: string | null,
) {
  const response = await api.post<ClinicalReconciliationItem>(
    `/integrations/imports/${batchId}/reconciliation/items/${encodeURIComponent(itemId)}/reject`,
    { justification },
  );
  return response.data;
}

export async function acceptClinicalReconciliationSafeItems(id: number) {
  const response = await api.post<ClinicalReconciliation>(
    `/integrations/imports/${id}/reconciliation/accept-safe`,
  );
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
