import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpenCheck, Link2, Plus } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import LoadingState from "../components/LoadingState";
import PageHeader from "../components/PageHeader";
import Badge from "../components/ui/Badge";
import StatusPanel from "../components/ui/StatusPanel";
import { useAuth } from "../context/AuthContext";
import { createEvidenceLink, createEvidenceSource, fetchEvidenceLinks, fetchEvidenceSources } from "../services/api";
import { formatStatus, humanizeTechnicalValue } from "../utils/formatters";

export default function Evidence() {
  const { can } = useAuth();
  const { t } = useTranslation();
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
    mutationFn: () => createEvidenceSource({ source_type: "other", title: sourceForm.title, identifier: sourceForm.identifier, url: sourceForm.url || null, jurisdiction: "BR-demo", source_version: "demo-v1", license_metadata: { review_required: true }, provenance: { origin: "manual", copied_full_text: false } }),
    onSuccess: async (source) => { setSourceForm({ title: "", identifier: "", url: "" }); setLinkForm((current) => ({ ...current, source_id: source.id })); await refresh(); },
  });
  const linkMutation = useMutation({
    mutationFn: () => createEvidenceLink(linkForm),
    onSuccess: async () => { setLinkForm((current) => ({ ...current, target_id: "", locator: "" })); await refresh(); },
  });

  if (sources.isLoading || links.isLoading) return <LoadingState label={t("evidence.loading")} />;
  if (sources.isError || links.isError) return <StatusPanel title={t("evidence.errorTitle")} tone="danger">{t("evidence.errorBody")}</StatusPanel>;

  return (
    <div className="grid gap-6 lg:gap-8">
      <PageHeader title={t("evidence.title")} description={t("evidence.description")} actions={<Badge tone="warning">{t("evidence.humanReview")}</Badge>} />
      <section className="grid gap-6 xl:grid-cols-2">
        <div className="surface-card p-5">
          <div className="flex items-center justify-between"><div className="flex items-center gap-2"><BookOpenCheck aria-hidden="true" className="h-5 w-5 text-ocean" /><h2 className="text-lg font-black">{t("evidence.sources")}</h2></div><Badge>{sources.data?.length ?? 0}</Badge></div>
          <div className="mt-4 grid gap-3">{sources.data?.map((source) => <article className="rounded-xl border border-slate-200 p-4" key={source.id}><div className="flex flex-wrap justify-between gap-2"><h3 className="font-extrabold">{source.title}</h3><Badge tone="warning">{formatStatus(source.review_status)}</Badge></div><p className="mt-1 text-xs text-slate-500">{humanizeTechnicalValue(source.source_type)} · <code>{source.identifier}</code> · {source.jurisdiction ?? t("evidence.noJurisdiction")}</p></article>)}{!sources.data?.length ? <p className="text-sm text-slate-500">{t("evidence.noSources")}</p> : null}</div>
        </div>
        <div className="surface-card p-5">
          <div className="flex items-center justify-between"><div className="flex items-center gap-2"><Link2 aria-hidden="true" className="h-5 w-5 text-ocean" /><h2 className="text-lg font-black">{t("evidence.links")}</h2></div><Badge>{links.data?.length ?? 0}</Badge></div>
          <div className="mt-4 grid gap-3">{links.data?.map((link) => <article className="rounded-xl border border-slate-200 p-4" key={link.id}><p className="font-extrabold">{formatStatus(link.relationship)}</p><p className="mt-1 text-xs text-slate-500"><code>{link.target_type}:{link.target_id}</code> · {link.locator || t("evidence.noLocator")}</p></article>)}{!links.data?.length ? <p className="text-sm text-slate-500">{t("evidence.noLinks")}</p> : null}</div>
        </div>
      </section>
      {can("evidence.write") ? (
        <section className="grid gap-6 xl:grid-cols-2">
          <form className="surface-card grid gap-3 p-5" onSubmit={(event) => { event.preventDefault(); sourceMutation.mutate(); }}><h2 className="font-black">{t("evidence.registerSource")}</h2><input aria-label={t("evidence.sourceTitle")} className="field" onChange={(event) => setSourceForm({ ...sourceForm, title: event.target.value })} placeholder={t("evidence.sourceTitle")} value={sourceForm.title} /><input aria-label={t("evidence.sourceIdentifier")} className="field" onChange={(event) => setSourceForm({ ...sourceForm, identifier: event.target.value })} placeholder={t("evidence.identifier")} value={sourceForm.identifier} /><input aria-label={t("evidence.url")} className="field" onChange={(event) => setSourceForm({ ...sourceForm, url: event.target.value })} placeholder={t("evidence.url")} value={sourceForm.url} /><button className="btn-primary" disabled={sourceMutation.isPending || sourceForm.title.length < 4 || sourceForm.identifier.length < 3} type="submit"><Plus aria-hidden="true" className="h-4 w-4" />{t("evidence.register")}</button></form>
          <form className="surface-card grid gap-3 p-5" onSubmit={(event) => { event.preventDefault(); linkMutation.mutate(); }}><h2 className="font-black">{t("evidence.linkSource")}</h2><select aria-label={t("evidence.source")} className="field" onChange={(event) => setLinkForm({ ...linkForm, source_id: event.target.value })} value={linkForm.source_id}><option value="">{t("evidence.select")}</option>{sources.data?.map((source) => <option key={source.id} value={source.id}>{source.title}</option>)}</select><select aria-label={t("evidence.targetType")} className="field" onChange={(event) => setLinkForm({ ...linkForm, target_type: event.target.value })} value={linkForm.target_type}>{["study", "protocol", "outcome", "concept_set", "medication", "dose_rule", "clinical_finding"].map((item) => <option key={item} value={item}>{humanizeTechnicalValue(item)}</option>)}</select><input aria-label={t("evidence.targetId")} className="field" onChange={(event) => setLinkForm({ ...linkForm, target_id: event.target.value })} placeholder={t("evidence.targetId")} value={linkForm.target_id} /><input aria-label={t("evidence.locator")} className="field" onChange={(event) => setLinkForm({ ...linkForm, locator: event.target.value })} placeholder={t("evidence.locator")} value={linkForm.locator} /><button className="btn-primary" disabled={linkMutation.isPending || !linkForm.source_id || !linkForm.target_id} type="submit">{t("evidence.createLink")}</button></form>
        </section>
      ) : null}
    </div>
  );
}
