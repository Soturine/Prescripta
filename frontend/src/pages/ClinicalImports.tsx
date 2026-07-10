import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Check,
  DatabaseZap,
  Download,
  FileJson,
  FlaskConical,
  ShieldCheck,
  Upload,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";

import LoadingState from "../components/LoadingState";
import RiskBadge from "../components/RiskBadge";
import { useAuth } from "../context/AuthContext";
import {
  acceptClinicalImport,
  acceptClinicalReconciliationItem,
  acceptClinicalReconciliationSafeItems,
  checkCdsPrescription,
  downloadReconciliationReport,
  fetchClinicalImports,
  fetchClinicalReconciliation,
  importClinicalCsv,
  importClinicalFhir,
  importClinicalJson,
  exportImportCsv,
  exportImportJson,
  rejectClinicalImport,
  rejectClinicalReconciliationItem,
} from "../services/api";
import type {
  ClinicalImportBatch,
  ClinicalReconciliation,
  ClinicalReconciliationItem,
  ImportConsentPayload,
} from "../types/integration";
import { formatDateTime } from "../utils/formatters";

const jsonDemo = JSON.stringify(
  {
    patient: {
      name: "Paciente Demo",
      birth_date: "1990-01-01",
      identifiers: [{ type: "external_system_id", value: "DEMO-EXT-123" }],
    },
    conditions: ["problema nos rins"],
    current_medications: ["Novalgina"],
  },
  null,
  2,
);

const fhirScenarios = {
  medication: {
    label: "Paciente + medicamento",
    bundle: {
    resourceType: "Bundle",
    entry: [
      {
        resource: {
          resourceType: "Patient",
          name: [{ given: ["Ana"], family: "FHIR" }],
          birthDate: "1990-01-01",
        },
      },
      {
        resource: {
          resourceType: "MedicationStatement",
          medicationCodeableConcept: { text: "metamizol" },
        },
      },
    ],
  },
  },
  renalConflict: {
    label: "Paciente + condição renal",
    bundle: {
      resourceType: "Bundle",
      entry: [
        {
          resource: {
            resourceType: "Patient",
            name: [{ given: ["Carlos"], family: "FHIR" }],
            birthDate: "1950-03-10",
          },
        },
        {
          resource: {
            resourceType: "Condition",
            code: { text: "Doença renal crônica" },
          },
        },
      ],
    },
  },
  allergyObservation: {
    label: "Alergia + observação",
    bundle: {
      resourceType: "Bundle",
      entry: [
        {
          resource: {
            resourceType: "AllergyIntolerance",
            code: { text: "dipirona" },
            criticality: "high",
          },
        },
        {
          resource: {
            resourceType: "Observation",
            code: { text: "creatinina" },
            valueString: "resultado externo pendente de revisão",
          },
        },
      ],
    },
  },
} satisfies Record<string, { label: string; bundle: Record<string, unknown> }>;

const fhirDemo = JSON.stringify(fhirScenarios.medication.bundle, null, 2);

const csvDemo = "record_type,value\nmedication,Novalgina\ncondition,renal\n";

export default function ClinicalImports() {
  const { canAccess } = useAuth();
  const canReview = canAccess(["admin", "medico"]);
  const canExport = canAccess(["admin", "medico", "auditor"]);
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mode, setMode] = useState<"json" | "fhir" | "csv">("json");
  const [sourceSystem, setSourceSystem] = useState("mock_hospital");
  const [purpose, setPurpose] = useState("Importação clínica assistida");
  const [authorizedBy, setAuthorizedBy] = useState("Paciente/representante demo");
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [body, setBody] = useState(jsonDemo);
  const [fhirScenario, setFhirScenario] = useState<keyof typeof fhirScenarios>("medication");
  const [rejectReason, setRejectReason] = useState("Rejeitado em revisão humana.");
  const [itemJustification, setItemJustification] = useState("Revisão granular registrada.");
  const { data: imports = [], isLoading } = useQuery({
    queryKey: ["clinical-imports"],
    queryFn: fetchClinicalImports,
  });
  const selected = useMemo(
    () => imports.find((item) => item.id === selectedId) ?? imports[0],
    [imports, selectedId],
  );
  const { data: reconciliation } = useQuery({
    queryKey: ["clinical-reconciliation", selected?.id],
    queryFn: () => fetchClinicalReconciliation(Number(selected?.id)),
    enabled: Boolean(selected),
  });
  const importMutation = useMutation({
    mutationFn: async () => {
      const consent: ImportConsentPayload = {
        consent_confirmed: consentConfirmed,
        purpose,
        authorized_by: authorizedBy,
        source_system: sourceSystem,
        patient_id: null,
      };
      if (mode === "csv") {
        return importClinicalCsv(consent, body);
      }
      const parsed = JSON.parse(body) as Record<string, unknown>;
      return mode === "fhir"
        ? importClinicalFhir(consent, parsed)
        : importClinicalJson(consent, parsed);
    },
    onSuccess: async (batch) => {
      setSelectedId(batch.id);
      await queryClient.invalidateQueries({ queryKey: ["clinical-imports"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const acceptMutation = useMutation({
    mutationFn: acceptClinicalImport,
    onSuccess: async (batch) => {
      setSelectedId(batch.id);
      await queryClient.invalidateQueries({ queryKey: ["clinical-imports"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const rejectMutation = useMutation({
    mutationFn: (id: number) => rejectClinicalImport(id, rejectReason),
    onSuccess: async (batch) => {
      setSelectedId(batch.id);
      await queryClient.invalidateQueries({ queryKey: ["clinical-imports"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const acceptSafeMutation = useMutation({
    mutationFn: acceptClinicalReconciliationSafeItems,
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: ["clinical-reconciliation", result.batch_id] });
      await queryClient.invalidateQueries({ queryKey: ["clinical-imports"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const acceptItemMutation = useMutation({
    mutationFn: (item: ClinicalReconciliationItem) =>
      acceptClinicalReconciliationItem(
        Number(selected?.id),
        item.item_id,
        itemJustification,
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["clinical-reconciliation", selected?.id] });
      await queryClient.invalidateQueries({ queryKey: ["clinical-imports"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const rejectItemMutation = useMutation({
    mutationFn: (item: ClinicalReconciliationItem) =>
      rejectClinicalReconciliationItem(
        Number(selected?.id),
        item.item_id,
        itemJustification,
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["clinical-reconciliation", selected?.id] });
      await queryClient.invalidateQueries({ queryKey: ["clinical-imports"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const cdsMutation = useMutation({
    mutationFn: () =>
      checkCdsPrescription({
        patient: {
          name: "Paciente CDS Demo",
          age: 30,
          weight_kg: 70,
          reproductive_gynecologic_factors: ["uso_anticoncepcional_hormonal"],
        },
        medication_request: {
          active_ingredient: "rifampicina",
          dose_mg: 300,
          frequency_per_day: 1,
          route: "oral",
          duration_days: 5,
          max_daily_dose_mg: 600,
        },
        allergies: [],
        conditions: [],
        current_medications: [],
        observations: [],
        persist: false,
      }),
  });
  const reconciliationReportMutation = useMutation({
    mutationFn: (id: number) => downloadReconciliationReport(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["reports"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const exportImportJsonMutation = useMutation({
    mutationFn: (id: number) => exportImportJson(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const exportImportCsvMutation = useMutation({
    mutationFn: (id: number) => exportImportCsv(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });

  function changeMode(nextMode: "json" | "fhir" | "csv") {
    setMode(nextMode);
    setBody(nextMode === "json" ? jsonDemo : nextMode === "fhir" ? fhirDemo : csvDemo);
  }

  function changeFhirScenario(nextScenario: keyof typeof fhirScenarios) {
    setFhirScenario(nextScenario);
    setBody(JSON.stringify(fhirScenarios[nextScenario].bundle, null, 2));
  }

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Importações Clínicas</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Importação clínica assistida com consentimento, auditoria e revisão humana obrigatória.
        </p>
      </header>

      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm font-medium leading-6 text-amber-900">
        Este recurso usa dados de exemplo. Integrações reais exigem autorização, contrato,
        segurança, governança e conformidade com LGPD.
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <ShieldCheck aria-hidden="true" className="h-5 w-5 text-ocean" />
            <h2 className="text-lg font-bold text-ink">Nova importação</h2>
          </div>
          <div className="mt-4 grid gap-3">
            <div className="flex rounded-lg border border-slate-200 bg-slate-50 p-1">
              {(["json", "fhir", "csv"] as const).map((item) => (
                <button
                  className={[
                    "flex-1 rounded-md px-3 py-2 text-sm font-semibold transition",
                    mode === item ? "bg-white text-ocean shadow-sm" : "text-slate-600",
                  ].join(" ")}
                  key={item}
                  onClick={() => changeMode(item)}
                  type="button"
                >
                  {item.toUpperCase()}
                </button>
              ))}
            </div>
            <label className="grid gap-1.5">
              <span className="label">Origem dos dados</span>
              <input className="field" value={sourceSystem} onChange={(event) => setSourceSystem(event.target.value)} />
            </label>
            <label className="grid gap-1.5">
              <span className="label">Finalidade</span>
              <input className="field" value={purpose} onChange={(event) => setPurpose(event.target.value)} />
            </label>
            <label className="grid gap-1.5">
              <span className="label">Autorizado por</span>
              <input className="field" value={authorizedBy} onChange={(event) => setAuthorizedBy(event.target.value)} />
            </label>
            <label className="flex items-start gap-3 rounded-lg border border-slate-200 p-3 text-sm font-semibold text-slate-700">
              <input
                checked={consentConfirmed}
                className="mt-1 h-4 w-4 accent-ocean"
                onChange={(event) => setConsentConfirmed(event.target.checked)}
                type="checkbox"
              />
              Confirmo que há autorização do paciente ou base legal aplicável para importar estes dados.
            </label>
            {mode === "fhir" ? (
              <label className="grid gap-1.5">
                <span className="label">Cenário FHIR fictício</span>
                <select
                  className="field"
                  value={fhirScenario}
                  onChange={(event) =>
                    changeFhirScenario(event.target.value as keyof typeof fhirScenarios)
                  }
                >
                  {Object.entries(fhirScenarios).map(([key, scenario]) => (
                    <option key={key} value={key}>
                      {scenario.label}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <label className="grid gap-1.5">
              <span className="label">{mode === "csv" ? "CSV" : "JSON"}</span>
              <textarea
                className="field min-h-72 resize-y font-mono text-xs"
                value={body}
                onChange={(event) => setBody(event.target.value)}
              />
            </label>
            <button
              className="btn-primary w-fit"
              disabled={importMutation.isPending}
              onClick={() => importMutation.mutate()}
              title="Importar"
              type="button"
            >
              <Upload aria-hidden="true" className="h-4 w-4" />
              {importMutation.isPending ? "Importando..." : "Importar"}
            </button>
            {importMutation.isError ? (
              <p className="text-sm font-semibold text-danger">
                Não foi possível importar. Revise consentimento e payload.
              </p>
            ) : null}
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <DatabaseZap aria-hidden="true" className="h-5 w-5 text-ocean" />
            <h2 className="text-lg font-bold text-ink">Lotes importados</h2>
          </div>
          {isLoading ? <LoadingState label="Carregando importacoes" /> : null}
          <div className="mt-4 grid gap-3">
            {imports.map((item) => (
              <button
                className={[
                  "rounded-lg border p-4 text-left transition",
                  selected?.id === item.id
                    ? "border-ocean bg-cyan-50"
                    : "border-slate-200 hover:bg-slate-50",
                ].join(" ")}
                key={item.id}
                onClick={() => setSelectedId(item.id)}
                type="button"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="font-bold text-ink">#{item.id} {item.source_system}</span>
                  <StatusPill status={item.status} />
                </div>
                <p className="mt-1 text-sm text-slate-600">
                  {item.source_type} - {formatDateTime(item.imported_at)}
                </p>
              </button>
            ))}
            {!imports.length && !isLoading ? (
              <p className="text-sm text-slate-500">Nenhuma importação registrada.</p>
            ) : null}
          </div>
        </div>
      </section>

      {selected ? (
        <ImportDetail
          batch={selected}
          canExport={canExport}
          canReview={canReview}
          isExporting={exportImportJsonMutation.isPending || exportImportCsvMutation.isPending}
          isAccepting={acceptMutation.isPending}
          isRejecting={rejectMutation.isPending}
          isGeneratingReport={reconciliationReportMutation.isPending}
          onAccept={() => acceptMutation.mutate(selected.id)}
          onReject={() => rejectMutation.mutate(selected.id)}
          onAcceptItem={(item) => acceptItemMutation.mutate(item)}
          onAcceptSafe={() => acceptSafeMutation.mutate(selected.id)}
          onDownloadReport={() => reconciliationReportMutation.mutate(selected.id)}
          onExportCsv={() => exportImportCsvMutation.mutate(selected.id)}
          onExportJson={() => exportImportJsonMutation.mutate(selected.id)}
          onRejectItem={(item) => rejectItemMutation.mutate(item)}
          itemJustification={itemJustification}
          reconciliation={reconciliation ?? null}
          rejectReason={rejectReason}
          setItemJustification={setItemJustification}
          setRejectReason={setRejectReason}
        />
      ) : null}

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <FlaskConical aria-hidden="true" className="h-5 w-5 text-ocean" />
          <h2 className="text-lg font-bold text-ink">Integração externa / CDS API</h2>
        </div>
        <div className="mt-4 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
            <p className="font-mono text-sm font-semibold text-ink">
              POST /api/cds/prescription-check
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Endpoint educacional com persist=false, regras determinísticas e cards estilo CDS.
            </p>
            <button
              className="btn-secondary mt-4"
              disabled={cdsMutation.isPending}
              onClick={() => cdsMutation.mutate()}
              title="Testar CDS"
              type="button"
            >
              <FileJson aria-hidden="true" className="h-4 w-4" />
              {cdsMutation.isPending ? "Testando..." : "Testar CDS demo"}
            </button>
          </div>
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
            {cdsMutation.data ? (
              <div className="grid gap-3">
                <div className="flex flex-wrap gap-2">
                  <RiskBadge status={cdsMutation.data.status as never} />
                  <RiskBadge level={cdsMutation.data.risk_level as never} />
                  <span className="rounded-lg bg-white px-3 py-2 text-xs font-semibold text-slate-600">
                    {cdsMutation.data.audit_id}
                  </span>
                </div>
                {cdsMutation.data.cards.map((card) => (
                  <div className="rounded-lg bg-white p-3 text-sm" key={card.summary}>
                    <p className="font-bold text-ink">{card.summary}</p>
                    <p className="mt-1 text-slate-600">{card.detail}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Resultado CDS aparece aqui após teste.</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function ImportDetail({
  batch,
  canExport,
  canReview,
  itemJustification,
  isExporting,
  isAccepting,
  isRejecting,
  isGeneratingReport,
  onAccept,
  onAcceptItem,
  onAcceptSafe,
  onDownloadReport,
  onExportCsv,
  onExportJson,
  onReject,
  onRejectItem,
  reconciliation,
  rejectReason,
  setItemJustification,
  setRejectReason,
}: {
  batch: ClinicalImportBatch;
  canExport: boolean;
  canReview: boolean;
  itemJustification: string;
  isExporting: boolean;
  isAccepting: boolean;
  isRejecting: boolean;
  isGeneratingReport: boolean;
  onAccept: () => void;
  onAcceptItem: (item: ClinicalReconciliationItem) => void;
  onAcceptSafe: () => void;
  onDownloadReport: () => void;
  onExportCsv: () => void;
  onExportJson: () => void;
  onReject: () => void;
  onRejectItem: (item: ClinicalReconciliationItem) => void;
  reconciliation: ClinicalReconciliation | null;
  rejectReason: string;
  setItemJustification: (value: string) => void;
  setRejectReason: (value: string) => void;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-bold text-ink">Detalhes da importação #{batch.id}</h2>
          <p className="mt-1 text-sm text-slate-600">
            Consentimento #{batch.consent_id ?? "-"} - {batch.records.length} registros
          </p>
        </div>
        <StatusPill status={batch.status} />
      </div>
      {canExport ? (
        <div className="mt-4 flex flex-wrap gap-3 border-t border-slate-100 pt-4">
          <button
            className="btn-secondary"
            disabled={isGeneratingReport}
            onClick={onDownloadReport}
            type="button"
          >
            <FileJson aria-hidden="true" className="h-4 w-4" />
            {isGeneratingReport ? "Gerando..." : "Baixar relatório de reconciliação"}
          </button>
          <button className="btn-secondary" disabled={isExporting} onClick={onExportJson} type="button">
            <FileJson aria-hidden="true" className="h-4 w-4" />
            Exportar JSON
          </button>
          <button className="btn-secondary" disabled={isExporting} onClick={onExportCsv} type="button">
            <Download aria-hidden="true" className="h-4 w-4" />
            Exportar CSV
          </button>
        </div>
      ) : null}
      {batch.errors.length ? (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-700">
          {batch.errors.join(", ")}
        </div>
      ) : null}
      <div className="mt-4 grid gap-3">
        {batch.records.map((record) => (
          <article className="rounded-lg border border-slate-100 bg-slate-50 p-4" key={record.id}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-sm font-bold text-ink">{record.record_type}</h3>
              <span className="rounded-lg bg-white px-3 py-1 text-xs font-semibold text-slate-600">
                confiança {Math.round(record.confidence * 100)}%
              </span>
            </div>
            <pre className="mt-3 max-h-52 overflow-auto rounded-lg bg-white p-3 text-xs text-slate-700">
              {JSON.stringify(record.mapped_payload, null, 2)}
            </pre>
          </article>
        ))}
      </div>
      {reconciliation ? (
        <ReconciliationPanel
          canReview={canReview && batch.status === "pending_review"}
          onAcceptItem={onAcceptItem}
          onAcceptSafe={onAcceptSafe}
          onRejectItem={onRejectItem}
          itemJustification={itemJustification}
          reconciliation={reconciliation}
          setItemJustification={setItemJustification}
        />
      ) : null}
      {canReview && batch.status === "pending_review" ? (
        <div className="mt-4 flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center">
          <button
            className="btn-primary"
            disabled={isAccepting}
            onClick={onAccept}
            title="Aceitar importação"
            type="button"
          >
            <Check aria-hidden="true" className="h-4 w-4" />
            Aceitar
          </button>
          <input
            className="field sm:max-w-md"
            value={rejectReason}
            onChange={(event) => setRejectReason(event.target.value)}
          />
          <button
            className="btn-secondary"
            disabled={isRejecting}
            onClick={onReject}
            title="Rejeitar importação"
            type="button"
          >
            <X aria-hidden="true" className="h-4 w-4" />
            Rejeitar
          </button>
        </div>
      ) : null}
    </section>
  );
}

function ReconciliationPanel({
  reconciliation,
  canReview,
  itemJustification,
  onAcceptSafe,
  onAcceptItem,
  onRejectItem,
  setItemJustification,
}: {
  reconciliation: ClinicalReconciliation;
  canReview: boolean;
  itemJustification: string;
  onAcceptSafe: () => void;
  onAcceptItem: (item: ClinicalReconciliationItem) => void;
  onRejectItem: (item: ClinicalReconciliationItem) => void;
  setItemJustification: (value: string) => void;
}) {
  return (
    <section className="mt-5 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h3 className="text-base font-bold text-ink">Reconciliação granular</h3>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            {reconciliation.educational_notice}
          </p>
        </div>
        {canReview ? (
          <button className="btn-secondary" onClick={onAcceptSafe} type="button">
            <Check aria-hidden="true" className="h-4 w-4" />
            Aceitar sem conflito
          </button>
        ) : null}
      </div>
      {canReview ? (
        <label className="mt-4 grid gap-1.5">
          <span className="label">Justificativa para decisão granular</span>
          <input
            className="field"
            value={itemJustification}
            onChange={(event) => setItemJustification(event.target.value)}
          />
        </label>
      ) : null}
      <div className="mt-4 grid gap-2 sm:grid-cols-4">
        {Object.entries(reconciliation.summary).map(([key, value]) => (
          <div className="rounded-lg bg-slate-50 p-3" key={key}>
            <p className="text-xs font-bold uppercase tracking-normal text-slate-500">{key}</p>
            <p className="mt-1 text-lg font-bold text-ink">{value}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px] text-left text-sm">
            <thead className="bg-slate-50 text-xs font-bold uppercase tracking-normal text-slate-500">
              <tr>
                <th className="px-4 py-3">Item</th>
                <th className="px-4 py-3">Atual</th>
                <th className="px-4 py-3">Importado</th>
                <th className="px-4 py-3">Badge</th>
                <th className="px-4 py-3">Sugestão</th>
                <th className="px-4 py-3 text-right">Revisão</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {reconciliation.items.map((item) => (
                <tr className="align-top text-slate-700" key={item.item_id}>
                  <td className="px-4 py-3">
                    <p className="font-semibold text-ink">{item.field_path}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {item.record_type} - confiança {Math.round(item.confidence * 100)}%
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <JsonValue value={item.current_value.value} />
                  </td>
                  <td className="px-4 py-3">
                    <JsonValue value={item.imported_value.value} />
                  </td>
                  <td className="px-4 py-3">
                    <ReconciliationBadge badge={item.badge} conflict={item.conflict} />
                  </td>
                  <td className="px-4 py-3">{item.suggestion}</td>
                  <td className="px-4 py-3 text-right">
                    {canReview && !item.decision ? (
                      <div className="flex justify-end gap-2">
                        <button
                          className="btn-secondary"
                          onClick={() => onAcceptItem(item)}
                          type="button"
                        >
                          <Check aria-hidden="true" className="h-4 w-4" />
                          Aceitar
                        </button>
                        <button
                          className="btn-secondary"
                          onClick={() => onRejectItem(item)}
                          type="button"
                        >
                          <X aria-hidden="true" className="h-4 w-4" />
                          Rejeitar
                        </button>
                      </div>
                    ) : (
                      <span className="font-semibold text-slate-600">
                        {item.decision ?? "-"}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function JsonValue({ value }: { value: unknown }) {
  return (
    <pre className="max-h-32 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-2 text-xs text-slate-700">
      {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
    </pre>
  );
}

function ReconciliationBadge({ badge, conflict }: { badge: string; conflict: boolean }) {
  const classes = conflict
    ? "border-red-200 bg-red-50 text-red-700"
    : badge === "aceito"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : badge === "rejeitado"
        ? "border-slate-200 bg-slate-100 text-slate-700"
        : "border-cyan-100 bg-cyan-50 text-cyan-900";
  return (
    <span className={`rounded-lg border px-2.5 py-1 text-xs font-bold ${classes}`}>
      {badge}
    </span>
  );
}

function StatusPill({ status }: { status: ClinicalImportBatch["status"] }) {
  const label = {
    pending_review: "Pendente",
    accepted: "Aceita",
    rejected: "Rejeitada",
    failed: "Falhou",
  }[status];
  return (
    <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-bold uppercase tracking-normal text-slate-700">
      {label}
    </span>
  );
}
