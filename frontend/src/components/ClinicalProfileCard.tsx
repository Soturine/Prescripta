import { ClipboardList } from "lucide-react";

import type { Patient } from "../types/patient";
import { formatClinicalValue } from "../utils/clinicalVocabulary";
import { formatDateTime, joinList } from "../utils/formatters";

type ClinicalProfileCardProps = {
  patient: Patient;
};

export default function ClinicalProfileCard({ patient }: ClinicalProfileCardProps) {
  const rows = [
    ["Condicao renal", formatClinicalValue(patient.renal_condition)],
    ["Condicao hepatica", formatClinicalValue(patient.hepatic_condition)],
    ["Risco cardiovascular", formatClinicalValue(patient.cardiac_condition)],
    ["Historico gastrointestinal", formatClinicalValue(patient.gastrointestinal_history)],
    ["Hipertensao", patient.hypertension ? "Sim" : "Nao"],
    ["Diabetes", patient.diabetes ? "Sim" : "Nao"],
    [
      "Gravidez/lactacao",
      patient.pregnancy_or_lactation === null ? "-" : patient.pregnancy_or_lactation ? "Sim" : "Nao",
    ],
    ["Reacoes adversas", joinList(patient.adverse_reactions) || "-"],
  ];

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-cyan-50 text-ocean">
            <ClipboardList aria-hidden="true" className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-ink">Perfil clinico inteligente</h2>
            <p className="mt-1 text-sm text-slate-600">
              {patient.clinical_profile_badge} · {patient.clinical_profile_completeness_score}%
            </p>
          </div>
        </div>
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        {rows.map(([label, value]) => (
          <div key={label} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <dt className="label">{label}</dt>
            <dd className="mt-1 font-semibold text-ink">{value || "-"}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 text-xs font-medium text-slate-500">
        Ultima revisao:{" "}
        {patient.clinical_profile_reviewed_at
          ? formatDateTime(patient.clinical_profile_reviewed_at)
          : "nao registrada"}
      </p>
    </section>
  );
}
