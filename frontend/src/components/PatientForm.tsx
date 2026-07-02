import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Save } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { Patient, PatientPayload } from "../types/patient";
import { joinList, splitList } from "../utils/formatters";

const patientSchema = z
  .object({
    name: z.string().min(2, "Informe o nome."),
    birth_date: z.string().optional(),
    age: z.number().min(0).max(130).optional(),
    weight_kg: z.number().positive("Informe o peso."),
    height_cm: z.number().min(1).max(260).optional(),
    allergies: z.string().optional(),
    comorbidities: z.string().optional(),
    current_medications: z.string().optional(),
  })
  .refine((data) => data.age !== undefined || Boolean(data.birth_date), {
    message: "Informe idade ou data de nascimento.",
    path: ["age"],
  });

type PatientFormValues = z.infer<typeof patientSchema>;

type PatientFormProps = {
  initialPatient?: Patient;
  submitLabel: string;
  onSubmit: (payload: PatientPayload) => Promise<void> | void;
};

export default function PatientForm({ initialPatient, submitLabel, onSubmit }: PatientFormProps) {
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    reset,
  } = useForm<PatientFormValues>({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      name: initialPatient?.name ?? "",
      birth_date: initialPatient?.birth_date ?? "",
      age: initialPatient?.age ?? undefined,
      weight_kg: initialPatient?.weight_kg ?? 70,
      height_cm: initialPatient?.height_cm ?? undefined,
      allergies: joinList(initialPatient?.allergies),
      comorbidities: joinList(initialPatient?.comorbidities),
      current_medications: joinList(initialPatient?.current_medications),
    },
  });

  const Icon = initialPatient ? Save : Plus;

  async function submit(values: PatientFormValues) {
    await onSubmit({
      name: values.name,
      birth_date: values.birth_date || null,
      age: values.age ?? null,
      weight_kg: values.weight_kg,
      height_cm: values.height_cm ?? null,
      allergies: splitList(values.allergies ?? ""),
      comorbidities: splitList(values.comorbidities ?? ""),
      current_medications: splitList(values.current_medications ?? ""),
    });

    if (!initialPatient) {
      reset({
        name: "",
        birth_date: "",
        age: undefined,
        weight_kg: 70,
        height_cm: undefined,
        allergies: "",
        comorbidities: "",
        current_medications: "",
      });
    }
  }

  return (
    <form className="grid gap-4" onSubmit={handleSubmit(submit)}>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="label">Nome</span>
          <input className="field" {...register("name")} />
          {errors.name ? <span className="text-xs text-danger">{errors.name.message}</span> : null}
        </label>

        <label className="grid gap-1.5">
          <span className="label">Idade</span>
          <input
            className="field"
            min="0"
            type="number"
            {...register("age", {
              setValueAs: (value) => (value === "" ? undefined : Number(value)),
            })}
          />
          {errors.age ? <span className="text-xs text-danger">{errors.age.message}</span> : null}
        </label>

        <label className="grid gap-1.5">
          <span className="label">Data de nascimento</span>
          <input className="field" type="date" {...register("birth_date")} />
        </label>

        <label className="grid gap-1.5">
          <span className="label">Peso kg</span>
          <input
            className="field"
            min="0"
            step="0.1"
            type="number"
            {...register("weight_kg", { valueAsNumber: true })}
          />
          {errors.weight_kg ? (
            <span className="text-xs text-danger">{errors.weight_kg.message}</span>
          ) : null}
        </label>

        <label className="grid gap-1.5">
          <span className="label">Altura cm</span>
          <input
            className="field"
            min="0"
            step="0.1"
            type="number"
            {...register("height_cm", {
              setValueAs: (value) => (value === "" ? undefined : Number(value)),
            })}
          />
        </label>

        <label className="grid gap-1.5">
          <span className="label">Alergias</span>
          <input className="field" {...register("allergies")} />
        </label>
      </div>

      <label className="grid gap-1.5">
        <span className="label">Comorbidades</span>
        <input className="field" {...register("comorbidities")} />
      </label>

      <label className="grid gap-1.5">
        <span className="label">Medicamentos contínuos</span>
        <input className="field" {...register("current_medications")} />
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
