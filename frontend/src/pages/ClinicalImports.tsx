import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Check,
  DatabaseZap,
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
  checkCdsPrescription,
  fetchClinicalImports,
  importClinicalCsv,
  importClinicalFhir,
  importClinicalJson,
  rejectClinicalImport,
} from "../services/api";
import type { ClinicalImportBatch, ImportConsentPayload } from "../types/integration";
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

const fhirDemo = JSON.stringify(
  {
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
  null,
  2,
);

const csvDemo = "record_type,value\nmedication,Novalgina\ncondition,renal\n";

export default function ClinicalImports() {
  const { canAccess } = useAuth();
  const canReview = canAccess(["admin", "medico"]);
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mode, setMode] = useState<"json" | "fhir" | "csv">("json");
  const [sourceSystem, setSourceSystem] = useState("mock_hospital");
  const [purpose, setPurpose] = useState("Importacao clinica demonstrativa");
  const [authorizedBy, setAuthorizedBy] = useState("Paciente/representante demo");
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [body, setBody] = useState(jsonDemo);
  const [rejectReason, setRejectReason] = useState("Rejeitado em revisao humana.");
  const { data: imports = [], isLoading } = useQuery({
    queryKey: ["clinical-imports"],
    queryFn: fetchClinicalImports,
  });
  const selected = useMemo(
    () => imports.find((item) => item.id === selectedId) ?? imports[0],
    [imports, selectedId],
  );
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

  function changeMode(nextMode: "json" | "fhir" | "csv") {
    setMode(nextMode);
    setBody(nextMode === "json" ? jsonDemo : nextMode === "fhir" ? fhirDemo : csvDemo);
  }

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Importacoes Clinicas</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Recurso demonstrativo com consentimento, auditoria e revisao humana obrigatoria.
        </p>
      </header>

      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm font-medium leading-6 text-amber-900">
        Este recurso e demonstrativo. Integracoes reais exigem autorizacao, contrato,
        seguranca, governanca e conformidade com LGPD.
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <ShieldCheck aria-hidden="true" className="h-5 w-5 text-ocean" />
            <h2 className="text-lg font-bold text-ink">Nova importacao</h2>
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
              Confirmo que ha autorizacao do paciente ou base legal aplicavel para importar estes dados.
            </label>
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
                Nao foi possivel importar. Revise consentimento e payload.
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
              <p className="text-sm text-slate-500">Nenhuma importacao registrada.</p>
            ) : null}
          </div>
        </div>
      </section>

      {selected ? (
        <ImportDetail
          batch={selected}
          canReview={canReview}
          isAccepting={acceptMutation.isPending}
          isRejecting={rejectMutation.isPending}
          onAccept={() => acceptMutation.mutate(selected.id)}
          onReject={() => rejectMutation.mutate(selected.id)}
          rejectReason={rejectReason}
          setRejectReason={setRejectReason}
        />
      ) : null}

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <FlaskConical aria-hidden="true" className="h-5 w-5 text-ocean" />
          <h2 className="text-lg font-bold text-ink">Integracao externa / CDS API</h2>
        </div>
        <div className="mt-4 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
            <p className="font-mono text-sm font-semibold text-ink">
              POST /api/cds/prescription-check
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Endpoint demonstrativo com persist=false, regras deterministicas e cards estilo CDS.
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
              <p className="text-sm text-slate-500">Resultado CDS aparece aqui apos teste.</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function ImportDetail({
  batch,
  canReview,
  isAccepting,
  isRejecting,
  onAccept,
  onReject,
  rejectReason,
  setRejectReason,
}: {
  batch: ClinicalImportBatch;
  canReview: boolean;
  isAccepting: boolean;
  isRejecting: boolean;
  onAccept: () => void;
  onReject: () => void;
  rejectReason: string;
  setRejectReason: (value: string) => void;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-bold text-ink">Detalhes da importacao #{batch.id}</h2>
          <p className="mt-1 text-sm text-slate-600">
            Consentimento #{batch.consent_id ?? "-"} - {batch.records.length} registros
          </p>
        </div>
        <StatusPill status={batch.status} />
      </div>
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
                confianca {Math.round(record.confidence * 100)}%
              </span>
            </div>
            <pre className="mt-3 max-h-52 overflow-auto rounded-lg bg-white p-3 text-xs text-slate-700">
              {JSON.stringify(record.mapped_payload, null, 2)}
            </pre>
          </article>
        ))}
      </div>
      {canReview && batch.status === "pending_review" ? (
        <div className="mt-4 flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center">
          <button
            className="btn-primary"
            disabled={isAccepting}
            onClick={onAccept}
            title="Aceitar importacao"
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
            title="Rejeitar importacao"
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
