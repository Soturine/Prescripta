import { Activity, Save } from "lucide-react";
import { useEffect, useState } from "react";

import type {
  PatientFunctionalProfile,
  PatientFunctionalProfilePayload,
} from "../types/patient";

const booleanFields = [
  ["drives_regularly", "Dirige"],
  ["professional_driver", "Motorista profissional"],
  ["operates_machinery", "Opera maquinas"],
  ["works_at_height", "Trabalho em altura"],
  ["fall_risk_activity", "Atividade com queda"],
  ["night_shift", "Turno noturno"],
  ["caregiver_responsibility", "Cuidador responsavel"],
  ["high_attention_activity", "Alta atencao"],
  ["frequent_alcohol_use", "Alcool frequente"],
  ["history_of_falls", "Historico de quedas"],
  ["low_tolerance_to_sedation_or_dizziness", "Baixa tolerancia a tontura"],
] as const;

type BooleanField = (typeof booleanFields)[number][0];

type FunctionalProfileCardProps = {
  profile: PatientFunctionalProfile;
  canManage: boolean;
  isSaving: boolean;
  onSubmit: (payload: PatientFunctionalProfilePayload) => Promise<void> | void;
};

function selectValue(value: boolean | null) {
  if (value === true) {
    return "true";
  }
  if (value === false) {
    return "false";
  }
  return "unknown";
}

function booleanValue(value: string) {
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  return null;
}

export default function FunctionalProfileCard({
  profile,
  canManage,
  isSaving,
  onSubmit,
}: FunctionalProfileCardProps) {
  const [values, setValues] = useState<Record<BooleanField, string>>(() =>
    Object.fromEntries(
      booleanFields.map(([field]) => [field, selectValue(profile[field])]),
    ) as Record<BooleanField, string>,
  );
  const [notes, setNotes] = useState(profile.notes ?? "");

  useEffect(() => {
    setValues(
      Object.fromEntries(
        booleanFields.map(([field]) => [field, selectValue(profile[field])]),
      ) as Record<BooleanField, string>,
    );
    setNotes(profile.notes ?? "");
  }, [profile]);

  async function submit() {
    await onSubmit({
      ...Object.fromEntries(
        booleanFields.map(([field]) => [field, booleanValue(values[field])]),
      ),
      source: "manual",
      notes: notes || null,
      last_reviewed_at: null,
    } as PatientFunctionalProfilePayload);
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-cyan-50 text-ocean">
            <Activity aria-hidden="true" className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-ink">Perfil funcional</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              {profile.educational_notice}
            </p>
          </div>
        </div>
        <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
          {profile.unknown_fields.length} campos desconhecidos
        </span>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {booleanFields.map(([field, label]) => (
          <label className="grid gap-1.5" key={field}>
            <span className="label">{label}</span>
            <select
              className="field"
              disabled={!canManage}
              onChange={(event) =>
                setValues((current) => ({ ...current, [field]: event.target.value }))
              }
              value={values[field]}
            >
              <option value="unknown">Nao informado</option>
              <option value="true">Sim</option>
              <option value="false">Nao</option>
            </select>
          </label>
        ))}
      </div>

      <label className="mt-4 grid gap-1.5">
        <span className="label">Notas</span>
        <textarea
          className="field min-h-20 resize-y"
          disabled={!canManage}
          onChange={(event) => setNotes(event.target.value)}
          value={notes}
        />
      </label>

      {canManage ? (
        <div className="mt-4 flex justify-end">
          <button className="btn-primary" disabled={isSaving} onClick={submit} type="button">
            <Save aria-hidden="true" className="h-4 w-4" />
            {isSaving ? "Salvando..." : "Salvar perfil funcional"}
          </button>
        </div>
      ) : null}
    </section>
  );
}
