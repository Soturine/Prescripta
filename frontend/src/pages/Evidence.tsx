import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpenCheck, Link2, Plus } from "lucide-react";
import { useState } from "react";

import LoadingState from "../components/LoadingState";
import PageHeader from "../components/PageHeader";
import Badge from "../components/ui/Badge";
import StatusPanel from "../components/ui/StatusPanel";
import { useAuth } from "../context/AuthContext";
import {
  createEvidenceLink,
  createEvidenceSource,
  fetchEvidenceLinks,
  fetchEvidenceSources,
} from "../services/api";

export default function Evidence() {
  const { can } = useAuth();
  const queryClient = useQueryClient();
  const [sourceForm, setSourceForm] = useState({ title: "", identifier: "", url: "" });
  const [linkForm, setLinkForm] = useState({ source_id: "", target_type: "study", target_id: "", relationship: "supports", locator: "" });
  const sources = useQuery({ queryKey: ["evidence-sources"], queryFn: fetchEvidenceSources });
  const links = useQuery({ queryKey: ["evidence-links"], queryFn: fetchEvidenceLinks });
  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["evidence-sources"] }),
      queryClient.invalidateQueries({ queryKey: ["evidence-links"] }),
    ]);
  };
  const sourceMutation = useMutation({
    mutationFn: () => createEvidenceSource({
      source_type: "other",
      title: sourceForm.title,
      identifier: sourceForm.identifier,
      url: sourceForm.url || null,
      jurisdiction: "BR-demo",
      source_version: "demo-v1",
      license_metadata: { review_required: true },
      provenance: { origin: "manual", copied_full_text: false },
    }),
    onSuccess: async (source) => {
      setSourceForm({ title: "", identifier: "", url: "" });
      setLinkForm((current) => ({ ...current, source_id: source.id }));
      await refresh();
    },
  });
  const linkMutation = useMutation({
    mutationFn: () => createEvidenceLink(linkForm),
    onSuccess: async () => {
      setLinkForm((current) => ({ ...current, target_id: "", locator: "" }));
      await refresh();
    },
  });

  if (sources.isLoading || links.isLoading) return <LoadingState label="Carregando Evidence" />;
  if (sources.isError || links.isError) return <StatusPanel title="Evidence indisponível" tone="danger">Nenhuma relação foi inferida ou criada.</StatusPanel>;

  return <div className="grid gap-6 lg:gap-8">
    <PageHeader title="Evidence Intelligence" description="Fontes cadastradas e relações explícitas. O sistema não inventa vínculos nem copia conteúdo protegido." actions={<Badge tone="warning">Revisão humana</Badge>} />
    <section className="grid gap-6 xl:grid-cols-2">
      <div className="surface-card p-5"><div className="flex items-center justify-between"><div className="flex items-center gap-2"><BookOpenCheck aria-hidden="true" className="h-5 w-5 text-ocean" /><h2 className="text-lg font-black">Sources</h2></div><Badge>{sources.data?.length ?? 0}</Badge></div><div className="mt-4 grid gap-3">{sources.data?.map((source) => <article className="rounded-xl border border-slate-200 p-4" key={source.id}><div className="flex flex-wrap justify-between gap-2"><h3 className="font-extrabold">{source.title}</h3><Badge tone="warning">{source.review_status}</Badge></div><p className="mt-1 text-xs text-slate-500">{source.source_type} · {source.identifier} · {source.jurisdiction ?? "sem jurisdição"}</p></article>)}{!sources.data?.length ? <p className="text-sm text-slate-500">Nenhuma fonte cadastrada.</p> : null}</div></div>
      <div className="surface-card p-5"><div className="flex items-center justify-between"><div className="flex items-center gap-2"><Link2 aria-hidden="true" className="h-5 w-5 text-ocean" /><h2 className="text-lg font-black">Evidence links</h2></div><Badge>{links.data?.length ?? 0}</Badge></div><div className="mt-4 grid gap-3">{links.data?.map((link) => <article className="rounded-xl border border-slate-200 p-4" key={link.id}><p className="font-extrabold">{link.relationship}</p><p className="mt-1 text-xs text-slate-500">{link.target_type}:{link.target_id} · {link.locator || "sem locator"}</p></article>)}{!links.data?.length ? <p className="text-sm text-slate-500">Nenhum vínculo explícito.</p> : null}</div></div>
    </section>
    {can("evidence.write") ? <section className="grid gap-6 xl:grid-cols-2"><form className="surface-card grid gap-3 p-5" onSubmit={(event) => { event.preventDefault(); sourceMutation.mutate(); }}><h2 className="font-black">Cadastrar source</h2><input aria-label="Título da fonte" className="field" onChange={(event) => setSourceForm({ ...sourceForm, title: event.target.value })} placeholder="Título" value={sourceForm.title} /><input aria-label="Identificador da fonte" className="field" onChange={(event) => setSourceForm({ ...sourceForm, identifier: event.target.value })} placeholder="DOI, PMID ou identificador" value={sourceForm.identifier} /><input aria-label="URL da fonte" className="field" onChange={(event) => setSourceForm({ ...sourceForm, url: event.target.value })} placeholder="URL opcional" value={sourceForm.url} /><button className="btn-primary" disabled={sourceMutation.isPending || sourceForm.title.length < 4 || sourceForm.identifier.length < 3} type="submit"><Plus aria-hidden="true" className="h-4 w-4" />Cadastrar</button></form><form className="surface-card grid gap-3 p-5" onSubmit={(event) => { event.preventDefault(); linkMutation.mutate(); }}><h2 className="font-black">Vincular fonte</h2><select aria-label="Fonte" className="field" onChange={(event) => setLinkForm({ ...linkForm, source_id: event.target.value })} value={linkForm.source_id}><option value="">Selecione</option>{sources.data?.map((source) => <option key={source.id} value={source.id}>{source.title}</option>)}</select><select aria-label="Tipo de alvo" className="field" onChange={(event) => setLinkForm({ ...linkForm, target_type: event.target.value })} value={linkForm.target_type}>{["study", "protocol", "outcome", "concept_set", "medication", "dose_rule", "clinical_finding"].map((item) => <option key={item}>{item}</option>)}</select><input aria-label="ID do alvo" className="field" onChange={(event) => setLinkForm({ ...linkForm, target_id: event.target.value })} placeholder="Target ID" value={linkForm.target_id} /><input aria-label="Locator" className="field" onChange={(event) => setLinkForm({ ...linkForm, locator: event.target.value })} placeholder="Página/seção opcional" value={linkForm.locator} /><button className="btn-primary" disabled={linkMutation.isPending || !linkForm.source_id || !linkForm.target_id} type="submit">Criar link</button></form></section> : null}
  </div>;
}
