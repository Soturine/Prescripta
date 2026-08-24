import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ClipboardPlus, Clock3, FileSearch, MessageSquareWarning, Pill, UserRound } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import LoadingState from "../components/LoadingState";
import PageHeader from "../components/PageHeader";
import Badge from "../components/ui/Badge";
import StatusPanel from "../components/ui/StatusPanel";
import TechnicalDetails from "../components/ui/TechnicalDetails";
import { useAuth } from "../context/AuthContext";
import {
  createPharmacyIntervention,
  decidePharmacyIntervention,
  fetchMedications,
  fetchPatients,
  fetchPharmacyInterventions,
  resolvePharmacyIntervention,
} from "../services/api";
import { formatDateTime, formatStatus, humanizeTechnicalValue } from "../utils/formatters";

export default function Pharmacy() {
  const { can } = useAuth();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ patientId: "", medicationId: "", problem: "", recommendation: "", source: "" });
  const query = useQuery({ queryKey: ["pharmacy-interventions"], queryFn: fetchPharmacyInterventions });
  const patientsQuery = useQuery({ queryKey: ["patients"], queryFn: fetchPatients });
  const medicationsQuery = useQuery({ queryKey: ["medications"], queryFn: fetchMedications });
  const patientById = new Map((patientsQuery.data ?? []).map((patient) => [patient.id, patient.name]));
  const medicationById = new Map((medicationsQuery.data ?? []).map((medication) => [medication.id, medication.brand_name || medication.active_ingredient]));
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["pharmacy-interventions"] });
  const createMutation = useMutation({
    mutationFn: () => createPharmacyIntervention({ patient_id: Number(form.patientId), medication_id: form.medicationId ? Number(form.medicationId) : null, intervention_type: "dose", severity: "moderate", priority: "priority", problem: form.problem, recommendation: form.recommendation, source_refs: [form.source], dose_snapshot: {}, idempotency_key: `ui-${crypto.randomUUID()}` }),
    onSuccess: async () => { setForm({ patientId: "", medicationId: "", problem: "", recommendation: "", source: "" }); await refresh(); },
  });
  const decisionMutation = useMutation({ mutationFn: ({ id, version, decision }: { id: number; version: number; decision: "accepted" | "rejected" }) => decidePharmacyIntervention(id, decision, "Decisão humana registrada no workspace profissional.", version), onSuccess: refresh });
  const resolveMutation = useMutation({ mutationFn: ({ id, version }: { id: number; version: number }) => resolvePharmacyIntervention(id, "Intervenção documentada e encerrada após decisão humana.", version), onSuccess: refresh });

  if (query.isLoading) return <LoadingState label={t("pharmacy.loading")} />;
  if (query.isError) return <StatusPanel title={t("pharmacy.errorTitle")} tone="danger">{t("pharmacy.errorBody")}</StatusPanel>;

  return (
    <div className="grid gap-6 lg:gap-8">
      <PageHeader title={t("pharmacy.title")} description={t("pharmacy.description")} actions={<Badge tone="info">{t("pharmacy.humanDecision")}</Badge>} />
      <section className="grid gap-6 xl:grid-cols-[minmax(20rem,.72fr)_minmax(0,1.28fr)]">
        {can("pharmacy.intervention.write") ? (
          <form className="surface-card grid content-start gap-3 p-5" onSubmit={(event) => { event.preventDefault(); createMutation.mutate(); }}>
            <div className="mb-2 flex items-center gap-2"><ClipboardPlus aria-hidden="true" className="h-5 w-5 text-ocean" /><h2 className="font-black">{t("pharmacy.new")}</h2></div>
            <label className="grid gap-1 text-sm font-bold">{t("pharmacy.patientSearch")}<select className="field" onChange={(event) => setForm({ ...form, patientId: event.target.value })} value={form.patientId}><option value="">{t("pharmacy.selectPatient")}</option>{patientsQuery.data?.map((patient) => <option key={patient.id} value={patient.id}>{patient.name}</option>)}</select></label>
            <label className="grid gap-1 text-sm font-bold">{t("pharmacy.medicationSearch")}<select className="field" onChange={(event) => setForm({ ...form, medicationId: event.target.value })} value={form.medicationId}><option value="">{t("pharmacy.noMedication")}</option>{medicationsQuery.data?.map((medication) => <option key={medication.id} value={medication.id}>{medication.brand_name} · {medication.active_ingredient}</option>)}</select></label>
            <textarea aria-label={t("pharmacy.problem")} className="field min-h-24" onChange={(event) => setForm({ ...form, problem: event.target.value })} placeholder={t("pharmacy.problem")} value={form.problem} />
            <textarea aria-label={t("pharmacy.recommendation")} className="field min-h-24" onChange={(event) => setForm({ ...form, recommendation: event.target.value })} placeholder={t("pharmacy.recommendation")} value={form.recommendation} />
            <input aria-label={t("pharmacy.source")} className="field" onChange={(event) => setForm({ ...form, source: event.target.value })} placeholder={t("pharmacy.source")} value={form.source} />
            <button className="btn-primary" disabled={createMutation.isPending || Number(form.patientId) < 1 || form.problem.length < 8 || form.recommendation.length < 8 || form.source.length < 2} type="submit">{t("pharmacy.register")}</button>
          </form>
        ) : null}

        <div className="grid content-start gap-4">
          {query.data?.map((item) => (
            <article className="surface-card overflow-hidden" key={item.id}>
              <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 bg-slate-50/70 p-5">
                <div className="flex gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-amber-800"><MessageSquareWarning aria-hidden="true" className="h-5 w-5" /></span><div><h3 className="font-black">{humanizeTechnicalValue(item.intervention_type)}</h3><p className="mt-1 text-xs text-slate-500">{t("pharmacy.version", { version: item.version })}</p></div></div>
                <Badge tone={item.status === "resolved" ? "success" : item.priority === "urgent" ? "danger" : "warning"}>{formatStatus(item.status)}</Badge>
              </div>
              <div className="grid gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_15rem]">
                <div>
                  <div className="flex flex-wrap gap-2 text-xs font-bold text-slate-600"><span className="inline-flex items-center gap-1 rounded-full bg-cyan-50 px-2.5 py-1"><UserRound aria-hidden="true" className="h-3.5 w-3.5" />{patientById.get(item.patient_id) ?? t("pharmacy.authorizedPatient")}</span><span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1"><Pill aria-hidden="true" className="h-3.5 w-3.5" />{item.medication_id ? medicationById.get(item.medication_id) ?? t("pharmacy.linkedMedication") : t("pharmacy.noMedication")}</span></div>
                  <p className="mt-4 text-sm font-extrabold text-slate-800">{item.problem}</p>
                  <h4 className="mt-4 text-xs font-black uppercase tracking-[0.1em] text-ocean">{t("pharmacy.recommendationTitle")}</h4><p className="mt-1 text-sm leading-6 text-slate-600">{item.recommendation}</p>
                  <div className="mt-4 flex flex-wrap gap-2"><Badge>{t("pharmacy.priority")}: {formatStatus(item.priority)}</Badge><Badge>{t("pharmacy.severity")}: {formatStatus(item.severity)}</Badge></div>
                  <div className="mt-4"><h4 className="flex items-center gap-1 text-xs font-black text-slate-600"><FileSearch aria-hidden="true" className="h-4 w-4" />{t("pharmacy.sources")}</h4><div className="mt-2 flex flex-wrap gap-2">{item.source_refs.map((source) => <code className="rounded-lg bg-slate-100 px-2 py-1 text-[0.6875rem]" key={source}>{source}</code>)}</div></div>
                  <div className="mt-4"><TechnicalDetails copyValue={`intervention_id=${item.id};patient_id=${item.patient_id};medication_id=${item.medication_id ?? ""}`}><code className="text-xs">intervention_id: {item.id}<br />patient_id: {item.patient_id}<br />medication_id: {item.medication_id ?? "—"}</code></TechnicalDetails></div>
                  <div className="mt-5 flex flex-wrap gap-2">{item.status === "open" && can("pharmacy.intervention.decide") ? <><button className="btn-primary" disabled={decisionMutation.isPending} onClick={() => decisionMutation.mutate({ id: item.id, version: item.version, decision: "accepted" })} type="button"><CheckCircle2 aria-hidden="true" className="h-4 w-4" />{t("pharmacy.accept")}</button><button className="btn-secondary" disabled={decisionMutation.isPending} onClick={() => decisionMutation.mutate({ id: item.id, version: item.version, decision: "rejected" })} type="button">{t("pharmacy.reject")}</button></> : null}{["accepted", "rejected"].includes(item.status) && can("pharmacy.intervention.write") ? <button className="btn-secondary" disabled={resolveMutation.isPending} onClick={() => resolveMutation.mutate({ id: item.id, version: item.version })} type="button">{t("pharmacy.resolve")}</button> : null}</div>
                </div>
                <aside className="rounded-xl border border-slate-200 bg-slate-50/70 p-4"><h4 className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.1em] text-slate-600"><Clock3 aria-hidden="true" className="h-4 w-4" />{t("pharmacy.timeline")}</h4><ol className="mt-4 grid gap-4 border-l-2 border-cyan-200 pl-4 text-xs"><li><strong className="block text-ink">{t("pharmacy.created")}</strong><span className="text-slate-500">{formatDateTime(item.created_at)}</span></li><li><strong className="block text-ink">{t("pharmacy.updated")}</strong><span className="text-slate-500">{formatDateTime(item.updated_at)}</span></li></ol></aside>
              </div>
            </article>
          ))}
          {!query.data?.length ? <StatusPanel title={t("pharmacy.emptyTitle")} tone="info">{t("pharmacy.emptyBody")}</StatusPanel> : null}
        </div>
      </section>
    </div>
  );
}
