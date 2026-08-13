import axios from "axios";

import type { AuditPage, DashboardSummary } from "../types/audit";
import type { CareTeamMembership, PatientAccessGrant } from "../types/access";
import type {
  AICredentialPayload,
  AICredentialStatus,
  AIHealth,
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
import type { ApiHealth } from "../types/health";
import type {
  AdverseEffectTaxonomyEntry,
  Medication,
  MedicationBulkImportPayload,
  MedicationCounselingGeneratePayload,
  MedicationCounselingReviewPayload,
  MedicationCounselingSummary,
  MedicationKnowledgeCurationItem,
  MedicationKnowledgeLookupPayload,
  MedicationKnowledgeReviewPayload,
  MedicationPayload,
} from "../types/medication";
import type {
  ClinicalContextGraph,
  Patient,
  PatientClinicalDocument,
  PatientClinicalDocumentPayload,
  PatientDocumentExtraction,
  PatientDocumentReviewPayload,
  PatientFunctionalProfile,
  PatientFunctionalProfilePayload,
  PatientIdentifier,
  PatientIdentifierPayload,
  PatientKnowledgeBundle,
  PatientPayload,
  PatientPsychologicalContext,
  PatientPsychologicalContextPayload,
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
  DecisionOverride,
  PrescriptionCheckPayload,
  PrescriptionCheckResult,
  PrescriptionExplanationPayload,
  PrescriptionExplanationResult,
} from "../types/prescription";
import type {
  EmergencyProtocol,
  ProtocolEvidence,
  ProtocolExplainPayload,
  ProtocolExplainResult,
  ProtocolReportPreview,
  ProtocolRunPayload,
  ProtocolRunResult,
} from "../types/protocol";
import type {
  AuditFilters,
  DecisionEvidenceItem,
  DecisionTimelineItem,
  GeneratedReport,
  ReportPreview,
} from "../types/report";
import type {
  AIInteraction,
  AnalysisPlan,
  AnalysisPlanPayload,
  AnalysisRun,
  CohortDefinition,
  CohortRun,
  CohortVersion,
  ComparativeAnalysis,
  ConceptSet,
  ConceptSetVersion,
  DataQualityFinding,
  DataQualityRun,
  EvidenceLink,
  EvidenceSource,
  EvidenceExtraction,
  EvidenceSearchPlan,
  OutcomeDefinition,
  PatientJourney,
  ResearchStudy,
  ResearchStudyPayload,
  ResearchWorkspace,
  ResearchPackage,
  ResearchAgentRun,
  ResearchQueryPreview,
  StudyProtocolVersion,
  StudyWorkspace,
} from "../types/research";
import type {
  OmopCompatibility,
  OmopEtlRun,
  TerminologyConceptPage,
  TerminologyMapping,
  TerminologyRelease,
  TerminologySource,
} from "../types/terminology";
import type {
  PharmacyIntervention,
  PharmacyInterventionPayload,
} from "../types/pharmacy";
import type {
  User,
  UserClinicalProfilePayload,
  UserCreatePayload,
  UserRole,
} from "../types/user";

const baseURL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";
export const api = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

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
  api.defaults.headers.common.Authorization = `Bearer ${token}`;
}

export function clearAuthToken() {
  delete api.defaults.headers.common.Authorization;
}

export async function login(payload: LoginPayload) {
  const response = await api.post<LoginResponse>("/auth/login", payload);
  return response.data;
}

export async function logoutSession() {
  await api.post("/auth/logout");
}

export async function fetchMe() {
  const response = await api.get<User>("/auth/me");
  return response.data;
}

export async function fetchDashboard() {
  const response = await api.get<DashboardSummary>("/dashboard");
  return response.data;
}

export async function fetchApiHealth() {
  const response = await api.get<ApiHealth>("/health");
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

export async function fetchPatientPsychologicalContext(id: number) {
  const response = await api.get<PatientPsychologicalContext>(
    `/patients/${id}/psychological-context`,
    { params: { purpose: "treatment" } },
  );
  return response.data;
}

export async function updatePatientPsychologicalContext(
  id: number,
  payload: PatientPsychologicalContextPayload,
) {
  const response = await api.put<PatientPsychologicalContext>(
    `/patients/${id}/psychological-context`,
    payload,
  );
  return response.data;
}

export async function fetchPatientAccessGrants(patientId: number) {
  const response = await api.get<PatientAccessGrant[]>(
    `/access/patients/${patientId}/grants`,
  );
  return response.data;
}

export async function createPatientAccessGrant(
  patientId: number,
  payload: {
    user_id: number;
    capability: string;
    purpose: string;
    reason: string;
  },
) {
  const response = await api.post<PatientAccessGrant>(
    `/access/patients/${patientId}/grants`,
    payload,
  );
  return response.data;
}

export async function revokePatientAccessGrant(
  grantId: number,
  reason: string,
) {
  const response = await api.post<PatientAccessGrant>(
    `/access/grants/${grantId}/revoke`,
    {
      reason,
    },
  );
  return response.data;
}

export async function fetchPatientCareTeam(patientId: number) {
  const response = await api.get<CareTeamMembership[]>(
    `/access/patients/${patientId}/care-team`,
  );
  return response.data;
}

export async function fetchPatientClinicalContext(id: number) {
  const response = await api.get<ClinicalContextGraph>(
    `/patients/${id}/clinical-context`,
  );
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
  const response = await api.get<PatientIdentifier[]>(
    `/patients/${id}/identifiers`,
  );
  return response.data;
}

export async function createPatientIdentifier(
  id: number,
  payload: PatientIdentifierPayload,
) {
  const response = await api.post<PatientIdentifier>(
    `/patients/${id}/identifiers`,
    payload,
  );
  return response.data;
}

export async function quickTriagePatient(
  id: number,
  payload: QuickTriagePayload,
) {
  const response = await api.patch<Patient>(
    `/patients/${id}/quick-triage`,
    payload,
  );
  return response.data;
}

export async function fetchPatientFunctionalProfile(id: number) {
  const response = await api.get<PatientFunctionalProfile>(
    `/patients/${id}/functional-profile`,
  );
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

export async function fetchPatientDocuments(id: number) {
  const response = await api.get<PatientClinicalDocument[]>(
    `/patients/${id}/documents`,
  );
  return response.data;
}

export async function createPatientDocument(
  id: number,
  payload: PatientClinicalDocumentPayload,
) {
  const response = await api.post<PatientClinicalDocument>(
    `/patients/${id}/documents`,
    payload,
  );
  return response.data;
}

export async function extractPatientDocument(id: number, documentId: number) {
  const response = await api.post<PatientDocumentExtraction>(
    `/patients/${id}/documents/${documentId}/extract`,
  );
  return response.data;
}

export async function reviewPatientDocumentExtraction(
  id: number,
  extractionId: number,
  payload: PatientDocumentReviewPayload,
) {
  const response = await api.post<PatientDocumentExtraction>(
    `/patients/${id}/document-extractions/${extractionId}/review`,
    payload,
  );
  return response.data;
}

export async function fetchPatientTimeline(id: number) {
  const response = await api.get<Array<Record<string, unknown>>>(
    `/patients/${id}/timeline`,
  );
  return response.data;
}

export async function fetchPatientKnowledgeBundle(id: number) {
  const response = await api.get<PatientKnowledgeBundle>(
    `/patients/${id}/knowledge-bundle`,
  );
  return response.data;
}

export async function fetchMedications() {
  const response = await api.get<Medication[]>("/medications");
  return response.data;
}

export async function fetchActiveIngredients() {
  const response = await api.get<ActiveIngredient[]>(
    "/medication-catalog/active-ingredients",
  );
  return response.data;
}

export async function searchMedicationCatalog(query: string) {
  const response = await api.get<MedicationCatalogSearchResult[]>(
    "/medication-catalog/search",
    {
      params: { q: query },
    },
  );
  return response.data;
}

export async function fetchClinicalVocabulary(category?: string) {
  const response = await api.get<ClinicalVocabularyEntry[]>(
    "/clinical-vocabulary",
    {
      params: category ? { category } : undefined,
    },
  );
  return response.data;
}

export async function lookupAnvisaSource(query: string) {
  const response = await api.get<AnvisaLookupResponse>(
    "/medication-sources/anvisa/search",
    {
      params: { q: query },
    },
  );
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

export async function lookupMedicationKnowledge(
  payload: MedicationKnowledgeLookupPayload,
) {
  const response = await api.post<MedicationKnowledgeCurationItem>(
    "/medications/knowledge/lookup",
    payload,
  );
  return response.data;
}

export async function bulkImportMedicationKnowledge(
  payload: MedicationBulkImportPayload,
) {
  const response = await api.post<MedicationKnowledgeCurationItem[]>(
    "/medications/knowledge/bulk-import",
    payload,
  );
  return response.data;
}

export async function fetchMedicationCurationQueue(reviewStatus?: string) {
  const response = await api.get<MedicationKnowledgeCurationItem[]>(
    "/medications/knowledge/curation-queue",
    { params: reviewStatus ? { review_status: reviewStatus } : undefined },
  );
  return response.data;
}

export async function reviewMedicationKnowledge(
  itemId: number,
  payload: MedicationKnowledgeReviewPayload,
) {
  const response = await api.post<MedicationKnowledgeCurationItem>(
    `/medications/knowledge/curation-queue/${itemId}/review`,
    payload,
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
  const response = await api.post<PrescriptionCheckResult>(
    "/prescriptions/check",
    payload,
  );
  return response.data;
}

export async function explainPrescription(
  payload: PrescriptionExplanationPayload,
) {
  const response = await api.post<PrescriptionExplanationResult>(
    "/prescriptions/explain",
    payload,
  );
  return response.data;
}

export async function requestDecisionOverride(auditId: number, reason: string) {
  const response = await api.post<DecisionOverride>(
    `/prescriptions/${auditId}/overrides`,
    {
      reason,
    },
  );
  return response.data;
}

export async function reviewDecisionOverride(
  overrideId: number,
  payload: { decision: "approved" | "rejected"; note: string },
) {
  const response = await api.post<DecisionOverride>(
    `/prescriptions/overrides/${overrideId}/review`,
    payload,
  );
  return response.data;
}

export async function fetchAudit(filters: AuditFilters = {}) {
  const response = await api.get<AuditPage>("/audit", { params: filters });
  return response.data;
}

export async function fetchAuditTimeline(eventId: number) {
  const response = await api.get<DecisionTimelineItem[]>(
    `/audit/${eventId}/timeline`,
  );
  return response.data;
}

export async function fetchAuditEvidence(eventId: number) {
  const response = await api.get<DecisionEvidenceItem[]>(
    `/audit/${eventId}/evidence`,
  );
  return response.data;
}

export async function fetchReports(params?: {
  report_type?: string;
  target_type?: string;
}) {
  const response = await api.get<GeneratedReport[]>("/reports", { params });
  return response.data;
}

export async function fetchReport(id: number) {
  const response = await api.get<GeneratedReport>(`/reports/${id}`);
  return response.data;
}

export async function fetchPrescriptionReportPreview(
  auditId: number,
  anonymized = false,
) {
  const response = await api.get<ReportPreview>(
    `/reports/prescriptions/${auditId}/preview`,
    {
      params: { mode: anonymized ? "anonymized" : "complete_internal" },
    },
  );
  return response.data;
}

export async function fetchPrescriptionTimeline(auditId: number) {
  const response = await api.get<DecisionTimelineItem[]>(
    `/reports/prescriptions/${auditId}/timeline`,
  );
  return response.data;
}

export async function fetchPrescriptionEvidence(auditId: number) {
  const response = await api.get<DecisionEvidenceItem[]>(
    `/reports/prescriptions/${auditId}/evidence`,
  );
  return response.data;
}

export async function fetchProtocols(category?: string) {
  const response = await api.get<EmergencyProtocol[]>("/protocols", {
    params: category ? { category } : undefined,
  });
  return response.data;
}

export async function fetchProtocol(id: string) {
  const response = await api.get<EmergencyProtocol>(`/protocols/${id}`);
  return response.data;
}

export async function runProtocol(id: string, payload: ProtocolRunPayload) {
  const response = await api.post<ProtocolRunResult>(
    `/protocols/${id}/run`,
    payload,
  );
  return response.data;
}

export async function explainProtocol(
  id: string,
  payload: ProtocolExplainPayload,
) {
  const response = await api.post<ProtocolExplainResult>(
    `/protocols/${id}/explain`,
    payload,
  );
  return response.data;
}

export async function fetchProtocolEvidence(id: string) {
  const response = await api.get<ProtocolEvidence[]>(
    `/protocols/${id}/evidence`,
  );
  return response.data;
}

export async function fetchProtocolReport(id: string, runId?: number | null) {
  const response = await api.get<ProtocolReportPreview>(
    `/protocols/${id}/report`,
    {
      params: runId ? { run_id: runId } : undefined,
    },
  );
  return response.data;
}

export async function downloadPrescriptionTechnicalReport(
  auditId: number,
  anonymized = false,
) {
  return downloadFromApi(
    `/reports/prescriptions/${auditId}/pdf`,
    `prescripta-relatorio-tecnico-${auditId}.pdf`,
    { mode: anonymized ? "anonymized" : "complete_internal" },
  );
}

export async function downloadPatientGuidanceReport(auditId: number) {
  return downloadFromApi(
    `/reports/prescriptions/${auditId}/patient-guidance.pdf`,
    `prescripta-orientacoes-paciente-${auditId}.pdf`,
  );
}

export async function downloadReconciliationReport(
  importId: number,
  anonymized = false,
) {
  return downloadFromApi(
    `/reports/imports/${importId}/reconciliation.pdf`,
    `prescripta-reconciliacao-${importId}.pdf`,
    { anonymized },
  );
}

export async function downloadAuditReport(filters: AuditFilters = {}) {
  return downloadFromApi(
    "/reports/audit-events/pdf",
    "prescripta-auditoria.pdf",
    filters,
  );
}

export async function downloadProtocolReportPdf(
  id: string,
  runId?: number | null,
) {
  return downloadFromApi(
    `/protocols/${id}/report.pdf`,
    `prescripta-protocolo-${id}.pdf`,
    runId ? { run_id: runId } : undefined,
  );
}

export async function downloadProtocolRunReportPdf(runId: number) {
  return downloadFromApi(
    `/protocols/runs/${runId}/report.pdf`,
    `prescripta-protocolo-run-${runId}.pdf`,
  );
}

export async function exportPrescriptionJson(
  auditId: number,
  anonymized = false,
) {
  return downloadFromApi(
    `/exports/prescriptions/${auditId}.json`,
    `prescricao-${auditId}.json`,
    { anonymized },
  );
}

export async function exportPrescriptionCsv(
  auditId: number,
  anonymized = false,
) {
  return downloadFromApi(
    `/exports/prescriptions/${auditId}.csv`,
    `prescricao-${auditId}.csv`,
    { anonymized },
  );
}

export async function exportImportJson(importId: number, anonymized = false) {
  return downloadFromApi(
    `/exports/imports/${importId}.json`,
    `importacao-${importId}.json`,
    {
      anonymized,
    },
  );
}

export async function exportImportCsv(importId: number, anonymized = false) {
  return downloadFromApi(
    `/exports/imports/${importId}.csv`,
    `importacao-${importId}.csv`,
    {
      anonymized,
    },
  );
}

export async function exportAuditJson(filters: AuditFilters = {}) {
  return downloadFromApi(
    "/exports/audit-events.json",
    "audit-events.json",
    filters,
  );
}

export async function exportAuditCsv(filters: AuditFilters = {}) {
  return downloadFromApi(
    "/exports/audit-events.csv",
    "audit-events.csv",
    filters,
  );
}

export async function exportReportJson(reportId: number) {
  return downloadFromApi(
    `/exports/reports/${reportId}.json`,
    `relatorio-${reportId}.json`,
  );
}

export async function exportProtocolRunJson(id: string, runId: number) {
  return downloadFromApi(
    `/protocols/runs/${runId}/report.json`,
    `protocolo-${id}-${runId}.json`,
  );
}

export async function exportProtocolRunCsv(id: string, runId: number) {
  return downloadFromApi(
    `/protocols/runs/${runId}/report.csv`,
    `protocolo-${id}-${runId}.csv`,
  );
}

export async function fetchAIProviders() {
  const response = await api.get<AIProviderInfo[]>("/settings/ai/providers");
  return response.data;
}

export async function fetchCurrentAISettings() {
  const response = await api.get<AISettings>("/settings/ai/current");
  return response.data;
}

export async function fetchAIHealth() {
  const response = await api.get<AIHealth>("/settings/ai/health");
  return response.data;
}

export async function fetchAIModels(provider: AIProviderId, refresh = false) {
  const response = await api.get<AIModelListResponse>("/settings/ai/models", {
    params: { provider, refresh },
  });
  return response.data;
}

export async function saveAICredential(payload: AICredentialPayload) {
  const response = await api.post<AICredentialStatus>(
    "/settings/ai/credentials",
    payload,
  );
  return response.data;
}

export async function deleteAICredential(provider: AIProviderId) {
  const response = await api.delete<AICredentialStatus>(
    `/settings/ai/credentials/${provider}`,
  );
  return response.data;
}

export async function testAIConnection(payload: AIConnectionTestPayload) {
  const response = await api.post<AIConnectionTestResult>(
    "/settings/ai/test",
    payload,
  );
  return response.data;
}

export async function selectAIModel(payload: AIModelSelectPayload) {
  const response = await api.post<AISettings>(
    "/settings/ai/select-model",
    payload,
  );
  return response.data;
}

export async function fetchClinicalImports() {
  const response = await api.get<ClinicalImportBatch[]>(
    "/integrations/imports",
  );
  return response.data;
}

export async function fetchClinicalImport(id: number) {
  const response = await api.get<ClinicalImportBatch>(
    `/integrations/imports/${id}`,
  );
  return response.data;
}

export async function importClinicalJson(
  consent: ImportConsentPayload,
  payload: Record<string, unknown>,
) {
  const response = await api.post<ClinicalImportBatch>(
    "/integrations/json/import",
    {
      ...consent,
      payload,
    },
  );
  return response.data;
}

export async function importClinicalFhir(
  consent: ImportConsentPayload,
  bundle: Record<string, unknown>,
) {
  const response = await api.post<ClinicalImportBatch>(
    "/integrations/fhir/import-bundle",
    {
      ...consent,
      bundle,
    },
  );
  return response.data;
}

export async function importClinicalCsv(
  consent: ImportConsentPayload,
  csv_text: string,
) {
  const response = await api.post<ClinicalImportBatch>(
    "/integrations/csv/import",
    {
      ...consent,
      csv_text,
    },
  );
  return response.data;
}

export async function acceptClinicalImport(id: number) {
  const response = await api.post<ClinicalImportBatch>(
    `/integrations/imports/${id}/accept`,
  );
  return response.data;
}

export async function rejectClinicalImport(id: number, reason: string | null) {
  const response = await api.post<ClinicalImportBatch>(
    `/integrations/imports/${id}/reject`,
    {
      reason,
    },
  );
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
  const response = await api.post<CdsCheckResult>(
    "/cds/prescription-check",
    payload,
  );
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

export async function updateUserClinicalProfile(
  id: number,
  payload: UserClinicalProfilePayload,
) {
  const response = await api.patch<User>(
    `/users/${id}/clinical-profile`,
    payload,
  );
  return response.data;
}

export async function fetchResearchWorkspace() {
  const response = await api.get<ResearchWorkspace>("/research/workspace");
  return response.data;
}

export async function fetchResearchStudies() {
  const response = await api.get<ResearchStudy[]>("/research/studies");
  return response.data;
}

export async function createResearchStudy(payload: ResearchStudyPayload) {
  const response = await api.post<ResearchStudy>("/research/studies", payload);
  return response.data;
}

export async function fetchStudyWorkspace(studyId: string) {
  const response = await api.get<StudyWorkspace>(
    `/research/studies/${studyId}/workspace`,
  );
  return response.data;
}

export async function createStudyProtocolVersion(
  studyId: string,
  payload: Record<string, unknown>,
) {
  const response = await api.post<StudyProtocolVersion>(
    `/research/studies/${studyId}/protocol-versions`,
    payload,
  );
  return response.data;
}

export async function reviewStudyProtocolVersion(
  versionId: string,
  decision: "in_review" | "reviewed_demo" | "superseded" | "archived",
  note: string,
) {
  const response = await api.post<StudyProtocolVersion>(
    `/research/protocol-versions/${versionId}/review`,
    { decision, note },
  );
  return response.data;
}

export async function fetchConceptSets() {
  const response = await api.get<ConceptSet[]>("/research/concept-sets");
  return response.data;
}

export async function createConceptSet(payload: Record<string, unknown>) {
  const response = await api.post<ConceptSet>(
    "/research/concept-sets",
    payload,
  );
  return response.data;
}

export async function reviewConceptSetVersion(
  versionId: string,
  decision:
    | "terminology_matched"
    | "human_reviewed"
    | "approved_for_demo_study"
    | "rejected",
  note: string,
) {
  const response = await api.post<ConceptSetVersion>(
    `/research/concept-set-versions/${versionId}/review`,
    { decision, note },
  );
  return response.data;
}

export async function createCohortVersion(
  studyId: string,
  name: string,
  definition: CohortDefinition,
) {
  const response = await api.post<CohortVersion>(
    `/research/studies/${studyId}/cohorts`,
    {
      name,
      definition,
    },
  );
  return response.data;
}

export async function reviewCohortVersion(
  versionId: string,
  decision: "reviewed_demo" | "rejected" | "superseded",
  note: string,
) {
  const response = await api.post<CohortVersion>(
    `/research/cohort-versions/${versionId}/review`,
    { decision, note },
  );
  return response.data;
}

export async function createOutcomeDefinition(
  studyId: string,
  payload: Record<string, unknown>,
) {
  const response = await api.post<OutcomeDefinition>(
    `/research/studies/${studyId}/outcomes`,
    payload,
  );
  return response.data;
}

export async function reviewOutcomeDefinition(
  outcomeId: string,
  decision: "reviewed_demo" | "rejected" | "superseded",
  note: string,
) {
  const response = await api.post<OutcomeDefinition>(
    `/research/outcomes/${outcomeId}/review`,
    { decision, note },
  );
  return response.data;
}

export async function executeCohortVersion(
  versionId: string,
  dataSnapshotMarker: string,
) {
  const response = await api.post<CohortRun>(
    `/research/cohort-versions/${versionId}/runs`,
    { data_snapshot_marker: dataSnapshotMarker },
  );
  return response.data;
}

export async function runDataQuality(studyId: string, cohortRunId: string) {
  const response = await api.post<DataQualityRun>("/data-quality/runs", {
    study_id: studyId,
    cohort_run_id: cohortRunId,
  });
  return response.data;
}

export async function fetchTerminologySources() {
  const response = await api.get<TerminologySource[]>("/terminology/sources");
  return response.data;
}

export async function fetchTerminologyReleases(sourceId?: string) {
  const response = await api.get<TerminologyRelease[]>("/terminology/releases", {
    params: sourceId ? { source_id: sourceId } : undefined,
  });
  return response.data;
}

export async function searchTerminologyConcepts(params: {
  query?: string;
  release_id?: string;
  domain?: string;
  standard_status?: string;
  active_only?: boolean;
}) {
  const response = await api.get<TerminologyConceptPage>("/terminology/concepts", { params });
  return response.data;
}

export async function fetchTerminologyMappings(mappingStatus?: string) {
  const response = await api.get<TerminologyMapping[]>("/terminology/mappings", {
    params: mappingStatus ? { mapping_status: mappingStatus } : undefined,
  });
  return response.data;
}

export async function reviewTerminologyMapping(
  mappingId: string,
  decision: "approved_for_demo" | "rejected" | "deprecated",
  note: string,
) {
  const response = await api.post<TerminologyMapping>(
    `/terminology/mappings/${mappingId}/review`,
    { decision, note },
  );
  return response.data;
}

export async function fetchOmopCompatibility() {
  const response = await api.get<OmopCompatibility>("/omop/compatibility");
  return response.data;
}

export async function fetchOmopRuns() {
  const response = await api.get<OmopEtlRun[]>("/omop/runs");
  return response.data;
}

export async function executeOmopAdapter(
  mode: "preview" | "exports",
  payload: { study_id: string; cohort_run_id: string; terminology_release_ids: string[] },
) {
  const response = await api.post<OmopEtlRun>(`/omop/${mode}`, payload);
  return response.data;
}

export async function fetchDataQualityFindings() {
  const response = await api.get<DataQualityFinding[]>(
    "/data-quality/findings",
  );
  return response.data;
}

export async function acknowledgeDataQualityFinding(
  findingId: string,
  resolution: string,
) {
  const response = await api.post<DataQualityFinding>(
    `/data-quality/findings/${findingId}/acknowledge`,
    { resolution },
  );
  return response.data;
}

export async function createAnalysisPlan(
  studyId: string,
  payload: AnalysisPlanPayload,
) {
  const response = await api.post<AnalysisPlan>(
    `/research/studies/${studyId}/analysis-plans`,
    payload,
  );
  return response.data;
}

export async function reviewAnalysisPlan(planId: string, note: string) {
  const response = await api.post<AnalysisPlan>(
    `/research/analysis-plans/${planId}/review`,
    { decision: "reviewed_demo", note },
  );
  return response.data;
}

export async function executeAnalysisPlan(planId: string) {
  const response = await api.post<AnalysisRun>(
    `/research/analysis-plans/${planId}/runs`,
  );
  return response.data;
}

export async function exportResearchPackage(analysisRunId: string) {
  const response = await api.post<ResearchPackage>(
    `/research/analysis-runs/${analysisRunId}/package`,
  );
  return response.data;
}

export async function fetchComparisons(studyId: string) {
  const response = await api.get<ComparativeAnalysis[]>(
    `/research/studies/${studyId}/comparisons`,
  );
  return response.data;
}

export async function executeComparison(
  studyId: string,
  payload: Record<string, unknown>,
) {
  const response = await api.post<ComparativeAnalysis>(
    `/research/studies/${studyId}/comparisons`,
    payload,
  );
  return response.data;
}

export async function createMedicationSafetyResearchDraft(
  studyId: string,
  payload: Record<string, unknown>,
) {
  const response = await api.post(
    `/research/studies/${studyId}/medication-safety-drafts`,
    payload,
  );
  return response.data as Record<string, unknown>;
}

export async function exportComparisonPackage(comparisonId: string) {
  const response = await api.post<ResearchPackage>(
    `/research/comparisons/${comparisonId}/package`,
  );
  return response.data;
}

export async function previewResearchQuery(payload: Record<string, unknown>) {
  const response = await api.post<ResearchQueryPreview>(
    "/research/query-assistant/previews",
    payload,
  );
  return response.data;
}

export async function executeResearchQuery(previewId: string) {
  const response = await api.post<ResearchQueryPreview>(
    `/research/query-assistant/previews/${previewId}/execute`,
    { confirm_preview: true },
  );
  return response.data;
}

export async function fetchPatientJourney(studyId: string, patientId: number) {
  const response = await api.get<PatientJourney>(
    `/research/studies/${studyId}/patient-journey/${patientId}`,
  );
  return response.data;
}

export async function executeAITask(payload: Record<string, unknown>) {
  const response = await api.post<AIInteraction>("/ai/tasks", payload);
  return response.data;
}

export async function fetchEvidenceSources() {
  const response = await api.get<EvidenceSource[]>("/evidence/sources");
  return response.data;
}

export async function createEvidenceSource(payload: Record<string, unknown>) {
  const response = await api.post<EvidenceSource>("/evidence/sources", payload);
  return response.data;
}

export async function createEvidenceSearchPlan(payload: Record<string, unknown>) {
  const response = await api.post<EvidenceSearchPlan>("/evidence/search-plans", payload);
  return response.data;
}

export async function executeEvidenceSearchPlan(planId: string) {
  const response = await api.post<EvidenceSearchPlan>(
    `/evidence/search-plans/${planId}/execute`,
    { confirm_metadata_retrieval: true },
  );
  return response.data;
}

export async function createResearchAgent(payload: Record<string, unknown>) {
  const response = await api.post<ResearchAgentRun>("/research/agents", payload);
  return response.data;
}

export async function advanceResearchAgent(
  runId: string,
  payload: Record<string, unknown>,
) {
  const response = await api.post<ResearchAgentRun>(
    `/research/agents/${runId}/steps`,
    payload,
  );
  return response.data;
}

export async function createEvidenceExtraction(payload: Record<string, unknown>) {
  const response = await api.post<EvidenceExtraction>(
    "/evidence/extractions",
    payload,
  );
  return response.data;
}

export async function fetchEvidenceLinks() {
  const response = await api.get<EvidenceLink[]>("/evidence/links");
  return response.data;
}

export async function createEvidenceLink(payload: Record<string, unknown>) {
  const response = await api.post<EvidenceLink>("/evidence/links", payload);
  return response.data;
}

export async function fetchPharmacyInterventions() {
  const response = await api.get<PharmacyIntervention[]>(
    "/pharmacy/interventions",
  );
  return response.data;
}

export async function createPharmacyIntervention(
  payload: PharmacyInterventionPayload,
) {
  const response = await api.post<PharmacyIntervention>(
    "/pharmacy/interventions",
    payload,
  );
  return response.data;
}

export async function decidePharmacyIntervention(
  interventionId: number,
  decision: "accepted" | "rejected",
  reason: string,
  expectedVersion: number,
) {
  const response = await api.post<PharmacyIntervention>(
    `/pharmacy/interventions/${interventionId}/decision`,
    { decision, reason, expected_version: expectedVersion },
  );
  return response.data;
}

export async function resolvePharmacyIntervention(
  interventionId: number,
  resolution: string,
  expectedVersion: number,
) {
  const response = await api.post<PharmacyIntervention>(
    `/pharmacy/interventions/${interventionId}/resolve`,
    { resolution, expected_version: expectedVersion },
  );
  return response.data;
}

async function downloadFromApi(
  url: string,
  fallbackFilename: string,
  params?: Record<string, unknown>,
) {
  const response = await api.get<Blob>(url, { params, responseType: "blob" });
  const disposition = response.headers["content-disposition"];
  const filename = filenameFromDisposition(disposition) ?? fallbackFilename;
  const contentType = response.headers["content-type"];
  const blob = new Blob([response.data], {
    type:
      typeof contentType === "string"
        ? contentType
        : "application/octet-stream",
  });
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

function filenameFromDisposition(disposition: unknown) {
  if (typeof disposition !== "string") {
    return null;
  }
  const match = disposition.match(/filename="?([^";]+)"?/i);
  return match?.[1] ?? null;
}
