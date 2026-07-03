import { zodResolver } from "@hookform/resolvers/zod";
import { Save } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { QuickTriagePayload } from "../types/patient";
import { splitList } from "../utils/formatters";

const triageSchema = z.object({
  renal_condition: z.boolean(),
  hepatic_condition: z.boolean(),
  cardiac_condition: z.boolean(),
  gastrointestinal_history: z.boolean(),
  hypertension: z.boolean(),
  diabetes: z.boolean(),
  pregnancy_or_lactation: z.boolean(),
  allergies: z.string().optional(),
  current_medications: z.string().optional(),
  adverse_reactions: z.string().optional(),
  condition_to_review: z.string().optional(),
  clinical_notes: z.string().optional(),
});

type QuickTriageValues = z.infer<typeof triageSchema>;

type QuickTriageFormProps = {
  onSubmit: (payload: QuickTriagePayload) => Promise<void> | void;
};

export default function QuickTriageForm({ onSubmit }: QuickTriageFormProps) {
  const {
    formState: { isSubmitting },
    handleSubmit,
    register,
    reset,
  } = useForm<QuickTriageValues>({
    resolver: zodResolver(triageSchema),
    defaultValues: {
      renal_condition: false,
      hepatic_condition: false,
      cardiac_condition: false,
      gastrointestinal_history: false,
      hypertension: false,
      diabetes: false,
      pregnancy_or_lactation: false,
      allergies: "",
      current_medications: "",
      adverse_reactions: "",
      condition_to_review: "",
      clinical_notes: "",
    },
  });

  async function submit(values: QuickTriageValues) {
    await onSubmit({
      renal_condition: values.renal_condition,
      hepatic_condition: values.hepatic_condition,
      cardiac_condition: values.cardiac_condition,
      gastrointestinal_history: values.gastrointestinal_history,
      hypertension: values.hypertension,
      diabetes: values.diabetes,
      pregnancy_or_lactation: values.pregnancy_or_lactation,
      allergies: splitList(values.allergies ?? ""),
      current_medications: splitList(values.current_medications ?? ""),
      adverse_reactions: splitList(values.adverse_reactions ?? ""),
      condition_to_review: values.condition_to_review || null,
      clinical_notes: values.clinical_notes || null,
    });
    reset();
  }

  const toggles = [
    ["renal_condition", "Possui problema nos rins?"],
    ["hepatic_condition", "Possui problema no fígado?"],
    ["cardiac_condition", "Possui problema cardíaco?"],
    ["gastrointestinal_history", "Histórico de gastrite, úlcera ou sangramento?"],
    ["hypertension", "Possui pressão alta?"],
    ["diabetes", "Possui diabetes?"],
    ["pregnancy_or_lactation", "Está grávida ou amamentando?"],
  ] as const;

  return (
    <form className="grid gap-4" onSubmit={handleSubmit(submit)}>
      <div className="grid gap-3 md:grid-cols-2">
        {toggles.map(([field, label]) => (
          <label
            className="flex min-h-11 items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700"
            key={field}
          >
            <input className="h-4 w-4 accent-ocean" type="checkbox" {...register(field)} />
            {label}
          </label>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="label">Alergias ou reações ruins</span>
          <input className="field" {...register("allergies")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Medicamentos contínuos</span>
          <input className="field" {...register("current_medications")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Efeitos colaterais importantes</span>
          <input className="field" {...register("adverse_reactions")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Condição para revisar</span>
          <input className="field" {...register("condition_to_review")} />
        </label>
      </div>
      <label className="grid gap-1.5">
        <span className="label">Observações clínicas relevantes</span>
        <textarea className="field min-h-20 resize-y" {...register("clinical_notes")} />
      </label>
      <div className="flex justify-end">
        <button className="btn-primary" disabled={isSubmitting} type="submit">
          <Save aria-hidden="true" className="h-4 w-4" />
          Salvar triagem rápida
        </button>
      </div>
    </form>
  );
}
