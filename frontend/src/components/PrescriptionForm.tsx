import { zodResolver } from "@hookform/resolvers/zod";
import { Calculator, Check, ClipboardCheck, FlaskConical, Route, Timer } from "lucide-react";
import type { TFunction } from "i18next";
import { useEffect, useMemo } from "react";
import type { ReactNode } from "react";
import { useForm, useWatch } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";

import type { Medication } from "../types/medication";
import type { Patient } from "../types/patient";
import type { PrescriptionCheckPayload } from "../types/prescription";
import Badge from "./ui/Badge";

const optionalPositive = z.number().positive().optional();

const createPrescriptionSchema = (t: TFunction) => z
  .object({
    patient_id: z.number().int().positive(t("prescription.form.errors.patient")),
    medication_id: z.number().int().positive(t("prescription.form.errors.medication")),
    amount: z.number().positive(t("prescription.form.errors.amount")),
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
    route: z.string().min(2, t("prescription.form.errors.route")),
    site: z.string().optional(),
    procedure_context: z.string().optional(),
    max_administrations_per_day: z.number().int().positive().max(96).optional(),
    indication: z.string().optional(),
    professional_notes: z.string().max(1000).optional(),
  })
  .superRefine((data, context) => {
    const requirePair = (value: number | undefined, unit: string | undefined, path: string, label: string) => {
      if ((value === undefined) !== !unit) {
        context.addIssue({ code: "custom", message: t("prescription.form.errors.pair", { label }), path: [path] });
      }
    };
    requirePair(data.concentration_value, data.concentration_unit, "concentration_value", t("prescription.form.concentration"));
    requirePair(data.volume, data.volume_unit, "volume", t("prescription.form.volume"));
    requirePair(data.rate_value, data.rate_unit, "rate_value", t("prescription.form.rate"));
    requirePair(data.interval_value, data.interval_unit, "interval_value", t("prescription.form.interval"));
    requirePair(data.duration_value, data.duration_unit, "duration_value", t("prescription.form.duration"));
    if (data.administration_kind === "continuous" && data.rate_value === undefined) {
      context.addIssue({ code: "custom", message: t("prescription.form.errors.continuousRate"), path: ["rate_value"] });
    }
    if (data.administration_kind === "intermittent" && data.frequency_per_day === undefined && data.interval_value === undefined) {
      context.addIssue({ code: "custom", message: t("prescription.form.errors.frequency"), path: ["frequency_per_day"] });
    }
    if (data.administration_kind === "prn" && data.max_administrations_per_day === undefined) {
      context.addIssue({ code: "custom", message: t("prescription.form.errors.prnLimit"), path: ["max_administrations_per_day"] });
    }
    const amountIsVolume = data.amount_unit === "mL";
    if (amountIsVolume && data.concentration_value === undefined) {
      context.addIssue({ code: "custom", message: t("prescription.form.errors.volumeConcentration"), path: ["concentration_value"] });
    }
  });

type PrescriptionFormValues = z.infer<ReturnType<typeof createPrescriptionSchema>>;

type PrescriptionFormProps = {
  patients: Patient[];
  medications: Medication[];
  onSubmit: (payload: PrescriptionCheckPayload) => Promise<void> | void;
  disabled?: boolean;
};

export default function PrescriptionForm({ patients, medications, onSubmit, disabled }: PrescriptionFormProps) {
  const { t } = useTranslation();
  const schema = useMemo(() => createPrescriptionSchema(t), [t]);
  const {
    control,
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    reset,
  } = useForm<PrescriptionFormValues>({
    resolver: zodResolver(schema),
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
        source_id: "ui-structured-dose-v0.8.9",
        source_version: "0.8.9",
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
      <FormStep icon={Route} number="1" title={t("prescription.form.authorizedContext")} description={t("prescription.form.authorizedContextBody")}>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label={t("prescription.form.patient")} error={errors.patient_id?.message}>
            <select aria-invalid={Boolean(errors.patient_id)} className="field" disabled={disabled} {...register("patient_id", { valueAsNumber: true })}>
              <option value={0}>{t("prescription.form.select")}</option>
              {patients.map((patient) => <option key={patient.id} value={patient.id}>{patient.name} · {t("prescription.form.contextScore", { score: patient.clinical_profile_completeness_score })}</option>)}
            </select>
          </Field>
          <Field label={t("prescription.form.medication")} error={errors.medication_id?.message}>
            <select aria-invalid={Boolean(errors.medication_id)} className="field" disabled={disabled} {...register("medication_id", { valueAsNumber: true })}>
              <option value={0}>{t("prescription.form.select")}</option>
              {medications.map((medication) => <option key={medication.id} value={medication.id}>{medication.brand_name} · {medication.active_ingredient}</option>)}
            </select>
          </Field>
        </div>
      </FormStep>

      <FormStep icon={FlaskConical} number="2" title={t("prescription.form.quantityDimension")} description={t("prescription.form.quantityDimensionBody")}>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label={t("prescription.form.amountPerAdministration")} error={errors.amount?.message} hint={t("prescription.form.dimension", { dimension: dimensionLabel(amountUnit, t) })}>
            <input aria-invalid={Boolean(errors.amount)} className="field" disabled={disabled} inputMode="decimal" min="0" step="any" type="number" {...register("amount", { valueAsNumber: true })} />
          </Field>
          <Field label={t("prescription.form.unit")} error={errors.amount_unit?.message}>
            <select aria-invalid={Boolean(errors.amount_unit)} className="field" disabled={disabled} {...register("amount_unit")}>
              {amountUnits(t).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </Field>
          <Field label={t("prescription.form.concentration")} error={errors.concentration_value?.message} hint={t("prescription.form.concentrationHint")}>
            <input aria-invalid={Boolean(errors.concentration_value)} className="field" disabled={disabled} min="0" placeholder="Ex.: 50" step="any" type="number" {...register("concentration_value", optionalNumber)} />
          </Field>
          <Field label={t("prescription.form.concentrationUnit")} error={errors.concentration_unit?.message}>
            <select aria-invalid={Boolean(errors.concentration_unit)} className="field" disabled={disabled} {...register("concentration_unit")}>
              <option value="">{t("prescription.form.notApplicable")}</option><option value="mg/mL">mg/mL</option><option value="mcg/mL">mcg/mL</option><option value="g/L">g/L</option>
            </select>
          </Field>
          <Field label={t("prescription.form.administeredVolume")} error={errors.volume?.message} hint={concentrationValue && volume ? t("prescription.form.derivedMass") : undefined}>
            <input aria-invalid={Boolean(errors.volume)} className="field" disabled={disabled} min="0" placeholder="Ex.: 2" step="any" type="number" {...register("volume", optionalNumber)} />
          </Field>
          <Field label={t("prescription.form.volumeUnit")} error={errors.volume_unit?.message}>
            <select aria-invalid={Boolean(errors.volume_unit)} className="field" disabled={disabled} {...register("volume_unit")}><option value="">{t("prescription.form.notApplicable")}</option><option value="mL">mL</option><option value="L">L</option></select>
          </Field>
          <Field label={t("prescription.form.modality")}>
            <select className="field" disabled={disabled} {...register("administration_kind")}><option value="intermittent">{t("prescription.form.intermittent")}</option><option value="bolus">Bolus</option><option value="continuous">{t("prescription.form.continuous")}</option><option value="prn">{t("prescription.form.prn")}</option></select>
          </Field>
          <div className="flex items-end"><Badge tone="info" icon={<Calculator aria-hidden="true" className="h-3.5 w-3.5" />}>{t("prescription.form.rounding")}</Badge></div>
        </div>
      </FormStep>

      <FormStep icon={Timer} number="3" title={t("prescription.form.regimenLimits")} description={t("prescription.form.regimenLimitsBody")}>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {administrationKind === "intermittent" ? <>
            <Field label={t("prescription.form.administrationsPerDay")} error={errors.frequency_per_day?.message} hint={t("prescription.form.frequencyHint")}><input aria-invalid={Boolean(errors.frequency_per_day)} className="field" disabled={disabled} min="1" max="96" type="number" {...register("frequency_per_day", optionalNumber)} /></Field>
            <Field label={t("prescription.form.interval")} error={errors.interval_value?.message}><input aria-invalid={Boolean(errors.interval_value)} className="field" disabled={disabled} min="0" placeholder={t("prescription.form.exampleEight")} step="any" type="number" {...register("interval_value", optionalNumber)} /></Field>
            <Field label={t("prescription.form.intervalUnit")} error={errors.interval_unit?.message}><select aria-invalid={Boolean(errors.interval_unit)} className="field" disabled={disabled} {...register("interval_unit")}><option value="">{t("prescription.form.notReported")}</option><option value="h">{t("prescription.form.hours")}</option><option value="min">{t("prescription.form.minutes")}</option><option value="day">{t("prescription.form.days")}</option></select></Field>
          </> : null}
          {administrationKind === "continuous" ? <>
            <Field label={t("prescription.form.infusionRate")} error={errors.rate_value?.message}><input aria-invalid={Boolean(errors.rate_value)} className="field" disabled={disabled} min="0" step="any" type="number" {...register("rate_value", optionalNumber)} /></Field>
            <Field label={t("prescription.form.rateUnit")} error={errors.rate_unit?.message}><select aria-invalid={Boolean(errors.rate_unit)} className="field" disabled={disabled} {...register("rate_unit")}><option value="">{t("prescription.form.select")}</option><option value="mL/h">mL/h</option><option value="mg/h">mg/h</option><option value="mcg/min">mcg/min</option><option value="mcg/kg/min">mcg/kg/min</option></select></Field>
          </> : null}
          {administrationKind === "prn" ? <Field label={t("prescription.form.prnDailyLimit")} error={errors.max_administrations_per_day?.message} hint={t("prescription.form.prnRequired")}><input aria-invalid={Boolean(errors.max_administrations_per_day)} className="field" disabled={disabled} min="1" max="96" type="number" {...register("max_administrations_per_day", optionalNumber)} /></Field> : null}
          <Field label={t("prescription.form.duration")} error={errors.duration_value?.message}><input aria-invalid={Boolean(errors.duration_value)} className="field" disabled={disabled} min="0" step="any" type="number" {...register("duration_value", optionalNumber)} /></Field>
          <Field label={t("prescription.form.durationUnit")} error={errors.duration_unit?.message}><select aria-invalid={Boolean(errors.duration_unit)} className="field" disabled={disabled} {...register("duration_unit")}><option value="">{t("prescription.form.notReportedFemale")}</option><option value="h">{t("prescription.form.hours")}</option><option value="day">{t("prescription.form.days")}</option><option value="min">{t("prescription.form.minutes")}</option></select></Field>
          <Field label={t("prescription.form.route")} error={errors.route?.message}><select aria-invalid={Boolean(errors.route)} className="field" disabled={disabled} {...register("route")}><option value="oral">{t("prescription.form.routes.oral")}</option><option value="intravenosa">{t("prescription.form.routes.intravenous")}</option><option value="intramuscular">{t("prescription.form.routes.intramuscular")}</option><option value="subcutanea">{t("prescription.form.routes.subcutaneous")}</option><option value="inalatoria">{t("prescription.form.routes.inhaled")}</option><option value="topica">{t("prescription.form.routes.topical")}</option></select></Field>
          <Field label={t("prescription.form.site")}><input className="field" disabled={disabled} placeholder={t("prescription.form.whenRelevant")} {...register("site")} /></Field>
          <Field label={t("prescription.form.procedure")}><input className="field" disabled={disabled} placeholder={t("prescription.form.procedurePlaceholder")} {...register("procedure_context")} /></Field>
        </div>
      </FormStep>

      <FormStep icon={Check} number="4" title={t("prescription.form.reviewExecution")} description={t("prescription.form.reviewExecutionBody")}>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label={t("prescription.form.demoIndication")}><input className="field" disabled={disabled} {...register("indication")} /></Field>
          <Field label={t("prescription.form.professionalNotes")} error={errors.professional_notes?.message}><textarea className="field min-h-24 resize-y" disabled={disabled} {...register("professional_notes")} /></Field>
        </div>
        <div className="mt-5 flex flex-col gap-3 border-t border-slate-200 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="max-w-2xl text-xs leading-5 text-slate-500">{t("prescription.form.executionNotice")}</p>
          <button className="btn-primary shrink-0" disabled={disabled || isSubmitting} type="submit"><ClipboardCheck aria-hidden="true" className="h-4 w-4" />{disabled || isSubmitting ? t("prescription.form.executing") : t("prescription.form.execute")}</button>
        </div>
      </FormStep>
    </form>
  );
}

const optionalNumber = { setValueAs: (value: string) => value === "" ? undefined : Number(value) } as const;

const amountUnits = (t: TFunction) => [
  ["mg", `mg · ${t("prescription.form.dimensions.mass")}`], ["mcg", `mcg · ${t("prescription.form.dimensions.mass")}`], ["g", `g · ${t("prescription.form.dimensions.mass")}`], ["mL", `mL · ${t("prescription.form.dimensions.volume")}`],
  ["mg/kg", `mg/kg · ${t("prescription.form.dimensions.byWeight")}`], ["mcg/kg", `mcg/kg · ${t("prescription.form.dimensions.byWeight")}`], ["mg/m2", `mg/m² · ${t("prescription.form.dimensions.bySurface")}`], ["mcg/kg/min", `mcg/kg/min · ${t("prescription.form.dimensions.rateByWeight")}`],
] as const;

function dimensionLabel(unit: string, t: TFunction) {
  if (unit.includes("/kg/") || unit.includes("/m2/")) return t("prescription.form.dimensions.rateByBodyBase");
  if (unit.includes("/kg")) return t("prescription.form.dimensions.massByWeight");
  if (unit.includes("/m2")) return t("prescription.form.dimensions.massBySurface");
  if (unit === "mL") return t("prescription.form.dimensions.volume");
  return t("prescription.form.dimensions.mass");
}

function FormStep({ icon: Icon, number, title, description, children }: { icon: typeof Route; number: string; title: string; description: string; children: ReactNode }) {
  const { t } = useTranslation();
  return (
    <fieldset className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
      <legend className="px-1">
        <span className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-50 text-ocean"><Icon aria-hidden="true" className="h-4 w-4" /></span>
          <span><span className="block text-xs font-extrabold uppercase tracking-[0.12em] text-ocean">{t("prescription.form.step", { number })}</span><span className="block text-base font-black text-ink">{title}</span></span>
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
