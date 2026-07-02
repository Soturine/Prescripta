import { useQuery } from "@tanstack/react-query";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import RiskBadge from "../components/RiskBadge";
import { fetchAudit } from "../services/api";
import { formatDateTime, formatDose } from "../utils/formatters";

export default function Audit() {
  const { data: records = [], isLoading } = useQuery({
    queryKey: ["audit"],
    queryFn: fetchAudit,
  });

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Auditoria</h1>
      </header>

      {isLoading ? <LoadingState label="Carregando auditoria" /> : null}
      {!isLoading && records.length === 0 ? (
        <EmptyState title="Nenhuma checagem registrada" />
      ) : null}
      {!isLoading && records.length > 0 ? (
        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[920px] text-left text-sm">
              <thead className="bg-slate-50 text-xs font-bold uppercase tracking-normal text-slate-500">
                <tr>
                  <th className="px-4 py-3">Data</th>
                  <th className="px-4 py-3">Paciente</th>
                  <th className="px-4 py-3">Medicamento</th>
                  <th className="px-4 py-3">Dose</th>
                  <th className="px-4 py-3">Via</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Risco</th>
                  <th className="px-4 py-3">Alertas</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {records.map((record) => (
                  <tr key={record.id} className="text-slate-700">
                    <td className="px-4 py-3">{formatDateTime(record.checked_at)}</td>
                    <td className="px-4 py-3 font-semibold text-ink">{record.patient_name}</td>
                    <td className="px-4 py-3">{record.medication_name}</td>
                    <td className="px-4 py-3">
                      {formatDose(record.dose_mg)} x {record.frequency_per_day}
                    </td>
                    <td className="px-4 py-3">{record.route}</td>
                    <td className="px-4 py-3">
                      <RiskBadge status={record.status} />
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge level={record.risk_level} />
                    </td>
                    <td className="px-4 py-3">{record.alerts.length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
