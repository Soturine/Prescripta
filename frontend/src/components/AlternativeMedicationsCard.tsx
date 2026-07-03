import RiskBadge from "./RiskBadge";
import type { AlternativeMedication } from "../types/prescription";

export default function AlternativeMedicationsCard({
  alternatives,
}: {
  alternatives: AlternativeMedication[];
}) {
  if (!alternatives.length) {
    return null;
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-bold text-ink">Alternativas para avaliação profissional</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="bg-slate-50 text-xs font-bold uppercase tracking-normal text-slate-500">
            <tr>
              <th className="px-4 py-3">Medicamento</th>
              <th className="px-4 py-3">Semelhança</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Risco</th>
              <th className="px-4 py-3">Observação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {alternatives.map((item) => (
              <tr key={item.medication_id}>
                <td className="px-4 py-3 font-semibold text-ink">
                  {item.name}
                  <div className="text-xs font-normal text-slate-500">{item.active_ingredient}</div>
                </td>
                <td className="px-4 py-3">{item.similarity_reason}</td>
                <td className="px-4 py-3"><RiskBadge status={item.status} /></td>
                <td className="px-4 py-3"><RiskBadge level={item.risk_level} /></td>
                <td className="px-4 py-3">{item.observation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
