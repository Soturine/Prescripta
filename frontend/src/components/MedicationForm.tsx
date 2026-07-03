import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Save } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { Medication, MedicationPayload } from "../types/medication";
import { joinList, splitList } from "../utils/formatters";

const medicationSchema = z.object({
  brand_name: z.string().min(2, "Informe o nome comercial."),
  active_ingredient: z.string().min(2, "Informe o princípio ativo."),
  therapeutic_class: z.string().min(2, "Informe a classe."),
  max_daily_dose_mg: z.number().positive("Informe a dose máxima."),
  max_duration_days: z.number().positive().optional(),
  max_cumulative_dose_mg: z.number().positive().optional(),
  condition_specific_limits: z.string().optional(),
  allowed_routes: z.string().min(2, "Informe ao menos uma via."),
  contraindications: z.string().optional(),
  renal_caution: z.boolean(),
  hepatic_caution: z.boolean(),
  cardiac_caution: z.boolean(),
  gastrointestinal_caution: z.boolean(),
  elderly_caution: z.boolean(),
  metabolism_organs: z.string().optional(),
  elimination_organs: z.string().optional(),
  organs_involved: z.string().optional(),
  relevant_adverse_effects: z.string().optional(),
  structured_contraindications: z.string().optional(),
  therapeutic_action: z.string().optional(),
  alternative_group: z.string().optional(),
  related_medications: z.string().optional(),
  knowledge_source: z.string().optional(),
  notes: z.string().optional(),
});

type MedicationFormValues = z.infer<typeof medicationSchema>;

type MedicationFormProps = {
  initialMedication?: Medication;
  submitLabel: string;
  onSubmit: (payload: MedicationPayload) => Promise<void> | void;
};

export default function MedicationForm({
  initialMedication,
  submitLabel,
  onSubmit,
}: MedicationFormProps) {
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    reset,
  } = useForm<MedicationFormValues>({
    resolver: zodResolver(medicationSchema),
    defaultValues: {
      brand_name: initialMedication?.brand_name ?? "",
      active_ingredient: initialMedication?.active_ingredient ?? "",
      therapeutic_class: initialMedication?.therapeutic_class ?? "",
      max_daily_dose_mg: initialMedication?.max_daily_dose_mg ?? 1000,
      max_duration_days: initialMedication?.max_duration_days ?? undefined,
      max_cumulative_dose_mg: initialMedication?.max_cumulative_dose_mg ?? undefined,
      condition_specific_limits: formatLimits(initialMedication?.condition_specific_limits),
      allowed_routes: joinList(initialMedication?.allowed_routes),
      contraindications: joinList(initialMedication?.contraindications),
      renal_caution: initialMedication?.renal_caution ?? false,
      hepatic_caution: initialMedication?.hepatic_caution ?? false,
      cardiac_caution: initialMedication?.cardiac_caution ?? false,
      gastrointestinal_caution: initialMedication?.gastrointestinal_caution ?? false,
      elderly_caution: initialMedication?.elderly_caution ?? false,
      metabolism_organs: joinList(initialMedication?.metabolism_organs),
      elimination_organs: joinList(initialMedication?.elimination_organs),
      organs_involved: joinList(initialMedication?.organs_involved),
      relevant_adverse_effects: joinList(initialMedication?.relevant_adverse_effects),
      structured_contraindications: joinList(initialMedication?.structured_contraindications),
      therapeutic_action: initialMedication?.therapeutic_action ?? "",
      alternative_group: initialMedication?.alternative_group ?? "",
      related_medications: joinList(initialMedication?.related_medications),
      knowledge_source: initialMedication?.knowledge_source ?? "",
      notes: initialMedication?.notes ?? "",
    },
  });

  const Icon = initialMedication ? Save : Plus;

  async function submit(values: MedicationFormValues) {
    await onSubmit({
      brand_name: values.brand_name,
      active_ingredient: values.active_ingredient,
      therapeutic_class: values.therapeutic_class,
      max_daily_dose_mg: values.max_daily_dose_mg,
      max_duration_days: values.max_duration_days ?? null,
      max_cumulative_dose_mg: values.max_cumulative_dose_mg ?? null,
      condition_specific_limits: parseLimits(values.condition_specific_limits ?? ""),
      allowed_routes: splitList(values.allowed_routes),
      contraindications: splitList(values.contraindications ?? ""),
      renal_caution: values.renal_caution,
      hepatic_caution: values.hepatic_caution,
      cardiac_caution: values.cardiac_caution,
      gastrointestinal_caution: values.gastrointestinal_caution,
      elderly_caution: values.elderly_caution,
      metabolism_organs: splitList(values.metabolism_organs ?? ""),
      elimination_organs: splitList(values.elimination_organs ?? ""),
      organs_involved: splitList(values.organs_involved ?? ""),
      relevant_adverse_effects: splitList(values.relevant_adverse_effects ?? ""),
      structured_contraindications: splitList(values.structured_contraindications ?? ""),
      therapeutic_action: values.therapeutic_action || null,
      alternative_group: values.alternative_group || null,
      related_medications: splitList(values.related_medications ?? ""),
      knowledge_source: values.knowledge_source || null,
      notes: values.notes || null,
    });

    if (!initialMedication) {
      reset({
        brand_name: "",
        active_ingredient: "",
        therapeutic_class: "",
        max_daily_dose_mg: 1000,
        max_duration_days: undefined,
        max_cumulative_dose_mg: undefined,
        condition_specific_limits: "",
        allowed_routes: "",
        contraindications: "",
        renal_caution: false,
        hepatic_caution: false,
        cardiac_caution: false,
        gastrointestinal_caution: false,
        elderly_caution: false,
        metabolism_organs: "",
        elimination_organs: "",
        organs_involved: "",
        relevant_adverse_effects: "",
        structured_contraindications: "",
        therapeutic_action: "",
        alternative_group: "",
        related_medications: "",
        knowledge_source: "",
        notes: "",
      });
    }
  }

  return (
    <form className="grid gap-4" onSubmit={handleSubmit(submit)}>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="label">Nome comercial</span>
          <input className="field" {...register("brand_name")} />
          {errors.brand_name ? (
            <span className="text-xs text-danger">{errors.brand_name.message}</span>
          ) : null}
        </label>

        <label className="grid gap-1.5">
          <span className="label">Princípio ativo</span>
          <input className="field" {...register("active_ingredient")} />
          {errors.active_ingredient ? (
            <span className="text-xs text-danger">{errors.active_ingredient.message}</span>
          ) : null}
        </label>

        <label className="grid gap-1.5">
          <span className="label">Classe terapêutica</span>
          <input className="field" {...register("therapeutic_class")} />
          {errors.therapeutic_class ? (
            <span className="text-xs text-danger">{errors.therapeutic_class.message}</span>
          ) : null}
        </label>

        <label className="grid gap-1.5">
          <span className="label">Dose máxima diária mg</span>
          <input
            className="field"
            min="0"
            step="0.1"
            type="number"
            {...register("max_daily_dose_mg", { valueAsNumber: true })}
          />
          {errors.max_daily_dose_mg ? (
            <span className="text-xs text-danger">{errors.max_daily_dose_mg.message}</span>
          ) : null}
        </label>

        <label className="grid gap-1.5">
          <span className="label">Duração máxima dias</span>
          <input
            className="field"
            min="1"
            type="number"
            {...register("max_duration_days", {
              setValueAs: (value) => (value === "" ? undefined : Number(value)),
            })}
          />
        </label>

        <label className="grid gap-1.5">
          <span className="label">Dose acumulada máxima mg</span>
          <input
            className="field"
            min="0"
            step="0.1"
            type="number"
            {...register("max_cumulative_dose_mg", {
              setValueAs: (value) => (value === "" ? undefined : Number(value)),
            })}
          />
        </label>
      </div>

      <label className="grid gap-1.5">
        <span className="label">Limites por condição</span>
        <input className="field" placeholder="renal:1200, hepático:800" {...register("condition_specific_limits")} />
      </label>

      <div className="grid gap-3 md:grid-cols-3">
        {[
          ["renal_caution", "Cautela renal"],
          ["hepatic_caution", "Cautela hepática"],
          ["cardiac_caution", "Cautela cardíaca"],
          ["gastrointestinal_caution", "Cautela gastrointestinal"],
          ["elderly_caution", "Cautela em idosos"],
        ].map(([field, label]) => (
          <label
            className="flex min-h-11 items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700"
            key={field}
          >
            <input className="h-4 w-4 accent-ocean" type="checkbox" {...register(field as keyof MedicationFormValues)} />
            {label}
          </label>
        ))}
      </div>

      <label className="grid gap-1.5">
        <span className="label">Vias permitidas</span>
        <input className="field" {...register("allowed_routes")} />
        {errors.allowed_routes ? (
          <span className="text-xs text-danger">{errors.allowed_routes.message}</span>
        ) : null}
      </label>

      <label className="grid gap-1.5">
        <span className="label">Contraindicações</span>
        <input className="field" {...register("contraindications")} />
      </label>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="label">Metabolização/processamento</span>
          <input className="field" {...register("metabolism_organs")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Eliminação principal</span>
          <input className="field" {...register("elimination_organs")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Órgãos envolvidos</span>
          <input className="field" {...register("organs_involved")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Efeitos colaterais relevantes</span>
          <input className="field" {...register("relevant_adverse_effects")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Contraindicações estruturadas</span>
          <input className="field" {...register("structured_contraindications")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Ação/finalidade</span>
          <input className="field" {...register("therapeutic_action")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Grupo de alternativas</span>
          <input className="field" {...register("alternative_group")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Medicamentos relacionados</span>
          <input className="field" {...register("related_medications")} />
        </label>
      </div>

      <label className="grid gap-1.5">
        <span className="label">Fonte demonstrativa</span>
        <input className="field" {...register("knowledge_source")} />
      </label>

      <label className="grid gap-1.5">
        <span className="label">Observações</span>
        <textarea className="field min-h-24 resize-y" {...register("notes")} />
      </label>

      <div className="flex justify-end">
        <button className="btn-primary" disabled={isSubmitting} title={submitLabel} type="submit">
          <Icon aria-hidden="true" className="h-4 w-4" />
          {submitLabel}
        </button>
      </div>
    </form>
  );
}

function parseLimits(value: string) {
  return Object.fromEntries(
    value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
      .map((item) => {
        const [key, rawValue] = item.split(":");
        return [key?.trim() ?? "", Number(rawValue)];
      })
      .filter(([key, rawValue]) => key && Number.isFinite(rawValue)),
  );
}

function formatLimits(value: Record<string, number> | null | undefined) {
  return Object.entries(value ?? {})
    .map(([key, limit]) => `${key}:${limit}`)
    .join(", ");
}
