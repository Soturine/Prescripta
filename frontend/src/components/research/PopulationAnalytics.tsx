import { ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";

import AttritionFlow from "./AttritionFlow";
import type { AnalysisRun, CohortRun } from "../../types/research";
import ChartFrame from "../ui/ChartFrame";

type NumericSummary = {
  n?: number;
  missing?: number;
  mean?: string | null;
  sd?: string | null;
  median?: string | null;
  q1?: string | null;
  q3?: string | null;
  iqr?: string | null;
  min?: string | null;
  max?: string | null;
};

type Category = {
  value: string;
  n: number | null;
  percent: string | null;
  suppressed: boolean;
};

export default function PopulationAnalytics({
  cohortRun,
  analysisRun,
}: {
  cohortRun?: CohortRun;
  analysisRun?: AnalysisRun;
}) {
  const { t } = useTranslation();
  if (!cohortRun) {
    return (
      <p className="text-sm text-slate-500">
        {t("research.analytics.executeFirst")}
      </p>
    );
  }
  const source = (analysisRun?.results ?? cohortRun.analytics) as Record<
    string,
    unknown
  >;
  const numeric = (source.numeric ?? {}) as Record<string, NumericSummary>;
  const categorical = (source.categorical ?? {}) as Record<
    string,
    { categories?: Category[]; missing?: number; small_cell_threshold?: number }
  >;
  const age = numeric.age_years;
  const sex = categorical.sex;
  const categories = sex?.categories ?? [];

  return (
    <div className="grid gap-5">
      <section
        aria-label={t("research.analytics.summary")}
        className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
      >
        <Metric
          label={t("research.analytics.population")}
          value={`N = ${cohortRun.result_count}`}
        />
        <Metric
          label={t("research.analytics.meanAge")}
          value={age?.mean ?? "—"}
        />
        <Metric
          label={t("research.analytics.medianAge")}
          value={age?.median ?? "—"}
        />
        <Metric
          label={t("research.analytics.missingAge")}
          value={String(age?.missing ?? 0)}
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 p-4">
          <ChartFrame
            description={t("research.analytics.chartDescription")}
            fallback={<table className="w-full text-left text-sm"><caption className="sr-only">{t("research.analytics.chartFallback")}</caption><thead><tr><th className="p-2">{t("research.analytics.category")}</th><th className="p-2">N</th><th className="p-2">%</th></tr></thead><tbody>{categories.map((item) => <tr className="border-t" key={`${item.value}-fallback`}><th className="p-2" scope="row">{item.value}</th><td className="p-2">{item.suppressed ? t("research.analytics.suppressed") : item.n}</td><td className="p-2">{item.suppressed ? "—" : item.percent}</td></tr>)}</tbody></table>}
            title={t("research.analytics.categorical")}
          >
          <div className="grid gap-3">
            {categories.map((item) => {
              const width = Math.max(2, Number(item.percent ?? 0));
              return (
                <div key={item.value}>
                  <div className="flex justify-between gap-3 text-sm">
                    <span>{item.value}</span>
                    <strong>
                      {item.suppressed
                        ? t("research.analytics.suppressed")
                        : `${item.n} (${item.percent}%)`}
                    </strong>
                  </div>
                  <div className="mt-1 h-3 rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-ocean"
                      style={{ width: `${width}%` }}
                    />
                  </div>
                </div>
              );
            })}
            {!categories.length ? (
              <p className="text-sm text-slate-500">
                {t("research.analytics.noCategories")}
              </p>
            ) : null}
          </div>
          </ChartFrame>
        </div>

        <div className="rounded-2xl border border-slate-200 p-4">
          <h3 className="font-black">{t("research.analytics.table1")}</h3>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <caption className="sr-only">
                {t("research.analytics.tableCaption")}
              </caption>
              <thead>
                <tr>
                  <th className="p-2">{t("research.analytics.variable")}</th>
                  <th className="p-2">N</th>
                  <th className="p-2">{t("research.analytics.missing")}</th>
                  <th className="p-2">
                    {t("research.analytics.tableSummary")}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t">
                  <td className="p-2 font-bold">
                    {t("research.analytics.age")}
                  </td>
                  <td className="p-2">{age?.n ?? 0}</td>
                  <td className="p-2">{age?.missing ?? 0}</td>
                  <td className="p-2">
                    {age
                      ? t("research.analytics.ageSummary", {
                          mean: age.mean,
                          sd: age.sd,
                          median: age.median,
                          q1: age.q1,
                          q3: age.q3,
                        })
                      : "—"}
                  </td>
                </tr>
                <tr className="border-t">
                  <td className="p-2 font-bold">
                    {t("research.analytics.sex")}
                  </td>
                  <td className="p-2">
                    {cohortRun.result_count - (sex?.missing ?? 0)}
                  </td>
                  <td className="p-2">{sex?.missing ?? 0}</td>
                  <td className="p-2">
                    {t("research.analytics.suppressionNote")}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <AttritionFlow steps={cohortRun.attrition} />
      <div className="flex items-start gap-2 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-900">
        <ShieldCheck aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0" />
        <p>{t("research.analytics.safeguard")}</p>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-cyan-950/10 bg-white p-4">
      <p className="text-2xl font-black text-ink">{value}</p>
      <p className="mt-1 text-xs font-bold uppercase tracking-wide text-slate-500">
        {label}
      </p>
    </div>
  );
}
