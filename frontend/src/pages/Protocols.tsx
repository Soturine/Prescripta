import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  Download,
  FileJson,
  FileText,
  Search,
  ShieldAlert,
  Siren,
  Sparkles,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { Dispatch, SetStateAction } from "react";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import { useAuth } from "../context/AuthContext";
import {
  downloadProtocolRunReportPdf,
  explainProtocol,
  exportProtocolRunCsv,
  exportProtocolRunJson,
  fetchProtocolEvidence,
  fetchProtocolReport,
  fetchProtocols,
  fetchPatients,
  runProtocol,
} from "../services/api";
import type { Patient } from "../types/patient";
import type {
  EmergencyProtocol,
  ProtocolContext,
  ProtocolContextField,
  ProtocolEvidence,
  ProtocolRunResult,
  ProtocolRunPayload,
  ProtocolStep,
  ProtocolWarningLevel,
} from "../types/protocol";

type FieldValues = Record<string, string>;

export default function Protocols() {
  const { canAccess } = useAuth();
  const canRun = canAccess(["admin", "medico", "enfermagem"]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [category, setCategory] = useState("todos");
  const [search, setSearch] = useState("");
  const [fieldValues, setFieldValues] = useState<FieldValues>({});
  const [selectedSteps, setSelectedSteps] = useState<number[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
  const [notes, setNotes] = useState("");
  const [question, setQuestion] = useState("Explique o racional sem alterar o fluxo.");

  const { data: protocols = [], isLoading } = useQuery({
    queryKey: ["protocols"],
    queryFn: () => fetchProtocols(),
  });
  const { data: patients = [] } = useQuery({
    queryKey: ["patients"],
    queryFn: fetchPatients,
  });

  const selectedProtocol = protocols.find((protocol) => protocol.id === selectedId) ?? protocols[0];
  const { data: evidence = [] } = useQuery({
    queryKey: ["protocols", selectedProtocol?.id, "evidence"],
    queryFn: () => fetchProtocolEvidence(String(selectedProtocol?.id)),
    enabled: Boolean(selectedProtocol),
  });

  useEffect(() => {
    if (!selectedId && protocols.length) {
      setSelectedId(protocols[0].id);
    }
  }, [protocols, selectedId]);

  useEffect(() => {
    if (selectedProtocol) {
      setFieldValues(initialValues(selectedProtocol.context_fields));
      setSelectedSteps([]);
      setNotes("");
    }
  }, [selectedProtocol?.id]);

  const categories = useMemo(
    () => Array.from(new Set(protocols.map((protocol) => protocol.category))).sort(),
    [protocols],
  );
  const visibleProtocols = useMemo(() => {
    const query = search.trim().toLowerCase();
    return protocols.filter((protocol) => {
      const matchesCategory = category === "todos" || protocol.category === category;
      const matchesSearch =
        !query ||
        [protocol.title, protocol.category, protocol.summary, ...protocol.red_flags]
          .join(" ")
          .toLowerCase()
          .includes(query);
      return matchesCategory && matchesSearch;
    });
  }, [protocols, category, search]);

  const runMutation = useMutation({
    mutationFn: () =>
      runProtocol(
        String(selectedProtocol?.id),
        buildRunPayload(selectedProtocol, fieldValues, selectedSteps, notes, selectedPatientId),
      ),
  });
  const explainMutation = useMutation({
    mutationFn: () =>
      explainProtocol(String(selectedProtocol?.id), {
        context: buildContext(selectedProtocol?.context_fields ?? [], fieldValues),
        run_id: runMutation.data?.run_id ?? null,
        question: question || null,
      }),
  });
  const reportMutation = useMutation({
    mutationFn: () => fetchProtocolReport(String(selectedProtocol?.id), runMutation.data?.run_id),
  });

  if (isLoading) {
    return <LoadingState label="Carregando protocolos" />;
  }

  if (!selectedProtocol) {
    return <EmptyState title="Nenhum protocolo disponível" />;
  }

  return (
    <div className="grid gap-6">
      <header className="overflow-hidden rounded-lg border border-cyan-200 bg-gradient-to-br from-cyan-900 via-ocean to-slate-900 p-6 text-white shadow-soft">
        <div className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-lg bg-white/10 px-3 py-1 text-xs font-bold">
              <Siren aria-hidden="true" className="h-4 w-4" />
              Central de Protocolos Rápidos
            </div>
            <h1 className="mt-4 text-3xl font-bold tracking-normal">
              Apoio emergencial estruturado, rastreável e sem decisão automática.
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-cyan-50">
              Fluxos demonstrativos com fonte, passos auditáveis, contexto mínimo e explicação
              controlada. A execução registra auditoria e preserva decisão humana.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <Metric label="Protocolos" value={protocols.length} />
            <Metric label="Fontes BR" value="7" />
            <Metric label="IA" value="explica" />
          </div>
        </div>
      </header>

      <section className="grid gap-4 xl:grid-cols-[360px_1fr]">
        <aside className="grid content-start gap-4">
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <div className="grid gap-3">
              <label className="grid gap-1.5">
                <span className="label">Buscar protocolo</span>
                <span className="relative">
                  <Search
                    aria-hidden="true"
                    className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400"
                  />
                  <input
                    className="field pl-9"
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Anafilaxia, glicemia, dor..."
                    value={search}
                  />
                </span>
              </label>
              <label className="grid gap-1.5">
                <span className="label">Categoria</span>
                <select
                  className="field"
                  onChange={(event) => setCategory(event.target.value)}
                  value={category}
                >
                  <option value="todos">Todas</option>
                  {categories.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          <div className="grid gap-3">
            {visibleProtocols.map((protocol) => (
              <button
                className={[
                  "group rounded-lg border p-4 text-left shadow-sm transition",
                  selectedProtocol.id === protocol.id
                    ? "border-ocean bg-cyan-50"
                    : "border-slate-200 bg-white hover:border-cyan-300 hover:bg-cyan-50/50",
                ].join(" ")}
                key={protocol.id}
                onClick={() => setSelectedId(protocol.id)}
                type="button"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-bold text-ink">{protocol.title}</p>
                    <p className="mt-1 text-xs font-semibold text-slate-500">{protocol.category}</p>
                  </div>
                  <WarningBadge level={protocol.severity_level} />
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-600">{protocol.summary}</p>
              </button>
            ))}
          </div>
        </aside>

        <main className="grid gap-4">
          <ProtocolHeader protocol={selectedProtocol} />

          <section className="grid gap-4 lg:grid-cols-[1fr_360px]">
            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="text-lg font-bold text-ink">Passo a passo</h2>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    Marque apenas o que foi revisado/executado no cenário demonstrativo.
                  </p>
                </div>
                <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
                  {selectedProtocol.steps.length} passos
                </span>
              </div>
              <div className="mt-4 grid gap-3">
                {selectedProtocol.steps.map((step) => (
                  <ProtocolStepRow
                    checked={selectedSteps.includes(step.order)}
                    key={step.order}
                    onToggle={() => toggleStep(step.order, setSelectedSteps)}
                    step={step}
                  />
                ))}
              </div>
            </div>

            <div className="grid content-start gap-4">
              <ContextPanel
                canRun={canRun}
                fieldValues={fieldValues}
                isRunning={runMutation.isPending}
                notes={notes}
                onFieldChange={(name, value) =>
                  setFieldValues((current) => ({ ...current, [name]: value }))
                }
                onNotesChange={setNotes}
                onRun={() => runMutation.mutate()}
                onPatientChange={setSelectedPatientId}
                patients={patients}
                protocol={selectedProtocol}
                selectedPatientId={selectedPatientId}
              />
              {runMutation.isError ? (
                <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-700">
                  Não foi possível executar. Confira o contexto mínimo obrigatório.
                </div>
              ) : null}
            </div>
          </section>

          {runMutation.data ? (
            <RunResultPanel
              onCsv={() => exportProtocolRunCsv(selectedProtocol.id, runMutation.data.run_id)}
              onJson={() => exportProtocolRunJson(selectedProtocol.id, runMutation.data.run_id)}
              onPdf={() => downloadProtocolRunReportPdf(runMutation.data.run_id)}
              onReport={() => reportMutation.mutate()}
              result={runMutation.data}
            />
          ) : null}

          <section className="grid gap-4 lg:grid-cols-[1fr_1fr]">
            <EvidencePanel evidence={evidence} protocol={selectedProtocol} />
            <ExplainPanel
              canRun={canRun}
              isExplaining={explainMutation.isPending}
              onExplain={() => explainMutation.mutate()}
              question={question}
              result={explainMutation.data ?? null}
              setQuestion={setQuestion}
            />
          </section>

          {reportMutation.data ? (
            <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <FileText aria-hidden="true" className="h-5 w-5 text-ocean" />
                <h2 className="text-lg font-bold text-ink">Preview do relatório</h2>
              </div>
              <pre className="mt-4 max-h-96 overflow-auto rounded-lg bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                {reportMutation.data.report_lines.join("\n")}
              </pre>
            </section>
          ) : null}
        </main>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-white/15 bg-white/10 px-3 py-4">
      <p className="text-2xl font-bold">{value}</p>
      <p className="mt-1 text-xs font-semibold text-cyan-50">{label}</p>
    </div>
  );
}

function ProtocolHeader({ protocol }: { protocol: EmergencyProtocol }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <WarningBadge level={protocol.severity_level} />
            <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
              {protocol.jurisdiction} · {protocol.validation_status}
            </span>
          </div>
          <h2 className="mt-3 text-2xl font-bold tracking-normal text-ink">{protocol.title}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            {protocol.clinical_goal}
          </p>
        </div>
        <div className="rounded-lg border border-cyan-100 bg-cyan-50 p-3 text-sm leading-6 text-cyan-950 lg:max-w-sm">
          <p className="font-bold">Fonte</p>
          <p>{protocol.source_name}</p>
          <p className="mt-1 text-xs font-semibold">{protocol.source_version}</p>
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <InfoList title="Alertas" items={protocol.red_flags} icon={AlertTriangle} />
        <InfoList title="Monitorar" items={protocol.monitoring} icon={ShieldAlert} />
        <InfoList title="Documentar" items={protocol.documentation_items} icon={FileJson} />
      </div>
    </section>
  );
}

function InfoList({
  title,
  items,
  icon: Icon,
}: {
  title: string;
  items: string[];
  icon: typeof AlertTriangle;
}) {
  return (
    <article className="rounded-lg border border-slate-100 bg-slate-50 p-4">
      <div className="flex items-center gap-2">
        <Icon aria-hidden="true" className="h-4 w-4 text-ocean" />
        <h3 className="text-sm font-bold text-ink">{title}</h3>
      </div>
      <ul className="mt-3 grid gap-2 text-sm leading-5 text-slate-600">
        {items.slice(0, 4).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </article>
  );
}

function ProtocolStepRow({
  step,
  checked,
  onToggle,
}: {
  step: ProtocolStep;
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <article className="rounded-lg border border-slate-100 bg-slate-50 p-4 transition hover:border-cyan-200 hover:bg-cyan-50/40">
      <div className="flex gap-3">
        <button
          className={[
            "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border transition",
            checked ? "border-ocean bg-ocean text-white" : "border-slate-300 bg-white text-slate-400",
          ].join(" ")}
          onClick={onToggle}
          title={checked ? "Desmarcar passo" : "Marcar passo"}
          type="button"
        >
          <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
        </button>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-md bg-white px-2 py-1 text-xs font-bold text-slate-600">
              {step.order}
            </span>
            <h3 className="text-sm font-bold text-ink">{step.title}</h3>
            <WarningBadge level={step.warning_level} />
          </div>
          <p className="mt-2 text-sm font-semibold leading-6 text-slate-800">{step.action}</p>
          <p className="mt-1 text-sm leading-6 text-slate-600">{step.explanation}</p>
          <p className="mt-2 text-xs font-semibold text-slate-500">
            Evidência: {step.evidence_ref}
          </p>
        </div>
      </div>
    </article>
  );
}

function ContextPanel({
  protocol,
  fieldValues,
  notes,
  patients,
  selectedPatientId,
  canRun,
  isRunning,
  onFieldChange,
  onNotesChange,
  onPatientChange,
  onRun,
}: {
  protocol: EmergencyProtocol;
  fieldValues: FieldValues;
  notes: string;
  patients: Patient[];
  selectedPatientId: number | null;
  canRun: boolean;
  isRunning: boolean;
  onFieldChange: (name: string, value: string) => void;
  onNotesChange: (value: string) => void;
  onPatientChange: (value: number | null) => void;
  onRun: () => void;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-bold text-ink">Contexto mínimo</h2>
      <div className="mt-4 grid gap-3">
        <label className="grid gap-1.5">
          <span className="label">Selecionar paciente</span>
          <select
            className="field"
            onChange={(event) =>
              onPatientChange(event.target.value ? Number(event.target.value) : null)
            }
            value={selectedPatientId ?? ""}
          >
            <option value="">Sem paciente vinculado</option>
            {patients.map((patient) => (
              <option key={patient.id} value={patient.id}>
                {patient.name} - {patient.age ?? "idade?"} anos - {patient.weight_kg} kg
              </option>
            ))}
          </select>
          <span className="text-xs text-slate-500">
            Idade, peso, alergias, medicamentos e historico revisado entram como contexto.
          </span>
        </label>
        {protocol.context_fields.map((field) => (
          <ContextInput
            field={field}
            key={field.name}
            onChange={(value) => onFieldChange(field.name, value)}
            value={fieldValues[field.name] ?? ""}
          />
        ))}
        <label className="grid gap-1.5">
          <span className="label">Notas do cenário</span>
          <textarea
            className="field min-h-20 resize-y"
            onChange={(event) => onNotesChange(event.target.value)}
            placeholder="Sem dado real de paciente"
            value={notes}
          />
        </label>
      </div>
      <button
        className="btn-primary mt-4 w-full"
        disabled={!canRun || isRunning}
        onClick={onRun}
        type="button"
      >
        <Siren aria-hidden="true" className="h-4 w-4" />
        {isRunning ? "Registrando..." : "Executar fluxo"}
      </button>
      {!canRun ? (
        <p className="mt-2 text-xs font-semibold text-slate-500">
          Seu perfil pode consultar protocolos, mas não registrar execução.
        </p>
      ) : null}
    </section>
  );
}

function ContextInput({
  field,
  value,
  onChange,
}: {
  field: ProtocolContextField;
  value: string;
  onChange: (value: string) => void;
}) {
  if (field.field_type === "boolean") {
    return (
      <label className="grid gap-1.5">
        <span className="label">
          {field.label}
          {field.required ? " *" : ""}
        </span>
        <select className="field" onChange={(event) => onChange(event.target.value)} value={value}>
          <option value="">Não informado</option>
          <option value="true">Sim</option>
          <option value="false">Não</option>
        </select>
        {field.helper ? <span className="text-xs text-slate-500">{field.helper}</span> : null}
      </label>
    );
  }
  return (
    <label className="grid gap-1.5">
      <span className="label">
        {field.label}
        {field.unit ? ` (${field.unit})` : ""}
        {field.required ? " *" : ""}
      </span>
      <input
        className="field"
        onChange={(event) => onChange(event.target.value)}
        type={field.field_type === "number" ? "number" : "text"}
        value={value}
      />
      {field.helper ? <span className="text-xs text-slate-500">{field.helper}</span> : null}
    </label>
  );
}

function RunResultPanel({
  result,
  onReport,
  onPdf,
  onJson,
  onCsv,
}: {
  result: ProtocolRunResult;
  onReport: () => void;
  onPdf: () => void;
  onJson: () => void;
  onCsv: () => void;
}) {
  return (
    <section className="rounded-lg border border-emerald-200 bg-emerald-50 p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-bold text-emerald-950">Execução registrada</h2>
          <p className="mt-1 text-sm font-semibold text-emerald-900">{result.audit_notice}</p>
          <p className="mt-1 text-xs font-bold text-emerald-900">
            Versao {result.protocol_version}
            {result.patient_id ? ` - Paciente #${result.patient_id}` : " - sem paciente vinculado"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="btn-secondary" onClick={onReport} type="button">
            <FileText aria-hidden="true" className="h-4 w-4" />
            Preview
          </button>
          <button className="btn-secondary" onClick={onPdf} type="button">
            <Download aria-hidden="true" className="h-4 w-4" />
            PDF
          </button>
          <button className="btn-secondary" onClick={onJson} type="button">
            <FileJson aria-hidden="true" className="h-4 w-4" />
            JSON
          </button>
          <button className="btn-secondary" onClick={onCsv} type="button">
            <Download aria-hidden="true" className="h-4 w-4" />
            CSV
          </button>
        </div>
      </div>
      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        {result.patient_context_summary && Object.keys(result.patient_context_summary).length ? (
          <div className="rounded-lg border border-emerald-200 bg-white p-4 lg:col-span-2">
            <h3 className="text-sm font-bold text-ink">Contexto do paciente</h3>
            <div className="mt-3 grid gap-2 text-sm text-slate-600 sm:grid-cols-2 lg:grid-cols-4">
              {[
                ["Idade", result.patient_context_summary.age_years],
                ["Peso", result.patient_context_summary.weight_kg],
                [
                  "Altura/IMC",
                  `${result.patient_context_summary.height_cm ?? "-"} / ${result.patient_context_summary.bmi ?? "-"}`,
                ],
                ["Documentos revisados", result.patient_context_summary.reviewed_documents],
              ].map(([label, value]) => (
                <p className="rounded-lg bg-slate-50 px-3 py-2" key={String(label)}>
                  <strong className="text-ink">{String(label)}:</strong> {String(value ?? "-")}
                </p>
              ))}
            </div>
          </div>
        ) : null}
        <div className="rounded-lg border border-emerald-200 bg-white p-4">
          <h3 className="text-sm font-bold text-ink">Flags</h3>
          <div className="mt-3 grid gap-2 text-sm text-slate-600">
            {result.triage_flags.map((flag) => (
              <p key={flag}>{flag}</p>
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-emerald-200 bg-white p-4">
          <h3 className="text-sm font-bold text-ink">Cálculos demonstrativos</h3>
          <div className="mt-3 grid gap-2 text-sm text-slate-600">
            {result.calculated_values.length ? (
              result.calculated_values.map((item) => (
                <p key={item.label}>
                  <strong className="text-ink">{item.label}:</strong> {item.value}. {item.warning}
                </p>
              ))
            ) : (
              <p>Nenhum cálculo aplicável para o contexto informado.</p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function EvidencePanel({
  protocol,
  evidence,
}: {
  protocol: EmergencyProtocol;
  evidence: ProtocolEvidence[];
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <ShieldAlert aria-hidden="true" className="h-5 w-5 text-ocean" />
        <h2 className="text-lg font-bold text-ink">Fonte e evidência</h2>
      </div>
      <div className="mt-4 rounded-lg border border-cyan-100 bg-cyan-50 p-4 text-sm leading-6 text-cyan-950">
        <p className="font-bold">{protocol.source_name}</p>
        <p>{protocol.source_version}</p>
        {protocol.source_url ? (
          <a className="font-bold underline" href={protocol.source_url} rel="noreferrer" target="_blank">
            Abrir fonte
          </a>
        ) : null}
      </div>
      <div className="mt-4 grid gap-2">
        {evidence.slice(0, 6).map((item) => (
          <article className="rounded-lg border border-slate-100 bg-slate-50 p-3" key={item.evidence_ref}>
            <p className="text-xs font-bold uppercase tracking-normal text-slate-500">
              {item.evidence_ref}
            </p>
            <p className="mt-1 text-sm leading-6 text-slate-600">{item.summary}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function ExplainPanel({
  canRun,
  question,
  setQuestion,
  onExplain,
  isExplaining,
  result,
}: {
  canRun: boolean;
  question: string;
  setQuestion: (value: string) => void;
  onExplain: () => void;
  isExplaining: boolean;
  result: {
    provider: string;
    model?: string | null;
    used_fallback: boolean;
    simple_explanation: string;
    professional_summary: string;
    safety_note: string;
    structure_locked: boolean;
  } | null;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <Bot aria-hidden="true" className="h-5 w-5 text-ocean" />
        <h2 className="text-lg font-bold text-ink">Explicação controlada</h2>
      </div>
      <label className="mt-4 grid gap-1.5">
        <span className="label">Pergunta contextual</span>
        <textarea
          className="field min-h-20 resize-y"
          onChange={(event) => setQuestion(event.target.value)}
          value={question}
        />
      </label>
      <button
        className="btn-primary mt-4"
        disabled={!canRun || isExplaining}
        onClick={onExplain}
        type="button"
      >
        <Sparkles aria-hidden="true" className="h-4 w-4" />
        {isExplaining ? "Explicando..." : "Explicar protocolo"}
      </button>
      {result ? (
        <div className="mt-4 grid gap-3 rounded-lg border border-slate-100 bg-slate-50 p-4 text-sm leading-6 text-slate-700">
          <p>
            <strong className="text-ink">Provider:</strong> {result.provider}
            {result.model ? ` / ${result.model}` : ""} ·{" "}
            {result.used_fallback ? "fallback local" : "IA externa"}
          </p>
          <p>{result.simple_explanation}</p>
          <p>{result.professional_summary}</p>
          <p className="font-semibold text-slate-900">{result.safety_note}</p>
        </div>
      ) : null}
    </section>
  );
}

function WarningBadge({ level }: { level: ProtocolWarningLevel }) {
  const styles: Record<ProtocolWarningLevel, string> = {
    info: "bg-slate-100 text-slate-700",
    attention: "bg-amber-50 text-amber-700",
    high: "bg-orange-50 text-orange-700",
    critical: "bg-red-50 text-red-700",
  };
  const labels: Record<ProtocolWarningLevel, string> = {
    info: "informativo",
    attention: "atenção",
    high: "alto",
    critical: "crítico",
  };
  return (
    <span className={`rounded-lg px-2 py-1 text-xs font-bold ${styles[level]}`}>
      {labels[level]}
    </span>
  );
}

function initialValues(fields: ProtocolContextField[]): FieldValues {
  return Object.fromEntries(fields.map((field) => [field.name, ""]));
}

function buildRunPayload(
  protocol: EmergencyProtocol | undefined,
  values: FieldValues,
  selectedStepOrders: number[],
  notes: string,
  patientId: number | null,
): ProtocolRunPayload {
  return {
    patient_id: patientId,
    context: buildContext(protocol?.context_fields ?? [], values),
    selected_step_orders: selectedStepOrders,
    notes: notes || null,
  };
}

function buildContext(fields: ProtocolContextField[], values: FieldValues): ProtocolContext {
  return Object.fromEntries(
    fields
      .map((field) => [field.name, normalizeValue(field, values[field.name])])
      .filter(([, value]) => value !== null && value !== ""),
  );
}

function normalizeValue(field: ProtocolContextField, value: string | undefined) {
  if (value === undefined || value === "") {
    return null;
  }
  if (field.field_type === "number") {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  }
  if (field.field_type === "boolean") {
    if (value === "true") {
      return true;
    }
    if (value === "false") {
      return false;
    }
    return null;
  }
  return value;
}

function toggleStep(order: number, setSelectedSteps: Dispatch<SetStateAction<number[]>>) {
  setSelectedSteps((current) =>
    current.includes(order) ? current.filter((item) => item !== order) : [...current, order],
  );
}
