import { zodResolver } from "@hookform/resolvers/zod";
import { ClipboardCheck } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { Medication } from "../types/medication";
import type { Patient } from "../types/patient";
import type { PrescriptionCheckPayload } from "../types/prescription";

const prescriptionSchema = z.object({
  patient_id: z.number().int().positive(),
  medication_id: z.number().int().positive(),
  dose_mg: z.number().positive("Informe a dose."),
  frequency_per_day: z.number().int().positive().max(24),
  route: z.string().min(2, "Informe a via."),
});

type PrescriptionFormValues = z.infer<typeof prescriptionSchema>;

type PrescriptionFormProps = {
  patients: Patient[];
  medications: Medication[];
  onSubmit: (payload: PrescriptionCheckPayload) => Promise<void> | void;
  disabled?: boolean;
};

export default function PrescriptionForm({
  patients,
  medications,
  onSubmit,
  disabled,
}: PrescriptionFormProps) {
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    reset,
  } = useForm<PrescriptionFormValues>({
    resolver: zodResolver(prescriptionSchema),
    defaultValues: {
      patient_id: patients[0]?.id ?? 0,
      medication_id: medications[0]?.id ?? 0,
      dose_mg: 100,
      frequency_per_day: 1,
      route: "oral",
    },
  });

  useEffect(() => {
    reset((values) => ({
      ...values,
      patient_id: values.patient_id || patients[0]?.id || 0,
      medication_id: values.medication_id || medications[0]?.id || 0,
    }));
  }, [medications, patients, reset]);

  return (
    <form className="grid gap-4" onSubmit={handleSubmit(onSubmit)}>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="label">Paciente</span>
          <select
            className="field"
            disabled={disabled}
            {...register("patient_id", { valueAsNumber: true })}
          >
            <option value={0}>Selecione</option>
            {patients.map((patient) => (
              <option key={patient.id} value={patient.id}>
                {patient.name}
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-1.5">
          <span className="label">Medicamento</span>
          <select
            className="field"
            disabled={disabled}
            {...register("medication_id", { valueAsNumber: true })}
          >
            <option value={0}>Selecione</option>
            {medications.map((medication) => (
              <option key={medication.id} value={medication.id}>
                {medication.brand_name} - {medication.active_ingredient}
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-1.5">
          <span className="label">Dose mg</span>
          <input
            className="field"
            disabled={disabled}
            min="0"
            step="0.1"
            type="number"
            {...register("dose_mg", { valueAsNumber: true })}
          />
          {errors.dose_mg ? (
            <span className="text-xs text-danger">{errors.dose_mg.message}</span>
          ) : null}
        </label>

        <label className="grid gap-1.5">
          <span className="label">Frequência por dia</span>
          <input
            className="field"
            disabled={disabled}
            min="1"
            type="number"
            {...register("frequency_per_day", { valueAsNumber: true })}
          />
        </label>

        <label className="grid gap-1.5 md:col-span-2">
          <span className="label">Via</span>
          <input className="field" disabled={disabled} {...register("route")} />
          {errors.route ? (
            <span className="text-xs text-danger">{errors.route.message}</span>
          ) : null}
        </label>
      </div>

      <div className="flex justify-end">
        <button
          className="btn-primary"
          disabled={disabled || isSubmitting}
          title="Verificar prescrição"
          type="submit"
        >
          <ClipboardCheck aria-hidden="true" className="h-4 w-4" />
          Verificar prescrição
        </button>
      </div>
    </form>
  );
}
