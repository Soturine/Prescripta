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
  allowed_routes: z.string().min(2, "Informe ao menos uma via."),
  contraindications: z.string().optional(),
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
      allowed_routes: joinList(initialMedication?.allowed_routes),
      contraindications: joinList(initialMedication?.contraindications),
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
      allowed_routes: splitList(values.allowed_routes),
      contraindications: splitList(values.contraindications ?? ""),
      notes: values.notes || null,
    });

    if (!initialMedication) {
      reset({
        brand_name: "",
        active_ingredient: "",
        therapeutic_class: "",
        max_daily_dose_mg: 1000,
        allowed_routes: "",
        contraindications: "",
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
