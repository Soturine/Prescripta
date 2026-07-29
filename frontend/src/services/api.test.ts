import { beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "./api";

const marker = { ok: true };
const payload = {} as never;

describe("cliente HTTP", () => {
  beforeEach(() => {
    vi.spyOn(client.api, "get").mockResolvedValue({ data: marker, headers: {} } as never);
    vi.spyOn(client.api, "post").mockResolvedValue({ data: marker, headers: {} } as never);
    vi.spyOn(client.api, "put").mockResolvedValue({ data: marker, headers: {} } as never);
    vi.spyOn(client.api, "patch").mockResolvedValue({ data: marker, headers: {} } as never);
    vi.spyOn(client.api, "delete").mockResolvedValue({ data: marker, headers: {} } as never);
  });

  it("mantém sessão em cookie e limpa bearer legado", async () => {
    client.setAuthToken("token-demo");
    expect(client.api.defaults.headers.common.Authorization).toBe("Bearer token-demo");
    client.clearAuthToken();
    expect(client.api.defaults.headers.common.Authorization).toBeUndefined();
    await client.logoutSession();
    expect(client.api.post).toHaveBeenCalledWith("/auth/logout");
  });

  it("mapeia autenticação, dashboard, pacientes e acesso clínico", async () => {
    const calls = await Promise.all([
      client.login(payload), client.fetchMe(), client.fetchDashboard(), client.fetchApiHealth(),
      client.fetchPatients(), client.fetchPatient(7), client.fetchPatientPsychologicalContext(7),
      client.updatePatientPsychologicalContext(7, payload), client.fetchPatientAccessGrants(7),
      client.createPatientAccessGrant(7, payload), client.revokePatientAccessGrant(9, "motivo auditável"),
      client.fetchPatientCareTeam(7), client.fetchPatientClinicalContext(7), client.createPatient(payload),
      client.updatePatient(7, payload), client.fetchPatientIdentifiers(7), client.createPatientIdentifier(7, payload),
      client.quickTriagePatient(7, payload), client.fetchPatientFunctionalProfile(7),
      client.updatePatientFunctionalProfile(7, payload), client.fetchPatientDocuments(7),
      client.createPatientDocument(7, payload), client.extractPatientDocument(7, 3),
      client.reviewPatientDocumentExtraction(7, 4, payload), client.fetchPatientTimeline(7),
      client.fetchPatientKnowledgeBundle(7),
    ]);
    expect(calls.every((value) => Object.is(value, marker))).toBe(true);
    expect(client.api.get).toHaveBeenCalledWith("/patients/7/psychological-context", { params: { purpose: "treatment" } });
    expect(client.api.post).toHaveBeenCalledWith("/access/grants/9/revoke", { reason: "motivo auditável" });
  });

  it("mapeia catálogo, curadoria, dose e decisão", async () => {
    const calls = await Promise.all([
      client.fetchMedications(), client.fetchActiveIngredients(), client.searchMedicationCatalog("dipirona"),
      client.fetchClinicalVocabulary(), client.fetchClinicalVocabulary("route"), client.lookupAnvisaSource("dipirona"),
      client.createMedication(payload), client.updateMedication(2, payload), client.fetchAdverseEffectTaxonomy(),
      client.lookupMedicationKnowledge(payload), client.bulkImportMedicationKnowledge(payload),
      client.fetchMedicationCurationQueue(), client.fetchMedicationCurationQueue("pending_review"),
      client.reviewMedicationKnowledge(4, payload), client.fetchMedicationCounselingSummary(2),
      client.generateMedicationCounselingSummary(2), client.generateMedicationCounselingSummary(2, payload),
      client.reviewMedicationCounselingSummary(2, payload), client.checkPrescription(payload),
      client.explainPrescription(payload), client.requestDecisionOverride(21, "justificativa"),
      client.reviewDecisionOverride(5, { decision: "approved", note: "segunda revisão" }),
    ]);
    expect(calls.every((value) => Object.is(value, marker))).toBe(true);
    expect(client.api.get).toHaveBeenCalledWith("/clinical-vocabulary", { params: undefined });
    expect(client.api.get).toHaveBeenCalledWith("/clinical-vocabulary", { params: { category: "route" } });
  });

  it("mapeia auditoria, relatórios e protocolos com parâmetros opcionais", async () => {
    const calls = await Promise.all([
      client.fetchAudit(), client.fetchAudit({ action: "prescription.check" }), client.fetchAuditTimeline(3),
      client.fetchAuditEvidence(3), client.fetchReports(), client.fetchReports({ report_type: "technical" }),
      client.fetchReport(4), client.fetchPrescriptionReportPreview(5), client.fetchPrescriptionReportPreview(5, true),
      client.fetchPrescriptionTimeline(5), client.fetchPrescriptionEvidence(5), client.fetchProtocols(),
      client.fetchProtocols("emergency"), client.fetchProtocol("demo"), client.runProtocol("demo", payload),
      client.explainProtocol("demo", payload), client.fetchProtocolEvidence("demo"),
      client.fetchProtocolReport("demo"), client.fetchProtocolReport("demo", 6),
    ]);
    expect(calls.every((value) => Object.is(value, marker))).toBe(true);
    expect(client.api.get).toHaveBeenCalledWith("/protocols", { params: { category: "emergency" } });
    expect(client.api.get).toHaveBeenCalledWith("/reports/prescriptions/5/preview", { params: { mode: "anonymized" } });
  });

  it("mapeia IA, integrações, CDS e perfis profissionais", async () => {
    const consent = { source_system: "demo" } as never;
    const calls = await Promise.all([
      client.fetchAIProviders(), client.fetchCurrentAISettings(), client.fetchAIHealth(),
      client.fetchAIModels("openai"), client.fetchAIModels("gemini", true), client.saveAICredential(payload),
      client.deleteAICredential("ollama"), client.testAIConnection(payload), client.selectAIModel(payload),
      client.fetchClinicalImports(), client.fetchClinicalImport(8), client.importClinicalJson(consent, { demo: true }),
      client.importClinicalFhir(consent, { resourceType: "Bundle" }), client.importClinicalCsv(consent, "type,value"),
      client.acceptClinicalImport(8), client.rejectClinicalImport(8, null), client.fetchClinicalReconciliation(8),
      client.acceptClinicalReconciliationItem(8, "item/a", "aceito"),
      client.rejectClinicalReconciliationItem(8, "item/b", "rejeitado"),
      client.acceptClinicalReconciliationSafeItems(8), client.checkCdsPrescription(payload), client.fetchUsers(),
      client.createUser(payload), client.updateUserStatus(2, false), client.updateUserRole(2, "farmaceutico"),
      client.updateUserClinicalProfile(2, payload),
    ]);
    expect(calls.every((value) => Object.is(value, marker))).toBe(true);
    expect(client.api.post).toHaveBeenCalledWith("/integrations/imports/8/reconciliation/items/item%2Fa/accept", { justification: "aceito" });
    expect(client.api.patch).toHaveBeenCalledWith("/users/2/role", { role: "farmaceutico" });
  });

  it("baixa relatórios usando filename seguro ou fallback", async () => {
    const createObjectURL = vi.fn(() => "blob:demo");
    const revokeObjectURL = vi.fn();
    Object.defineProperty(URL, "createObjectURL", { configurable: true, value: createObjectURL });
    Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: revokeObjectURL });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    vi.mocked(client.api.get).mockResolvedValue({
      data: new Uint8Array([1, 2]),
      headers: { "content-disposition": 'attachment; filename="relatorio-seguro.pdf"', "content-type": "application/pdf" },
    } as never);

    await Promise.all([
      client.downloadPrescriptionTechnicalReport(1), client.downloadPrescriptionTechnicalReport(1, true),
      client.downloadPatientGuidanceReport(1), client.downloadReconciliationReport(2),
      client.downloadReconciliationReport(2, true), client.downloadAuditReport(),
      client.downloadProtocolReportPdf("demo"), client.downloadProtocolReportPdf("demo", 3),
      client.downloadProtocolRunReportPdf(3), client.exportPrescriptionJson(1),
      client.exportPrescriptionCsv(1, true), client.exportImportJson(2), client.exportImportCsv(2, true),
      client.exportAuditJson(), client.exportAuditCsv({ user: "2" }), client.exportReportJson(4),
      client.exportProtocolRunJson("demo", 3), client.exportProtocolRunCsv("demo", 3),
    ]);
    expect(click).toHaveBeenCalledTimes(18);
    expect(createObjectURL).toHaveBeenCalledTimes(18);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:demo");

    vi.mocked(client.api.get).mockResolvedValue({ data: new Uint8Array(), headers: {} } as never);
    await client.exportReportJson(99);
    expect(click).toHaveBeenCalledTimes(19);
  });
});
