import { useTranslation } from "react-i18next";

import RiskBadge from "./RiskBadge";
import type { AlternativeMedication } from "../types/prescription";

export default function AlternativeMedicationsCard({
  alternatives,
}: {
  alternatives: AlternativeMedication[];
}) {
  const { t } = useTranslation();
  if (!alternatives.length) {
    return null;
  }

  return (
    <section
      aria-labelledby="alternatives-title"
      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
    >
      <h2 id="alternatives-title" className="text-lg font-bold text-ink">
        {t("alternatives.title")}
      </h2>
      <p className="mt-1 text-sm text-slate-600">{t("alternatives.notice")}</p>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="bg-slate-50 text-xs font-bold uppercase tracking-normal text-slate-500">
            <tr>
              <th scope="col" className="px-4 py-3">{t("alternatives.columns.medication")}</th>
              <th scope="col" className="px-4 py-3">{t("alternatives.columns.similarity")}</th>
              <th scope="col" className="px-4 py-3">{t("alternatives.columns.screening")}</th>
              <th scope="col" className="px-4 py-3">{t("alternatives.columns.risk")}</th>
              <th scope="col" className="px-4 py-3">{t("alternatives.columns.dose")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {alternatives.map((item) => (
              <tr key={item.medication_id}>
                <td className="px-4 py-3 font-semibold text-ink">
                  {item.name}
                  <div className="text-xs font-normal text-slate-500">{item.active_ingredient}</div>
                </td>
                <td className="px-4 py-3">
                  {item.similarity_kind
                    ? t(`alternatives.similarity.${item.similarity_kind}`)
                    : item.similarity_reason}
                </td>
                <td className="px-4 py-3">
                  {/* Nunca exibe "liberado": é triagem para revisão humana. */}
                  <RiskBadge status={item.status === "bloqueado" ? "bloqueado" : "atencao"} />
                  <div className="mt-1 text-xs text-slate-600">
                    {t(`alternatives.review.${item.review_status ?? "candidate_for_human_review"}`)}
                  </div>
                </td>
                <td className="px-4 py-3"><RiskBadge level={item.risk_level} /></td>
                <td className="px-4 py-3 text-slate-700">
                  {t(`alternatives.dose.${item.dose_assessment ?? "not_evaluated_for_alternative"}`)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
