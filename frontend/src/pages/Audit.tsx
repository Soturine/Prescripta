import { useQuery } from "@tanstack/react-query";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import RiskBadge from "../components/RiskBadge";
import { fetchAudit } from "../services/api";
import { formatAuditAction, formatDateTime, formatRole } from "../utils/formatters";

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
                  <th className="px-4 py-3">Usuário</th>
                  <th className="px-4 py-3">Perfil</th>
                  <th className="px-4 py-3">Ação</th>
                  <th className="px-4 py-3">Recurso</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Risco</th>
                  <th className="px-4 py-3">Detalhes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {records.map((record) => (
                  <tr key={record.id} className="text-slate-700">
                    <td className="px-4 py-3">{formatDateTime(record.created_at)}</td>
                    <td className="px-4 py-3 font-semibold text-ink">
                      {record.user_name ?? "-"}
                      <div className="text-xs font-normal text-slate-500">
                        {record.user_email ?? ""}
                      </div>
                    </td>
                    <td className="px-4 py-3">{formatRole(record.user_role)}</td>
                    <td className="px-4 py-3">{formatAuditAction(record.action)}</td>
                    <td className="px-4 py-3">
                      {record.resource_type}
                      {record.resource_id ? ` #${record.resource_id}` : ""}
                    </td>
                    <td className="px-4 py-3">
                      {record.status ? <RiskBadge status={record.status} /> : "-"}
                    </td>
                    <td className="px-4 py-3">
                      {record.risk_level ? <RiskBadge level={record.risk_level} /> : "-"}
                    </td>
                    <td className="px-4 py-3">
                      {record.details.patient_name || record.details.medication_name
                        ? [record.details.patient_name, record.details.medication_name]
                            .filter(Boolean)
                            .join(" · ")
                        : record.details.email?.toString() || record.details.name?.toString() || "-"}
                    </td>
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
