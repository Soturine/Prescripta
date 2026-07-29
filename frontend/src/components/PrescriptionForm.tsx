import { zodResolver } from "@hookform/resolvers/zod";
import { Calculator, Check, ClipboardCheck, FlaskConical, Route, Timer } from "lucide-react";
import { useEffect } from "react";
import type { ReactNode } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";

import type { Medication } from "../types/medication";
import type { Patient } from "../types/patient";
import type { PrescriptionCheckPayload } from "../types/prescription";
import Badge from "./ui/Badge";

const optionalPositive = z.number().positive().optional();

const prescriptionSchema = z
  .object({
    patient_id: z.number().int().positive("Selecione um paciente autorizado."),
    medication_id: z.number().int().positive("Selecione um medicamento."),
    amount: z.number().positive("Informe uma quantidade maior que zero."),
    amount_unit: z.enum(["mg", "mcg", "g", "mL", "mg/kg", "mcg/kg", "mg/m2", "mcg/kg/min"]),
    administration_kind: z.enum(["bolus", "intermittent", "continuous", "prn"]),
    concentration_value: optionalPositive,
    concentration_unit: z.string().optional(),
    volume: optionalPositive,
    volume_unit: z.string().optional(),
    rate_value: optionalPositive,
    rate_unit: z.string().optional(),
    frequency_per_day: z.number().int().positive().max(96).optional(),
    interval_value: optionalPositive,
    interval_unit: z.string().optional(),
    duration_value: optionalPositive,
    duration_unit: z.string().optional(),
    route: z.string().min(2, "Informe a via."),
    site: z.string().optional(),
    procedure_context: z.string().optional(),
    max_administrations_per_day: z.number().int().positive().max(96).optional(),
    indication: z.string().optional(),
    professional_notes: z.string().max(1000).optional(),
  })
  .superRefine((data, context) => {
    const requirePair = (value: number | undefined, unit: string | undefined, path: string, label: string) => {
      if ((value === undefined) !== !unit) {
        context.addIssue({ code: "custom", message: `${label} exige valor e unidade.`, path: [path] });
      }
    };
    requirePair(data.concentration_value, data.concentration_unit, "concentration_value", "Concentração");
    requirePair(data.volume, data.volume_unit, "volume", "Volume");
    requirePair(data.rate_value, data.rate_unit, "rate_value", "Taxa");
    requirePair(data.interval_value, data.interval_unit, "interval_value", "Intervalo");
    requirePair(data.duration_value, data.duration_unit, "duration_value", "Duração");
    if (data.administration_kind === "continuous" && data.rate_value === undefined) {
      context.addIssue({ code: "custom", message: "Infusão contínua exige taxa explícita.", path: ["rate_value"] });
    }
    if (data.administration_kind === "intermittent" && data.frequency_per_day === undefined && data.interval_value === undefined) {
      context.addIssue({ code: "custom", message: "Informe frequência ou intervalo.", path: ["frequency_per_day"] });
    }
    if (data.administration_kind === "prn" && data.max_administrations_per_day === undefined) {
      context.addIssue({ code: "custom", message: "PRN exige teto de administrações.", path: ["max_administrations_per_day"] });
    }
    const amountIsVolume = data.amount_unit === "mL";
    if (amountIsVolume && data.concentration_value === undefined) {
      context.addIssue({ code: "custom", message: "Quantidade em volume exige concentração para calcular massa.", path: ["concentration_value"] });
    }
  });

type PrescriptionFormValues = z.infer<typeof prescriptionSchema>;

type PrescriptionFormProps = {
  patients: Patient[];
  medications: Medication[];
  onSubmit: (payload: PrescriptionCheckPayload) => Promise<void> | void;
  disabled?: boolean;
};

export default function PrescriptionForm({ patients, medications, onSubmit, disabled }: PrescriptionFormProps) {
  const {
    control,
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    reset,
  } = useForm<PrescriptionFormValues>({
    resolver: zodResolver(prescriptionSchema),
    mode: "onBlur",
    defaultValues: {
      patient_id: patients[0]?.id ?? 0,
      medication_id: medications[0]?.id ?? 0,
      amount: 100,
      amount_unit: "mg",
      administration_kind: "intermittent",
      frequency_per_day: 1,
      route: "oral",
      duration_value: 3,
      duration_unit: "day",
      indication: "dor",
      professional_notes: "",
    },
  });

  const administrationKind = useWatch({ control, name: "administration_kind" });
  const amountUnit = useWatch({ control, name: "amount_unit" });
  const concentrationValue = useWatch({ control, name: "concentration_value" });
  const volume = useWatch({ control, name: "volume" });

  useEffect(() => {
    reset((values) => ({
      ...values,
      patient_id: values.patient_id || patients[0]?.id || 0,
      medication_id: values.medication_id || medications[0]?.id || 0,
    }));
  }, [medications, patients, reset]);

  async function submit(values: PrescriptionFormValues) {
    const isPrn = values.administration_kind === "prn";
    await onSubmit({
      patient_id: values.patient_id,
      medication_id: values.medication_id,
      route: values.route,
      dose: {
        amount: values.amount,
        amount_unit: values.amount_unit,
        administration_kind: values.administration_kind,
        concentration_value: values.concentration_value ?? null,
        concentration_unit: values.concentration_unit || null,
        volume: values.volume ?? null,
        volume_unit: values.volume_unit || null,
        rate_value: values.rate_value ?? null,
        rate_unit: values.rate_unit || null,
        frequency_per_day: isPrn ? null : values.frequency_per_day ?? null,
        interval_value: isPrn ? null : values.interval_value ?? null,
        interval_unit: isPrn ? null : values.interval_unit || null,
        duration_value: values.duration_value ?? null,
        duration_unit: values.duration_unit || null,
        route: values.route,
        site: values.site || null,
        procedure_context: values.procedure_context || null,
        prn: isPrn,
        max_administrations_per_day: isPrn ? values.max_administrations_per_day ?? null : null,
        source_id: "ui-structured-dose-v0.8.7",
        source_version: "0.8.7",
        precision: "0.0001",
        rounding_policy: "prescripta-half-even-v1",
      },
      duration_days: values.duration_unit === "day" && Number.isInteger(values.duration_value) ? values.duration_value ?? null : null,
      indication: values.indication || null,
      professional_notes: values.professional_notes || null,
    });
  }

  function focusFirstError() {
    window.requestAnimationFrame(() => {
      document.querySelector<HTMLElement>("[aria-invalid='true']")?.focus();
    });
  }

  return (
    <form className="grid gap-5" noValidate onSubmit={handleSubmit(submit, focusFirstError)}>
      <FormStep icon={Route} number="1" title="Contexto autorizado" description="Paciente e medicamento que serão avaliados.">
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Paciente" error={errors.patient_id?.message}>
            <select aria-invalid={Boolean(errors.patient_id)} className="field" disabled={disabled} {...register("patient_id", { valueAsNumber: true })}>
              <option value={0}>Selecione</option>
              {patients.map((patient) => <option key={patient.id} value={patient.id}>{patient.name} · contexto {patient.clinical_profile_completeness_score}%</option>)}
            </select>
          </Field>
          <Field label="Medicamento" error={errors.medication_id?.message}>
            <select aria-invalid={Boolean(errors.medication_id)} className="field" disabled={disabled} {...register("medication_id", { valueAsNumber: true })}>
              <option value={0}>Selecione</option>
              {medications.map((medication) => <option key={medication.id} value={medication.id}>{medication.brand_name} · {medication.active_ingredient}</option>)}
            </select>
          </Field>
        </div>
      </FormStep>

      <FormStep icon={FlaskConical} number="2" title="Quantidade e dimensão" description="Informe a unidade real; conversões usam aritmética decimal no backend.">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Quantidade por administração" error={errors.amount?.message} hint={`Dimensão: ${dimensionLabel(amountUnit)}`}>
            <input aria-invalid={Boolean(errors.amount)} className="field" disabled={disabled} inputMode="decimal" min="0" step="any" type="number" {...register("amount", { valueAsNumber: true })} />
          </Field>
          <Field label="Unidade" error={errors.amount_unit?.message}>
            <select aria-invalid={Boolean(errors.amount_unit)} className="field" disabled={disabled} {...register("amount_unit")}>
              {amountUnits.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </Field>
          <Field label="Concentração" error={errors.concentration_value?.message} hint="Obrigatória quando a quantidade é volume.">
            <input aria-invalid={Boolean(errors.concentration_value)} className="field" disabled={disabled} min="0" placeholder="Ex.: 50" step="any" type="number" {...register("concentration_value", optionalNumber)} />
          </Field>
          <Field label="Unidade da concentração" error={errors.concentration_unit?.message}>
            <select aria-invalid={Boolean(errors.concentration_unit)} className="field" disabled={disabled} {...register("concentration_unit")}>
              <option value="">Não aplicável</option><option value="mg/mL">mg/mL</option><option value="mcg/mL">mcg/mL</option><option value="g/L">g/L</option>
            </select>
          </Field>
          <Field label="Volume administrado" error={errors.volume?.message} hint={concentrationValue && volume ? "Massa será derivada de concentração × volume." : undefined}>
            <input aria-invalid={Boolean(errors.volume)} className="field" disabled={disabled} min="0" placeholder="Ex.: 2" step="any" type="number" {...register("volume", optionalNumber)} />
          </Field>
          <Field label="Unidade do volume" error={errors.volume_unit?.message}>
            <select aria-invalid={Boolean(errors.volume_unit)} className="field" disabled={disabled} {...register("volume_unit")}><option value="">Não aplicável</option><option value="mL">mL</option><option value="L">L</option></select>
          </Field>
          <Field label="Modalidade">
            <select className="field" disabled={disabled} {...register("administration_kind")}><option value="intermittent">Intermitente</option><option value="bolus">Bolus</option><option value="continuous">Infusão contínua</option><option value="prn">PRN / se necessário</option></select>
          </Field>
          <div className="flex items-end"><Badge tone="info" icon={<Calculator aria-hidden="true" className="h-3.5 w-3.5" />}>Arredondamento half-even · 0,0001</Badge></div>
        </div>
      </FormStep>

      <FormStep icon={Timer} number="3" title="Regime e limites" description="Frequência, intervalo, duração, taxa e teto PRN são conceitos separados.">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {administrationKind === "intermittent" ? <>
            <Field label="Administrações por dia" error={errors.frequency_per_day?.message} hint="Pode usar frequência ou intervalo."><input aria-invalid={Boolean(errors.frequency_per_day)} className="field" disabled={disabled} min="1" max="96" type="number" {...register("frequency_per_day", optionalNumber)} /></Field>
            <Field label="Intervalo" error={errors.interval_value?.message}><input aria-invalid={Boolean(errors.interval_value)} className="field" disabled={disabled} min="0" placeholder="Ex.: 8" step="any" type="number" {...register("interval_value", optionalNumber)} /></Field>
            <Field label="Unidade do intervalo" error={errors.interval_unit?.message}><select aria-invalid={Boolean(errors.interval_unit)} className="field" disabled={disabled} {...register("interval_unit")}><option value="">Não informado</option><option value="h">horas</option><option value="min">minutos</option><option value="day">dias</option></select></Field>
          </> : null}
          {administrationKind === "continuous" ? <>
            <Field label="Taxa de infusão" error={errors.rate_value?.message}><input aria-invalid={Boolean(errors.rate_value)} className="field" disabled={disabled} min="0" step="any" type="number" {...register("rate_value", optionalNumber)} /></Field>
            <Field label="Unidade da taxa" error={errors.rate_unit?.message}><select aria-invalid={Boolean(errors.rate_unit)} className="field" disabled={disabled} {...register("rate_unit")}><option value="">Selecione</option><option value="mL/h">mL/h</option><option value="mg/h">mg/h</option><option value="mcg/min">mcg/min</option><option value="mcg/kg/min">mcg/kg/min</option></select></Field>
          </> : null}
          {administrationKind === "prn" ? <Field label="Teto de administrações/dia" error={errors.max_administrations_per_day?.message} hint="Obrigatório para PRN."><input aria-invalid={Boolean(errors.max_administrations_per_day)} className="field" disabled={disabled} min="1" max="96" type="number" {...register("max_administrations_per_day", optionalNumber)} /></Field> : null}
          <Field label="Duração" error={errors.duration_value?.message}><input aria-invalid={Boolean(errors.duration_value)} className="field" disabled={disabled} min="0" step="any" type="number" {...register("duration_value", optionalNumber)} /></Field>
          <Field label="Unidade da duração" error={errors.duration_unit?.message}><select aria-invalid={Boolean(errors.duration_unit)} className="field" disabled={disabled} {...register("duration_unit")}><option value="">Não informada</option><option value="h">horas</option><option value="day">dias</option><option value="min">minutos</option></select></Field>
          <Field label="Via" error={errors.route?.message}><select aria-invalid={Boolean(errors.route)} className="field" disabled={disabled} {...register("route")}><option value="oral">Oral</option><option value="intravenosa">Intravenosa</option><option value="intramuscular">Intramuscular</option><option value="subcutanea">Subcutânea</option><option value="inalatoria">Inalatória</option><option value="topica">Tópica</option></select></Field>
          <Field label="Sítio"><input className="field" disabled={disabled} placeholder="Quando relevante" {...register("site")} /></Field>
          <Field label="Procedimento"><input className="field" disabled={disabled} placeholder="Contexto perioperatório, sessão…" {...register("procedure_context")} /></Field>
        </div>
      </FormStep>

      <FormStep icon={Check} number="4" title="Revisão e execução" description="A validação da interface ajuda, mas o backend continua sendo a autoridade.">
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Indicação demonstrativa"><input className="field" disabled={disabled} {...register("indication")} /></Field>
          <Field label="Observações do profissional" error={errors.professional_notes?.message}><textarea className="field min-h-24 resize-y" disabled={disabled} {...register("professional_notes")} /></Field>
        </div>
        <div className="mt-5 flex flex-col gap-3 border-t border-slate-200 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="max-w-2xl text-xs leading-5 text-slate-500">A execução persiste snapshot, decisão, cobertura, fontes e auditoria antes de habilitar qualquer explicação por IA.</p>
          <button className="btn-primary shrink-0" disabled={disabled || isSubmitting} type="submit"><ClipboardCheck aria-hidden="true" className="h-4 w-4" />{disabled || isSubmitting ? "Executando checagem…" : "Executar checagem"}</button>
        </div>
      </FormStep>
    </form>
  );
}

const optionalNumber = { setValueAs: (value: string) => value === "" ? undefined : Number(value) } as const;

const amountUnits = [
  ["mg", "mg · massa"], ["mcg", "mcg · massa"], ["g", "g · massa"], ["mL", "mL · volume"],
  ["mg/kg", "mg/kg · por peso"], ["mcg/kg", "mcg/kg · por peso"], ["mg/m2", "mg/m² · por superfície"], ["mcg/kg/min", "mcg/kg/min · taxa por peso"],
] as const;

function dimensionLabel(unit: string) {
  if (unit.includes("/kg/") || unit.includes("/m2/")) return "taxa por base corporal";
  if (unit.includes("/kg")) return "massa por peso";
  if (unit.includes("/m2")) return "massa por superfície";
  if (unit === "mL") return "volume";
  return "massa";
}

function FormStep({ icon: Icon, number, title, description, children }: { icon: typeof Route; number: string; title: string; description: string; children: ReactNode }) {
  return (
    <fieldset className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
      <legend className="px-1">
        <span className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-50 text-ocean"><Icon aria-hidden="true" className="h-4 w-4" /></span>
          <span><span className="block text-xs font-extrabold uppercase tracking-[0.12em] text-ocean">Etapa {number}</span><span className="block text-base font-black text-ink">{title}</span></span>
        </span>
      </legend>
      <p className="mb-4 mt-2 text-sm leading-6 text-slate-600">{description}</p>
      {children}
    </fieldset>
  );
}

function Field({ label, error, hint, children }: { label: string; error?: string; hint?: string; children: ReactNode }) {
  return <label className="grid content-start gap-1.5"><span className="label">{label}</span>{children}{error ? <span className="field-error" role="alert">{error}</span> : hint ? <span className="field-hint">{hint}</span> : null}</label>;
}
