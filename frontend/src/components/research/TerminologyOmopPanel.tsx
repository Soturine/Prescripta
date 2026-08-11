import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Database, Search } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import {
  executeOmopAdapter,
  fetchOmopCompatibility,
  fetchOmopRuns,
  fetchTerminologyMappings,
  fetchTerminologyReleases,
  fetchTerminologySources,
  reviewTerminologyMapping,
  searchTerminologyConcepts,
} from "../../services/api";
import Badge from "../ui/Badge";
import StatusPanel from "../ui/StatusPanel";

type Props = {
  area: "terminology" | "omop";
  studyId: string;
  cohortRunId?: string;
  canReadTerminology: boolean;
  canReviewMappings: boolean;
  canPreviewOmop: boolean;
  canExportOmop: boolean;
};

export default function TerminologyOmopPanel(props: Props) {
  const { t } = useTranslation();
  const client = useQueryClient();
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");

  const sources = useQuery({
    queryKey: ["terminology-sources"],
    queryFn: fetchTerminologySources,
    enabled: props.canReadTerminology,
  });
  const releases = useQuery({
    queryKey: ["terminology-releases"],
    queryFn: () => fetchTerminologyReleases(),
    enabled: props.canReadTerminology,
  });
  const concepts = useQuery({
    queryKey: ["terminology-concepts", submittedQuery],
    queryFn: () => searchTerminologyConcepts({ query: submittedQuery, active_only: true }),
    enabled: props.canReadTerminology,
  });
  const mappings = useQuery({
    queryKey: ["terminology-mappings"],
    queryFn: () => fetchTerminologyMappings(),
    enabled: props.canReadTerminology,
  });
  const compatibility = useQuery({
    queryKey: ["omop-compatibility"],
    queryFn: fetchOmopCompatibility,
    enabled: props.canPreviewOmop,
  });
  const runs = useQuery({
    queryKey: ["omop-runs"],
    queryFn: fetchOmopRuns,
    enabled: props.canPreviewOmop,
  });
  const action = useMutation({
    mutationFn: (mode: "preview" | "exports") => {
      if (!props.cohortRunId) throw new Error("cohort_run_required");
      return executeOmopAdapter(mode, {
        study_id: props.studyId,
        cohort_run_id: props.cohortRunId,
        terminology_release_ids: (releases.data ?? [])
          .filter((item) => item.status === "imported")
          .map((item) => item.id),
      });
    },
    onSuccess: () => client.invalidateQueries({ queryKey: ["omop-runs"] }),
  });
  const review = useMutation({
    mutationFn: (id: string) =>
      reviewTerminologyMapping(id, "approved_for_demo", t("research.terminology.reviewNote")),
    onSuccess: () => client.invalidateQueries({ queryKey: ["terminology-mappings"] }),
  });

  if (props.area === "terminology") {
    if (!props.canReadTerminology) {
      return <StatusPanel title={t("research.terminology.denied")} tone="warning">{t("research.terminology.deniedBody")}</StatusPanel>;
    }
    return (
      <section className="grid gap-4">
        <StatusPanel title={t("research.terminology.title")} tone="info">
          {t("research.terminology.notice")}
        </StatusPanel>
        <div className="grid gap-4 xl:grid-cols-2">
          <div className="surface-card p-5">
            <h2 className="font-black">{t("research.terminology.registry")}</h2>
            <div className="mt-4 grid gap-3">
              {(sources.data ?? []).map((source) => (
                <div className="rounded-xl border border-slate-200 p-3" key={source.id}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <strong>{source.public_name}</strong><Badge>{source.family}</Badge>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">{source.steward} · {source.canonical_system}</p>
                </div>
              ))}
              {!sources.data?.length ? <p className="text-sm text-slate-500">{t("research.terminology.emptyRegistry")}</p> : null}
            </div>
          </div>
          <div className="surface-card p-5">
            <h2 className="font-black">{t("research.terminology.releases")}</h2>
            <div className="mt-4 grid gap-3">
              {(releases.data ?? []).map((release) => (
                <div className="rounded-xl border border-slate-200 p-3" key={release.id}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <strong>{release.version}</strong>
                    <Badge tone={release.license_status === "authorized" ? "success" : "warning"}>{release.license_status}</Badge>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">{release.license_name} · SHA-256 {release.source_checksum.slice(0, 12)}…</p>
                </div>
              ))}
              {!releases.data?.length ? <p className="text-sm text-slate-500">{t("research.terminology.emptyReleases")}</p> : null}
            </div>
          </div>
        </div>
        <div className="surface-card p-5">
          <h2 className="font-black">{t("research.terminology.search")}</h2>
          <form className="mt-3 flex gap-2" onSubmit={(event) => { event.preventDefault(); setSubmittedQuery(query.trim()); }}>
            <input className="field min-w-0 flex-1" onChange={(event) => setQuery(event.target.value)} value={query} />
            <button className="btn-secondary" type="submit"><Search aria-hidden="true" className="h-4 w-4" />{t("research.terminology.searchAction")}</button>
          </form>
          <p className="mt-2 text-xs text-slate-500">{t("research.terminology.suggestionOnly")}</p>
          <div className="mt-4 grid gap-2">
            {(concepts.data?.items ?? []).map((concept) => (
              <div className="rounded-xl border border-slate-200 p-3" key={concept.id}>
                <strong>{concept.source_code} · {concept.display}</strong>
                <p className="text-xs text-slate-500">{concept.source_system} · {concept.domain} · {concept.standard_status}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="surface-card p-5">
          <h2 className="font-black">{t("research.terminology.mappingQueue")}</h2>
          <div className="mt-4 grid gap-3">
            {(mappings.data ?? []).map((mapping) => (
              <div className="rounded-xl border border-slate-200 p-3" key={mapping.id}>
                <div className="flex flex-wrap items-center justify-between gap-2"><strong>v{mapping.version} · {mapping.relationship_type}</strong><Badge>{mapping.status}</Badge></div>
                <p className="mt-1 text-xs text-slate-500">{mapping.mapping_hash.slice(0, 16)}… · {mapping.mapping_method}</p>
                {mapping.status === "proposed" && props.canReviewMappings ? <button className="btn-secondary mt-3" disabled={review.isPending} onClick={() => review.mutate(mapping.id)} type="button"><CheckCircle2 aria-hidden="true" className="h-4 w-4" />{t("research.terminology.approve")}</button> : null}
              </div>
            ))}
            {!mappings.data?.length ? <p className="text-sm text-slate-500">{t("research.terminology.emptyMappings")}</p> : null}
          </div>
        </div>
      </section>
    );
  }

  if (!props.canPreviewOmop) {
    return <StatusPanel title={t("research.omop.denied")} tone="warning">{t("research.omop.deniedBody")}</StatusPanel>;
  }
  return (
    <section className="grid gap-4">
      <StatusPanel title={t("research.omop.title")} tone="warning">{t("research.omop.notice")}</StatusPanel>
      <div className="surface-card p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div><h2 className="font-black">{t("research.omop.adapter")}</h2><p className="mt-1 text-sm text-slate-600">{t("research.omop.adapterBody")}</p></div>
          <div className="flex gap-2">
            <button className="btn-secondary" disabled={!props.cohortRunId || action.isPending} onClick={() => action.mutate("preview")} type="button"><Database aria-hidden="true" className="h-4 w-4" />{t("research.omop.preview")}</button>
            {props.canExportOmop ? <button className="btn-primary" disabled={!props.cohortRunId || action.isPending} onClick={() => action.mutate("exports")} type="button">{t("research.omop.export")}</button> : null}
          </div>
        </div>
        {!props.cohortRunId ? <p className="mt-3 text-sm font-bold text-amber-700">{t("research.omop.runRequired")}</p> : null}
      </div>
      <div className="surface-card overflow-x-auto p-5">
        <h2 className="font-black">{t("research.omop.compatibility")}</h2>
        <table className="mt-4 w-full min-w-[720px] text-left text-sm"><thead><tr><th className="p-2">{t("research.omop.target")}</th><th className="p-2">{t("research.omop.level")}</th><th className="p-2">{t("research.omop.proven")}</th><th className="p-2">{t("research.omop.missing")}</th></tr></thead><tbody>{(compatibility.data?.targets ?? []).map((item) => <tr className="border-t border-slate-200" key={item.target}><td className="p-2 font-bold">{item.target}</td><td className="p-2"><Badge>{item.level}</Badge></td><td className="p-2">{item.proven}</td><td className="p-2">{item.missing}</td></tr>)}</tbody></table>
      </div>
      <div className="surface-card p-5">
        <h2 className="font-black">{t("research.omop.history")}</h2>
        <div className="mt-4 grid gap-3">{(runs.data ?? []).map((run) => <div className="rounded-xl border border-slate-200 p-3" key={run.id}><div className="flex flex-wrap justify-between gap-2"><strong>{run.status} · CDM {run.cdm_version}</strong><Badge tone="warning">{t("research.synthetic")}</Badge></div><p className="mt-1 text-xs text-slate-500">{run.source_snapshot_marker} · {run.export_hash.slice(0, 16)}…</p></div>)}</div>
      </div>
    </section>
  );
}
