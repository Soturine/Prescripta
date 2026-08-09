import { zodResolver } from "@hookform/resolvers/zod";
import type { TFunction } from "i18next";
import { Plus, Save } from "lucide-react";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";

import type { Patient, PatientPayload } from "../types/patient";
import {
  cardiacOptions,
  gastrointestinalOptions,
  hepaticOptions,
  renalOptions,
} from "../utils/clinicalVocabulary";
import { joinList, splitList } from "../utils/formatters";
import ControlledSelect from "./ControlledSelect";

const createPatientSchema = (t: TFunction) => z
  .object({
    name: z.string().min(2, t("patientForm.errors.name")),
    birth_date: z.string().optional(),
    age: z.number().min(0).max(130).optional(),
    weight_kg: z.number().positive(t("patientForm.errors.weight")),
    height_cm: z.number().min(1).max(260).optional(),
    sex_for_dosing_calculation: z.enum(["male", "female"]).or(z.literal("")).optional(),
    phone: z.string().optional(),
    email: z.string().optional(),
    mother_name: z.string().optional(),
    allergies: z.string().optional(),
    comorbidities: z.string().optional(),
    current_medications: z.string().optional(),
    renal_condition: z.string().optional(),
    hepatic_condition: z.string().optional(),
    cardiac_condition: z.string().optional(),
    gastrointestinal_history: z.string().optional(),
    hypertension: z.boolean(),
    diabetes: z.boolean(),
    pregnancy_or_lactation: z.boolean(),
    mental_health_factors: z.string().optional(),
    reproductive_gynecologic_factors: z.string().optional(),
    adverse_reactions: z.string().optional(),
    clinical_notes: z.string().optional(),
  })
  .refine((data) => data.age !== undefined || Boolean(data.birth_date), {
    message: t("patientForm.errors.ageOrBirth"),
    path: ["age"],
  });

type PatientFormValues = z.infer<ReturnType<typeof createPatientSchema>>;

type PatientFormProps = {
  initialPatient?: Patient;
  submitLabel: string;
  onSubmit: (payload: PatientPayload) => Promise<void> | void;
};

export default function PatientForm({ initialPatient, submitLabel, onSubmit }: PatientFormProps) {
  const { t } = useTranslation();
  const schema = useMemo(() => createPatientSchema(t), [t]);
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    reset,
  } = useForm<PatientFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initialPatient?.name ?? "",
      birth_date: initialPatient?.birth_date ?? "",
      age: initialPatient?.age ?? undefined,
      weight_kg: initialPatient?.weight_kg ?? 70,
      height_cm: initialPatient?.height_cm ?? undefined,
      sex_for_dosing_calculation: initialPatient?.sex_for_dosing_calculation ?? "",
      phone: initialPatient?.phone ?? "",
      email: initialPatient?.email ?? "",
      mother_name: initialPatient?.mother_name ?? "",
      allergies: joinList(initialPatient?.allergies),
      comorbidities: joinList(initialPatient?.comorbidities),
      current_medications: joinList(initialPatient?.current_medications),
      renal_condition: initialPatient?.renal_condition ?? "",
      hepatic_condition: initialPatient?.hepatic_condition ?? "",
      cardiac_condition: initialPatient?.cardiac_condition ?? "",
      gastrointestinal_history: initialPatient?.gastrointestinal_history ?? "",
      hypertension: initialPatient?.hypertension ?? false,
      diabetes: initialPatient?.diabetes ?? false,
      pregnancy_or_lactation: initialPatient?.pregnancy_or_lactation ?? false,
      mental_health_factors: joinList(initialPatient?.mental_health_factors),
      reproductive_gynecologic_factors: joinList(
        initialPatient?.reproductive_gynecologic_factors,
      ),
      adverse_reactions: joinList(initialPatient?.adverse_reactions),
      clinical_notes: initialPatient?.clinical_notes ?? "",
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
      sex_for_dosing_calculation: values.sex_for_dosing_calculation || null,
      phone: values.phone || null,
      email: values.email || null,
      mother_name: values.mother_name || null,
      allergies: splitList(values.allergies ?? ""),
      comorbidities: splitList(values.comorbidities ?? ""),
      current_medications: splitList(values.current_medications ?? ""),
      renal_condition: values.renal_condition || null,
      hepatic_condition: values.hepatic_condition || null,
      cardiac_condition: values.cardiac_condition || null,
      gastrointestinal_history: values.gastrointestinal_history || null,
      hypertension: values.hypertension,
      diabetes: values.diabetes,
      pregnancy_or_lactation: values.pregnancy_or_lactation,
      mental_health_factors: splitList(values.mental_health_factors ?? ""),
      reproductive_gynecologic_factors: splitList(
        values.reproductive_gynecologic_factors ?? "",
      ),
      adverse_reactions: splitList(values.adverse_reactions ?? ""),
      clinical_notes: values.clinical_notes || null,
    });

    if (!initialPatient) {
      reset({
        name: "",
        birth_date: "",
        age: undefined,
        weight_kg: 70,
        height_cm: undefined,
        sex_for_dosing_calculation: "",
        phone: "",
        email: "",
        mother_name: "",
        allergies: "",
        comorbidities: "",
        current_medications: "",
        renal_condition: "",
        hepatic_condition: "",
        cardiac_condition: "",
        gastrointestinal_history: "",
        hypertension: false,
        diabetes: false,
        pregnancy_or_lactation: false,
        mental_health_factors: "",
        reproductive_gynecologic_factors: "",
        adverse_reactions: "",
        clinical_notes: "",
      });
    }
  }

  return (
    <form className="grid gap-4" onSubmit={handleSubmit(submit)}>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="label">{t("patientForm.name")}</span>
          <input className="field" {...register("name")} />
          {errors.name ? <span className="text-xs text-danger">{errors.name.message}</span> : null}
        </label>

        <label className="grid gap-1.5">
          <span className="label">{t("patientForm.age")}</span>
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
          <span className="label">{t("patientForm.birthDate")}</span>
          <input className="field" type="date" {...register("birth_date")} />
        </label>

        <label className="grid gap-1.5">
          <span className="label">{t("patientForm.weightKg")}</span>
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
          <span className="label">{t("patientForm.heightCm")}</span>
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
          <span className="label">{t("patientForm.dosingSex")}</span>
          <select className="field" {...register("sex_for_dosing_calculation")}>
            <option value="">{t("patientForm.notReported")}</option>
            <option value="female">{t("patientForm.femalePhysiology")}</option>
            <option value="male">{t("patientForm.malePhysiology")}</option>
          </select>
          <span className="text-xs text-muted">
            {t("patientForm.dosingSexHint")}
          </span>
        </label>

        <label className="grid gap-1.5">
          <span className="label">{t("patientForm.phone")}</span>
          <input className="field" placeholder={t("patientForm.demoPlaceholder")} {...register("phone")} />
        </label>

        <label className="grid gap-1.5">
          <span className="label">{t("patientForm.email")}</span>
          <input className="field" placeholder="paciente@demo.local" {...register("email")} />
        </label>

        <label className="grid gap-1.5">
          <span className="label">{t("patientForm.motherName")}</span>
          <input className="field" placeholder={t("patientForm.matchingHint")} {...register("mother_name")} />
        </label>

        <label className="grid gap-1.5">
          <span className="label">{t("patientForm.allergies")}</span>
          <input className="field" placeholder="dipirona" {...register("allergies")} />
        </label>
      </div>

      <label className="grid gap-1.5">
        <span className="label">{t("patientForm.comorbidities")}</span>
        <input className="field" {...register("comorbidities")} />
      </label>

      <label className="grid gap-1.5">
        <span className="label">{t("patientForm.currentMedications")}</span>
        <input className="field" {...register("current_medications")} />
      </label>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="label">{t("patientForm.neuropsychiatric")}</span>
          <input
            className="field"
            placeholder="uso_isrs, epilepsia_convulsoes"
            {...register("mental_health_factors")}
          />
        </label>

        <label className="grid gap-1.5">
          <span className="label">{t("patientForm.reproductive")}</span>
          <input
            className="field"
            placeholder="uso_anticoncepcional_hormonal, gestante"
            {...register("reproductive_gynecologic_factors")}
          />
        </label>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <ControlledSelect label={t("patientForm.renal")} options={localizedOptions(renalOptions, t)} {...register("renal_condition")} />
        <ControlledSelect label={t("patientForm.hepatic")} options={localizedOptions(hepaticOptions, t)} {...register("hepatic_condition")} />
        <ControlledSelect label={t("patientForm.cardiovascular")} options={localizedOptions(cardiacOptions, t)} {...register("cardiac_condition")} />
        <ControlledSelect
          label={t("patientForm.gastrointestinal")}
          options={localizedOptions(gastrointestinalOptions, t)}
          {...register("gastrointestinal_history")}
        />
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <label className="flex min-h-11 items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700">
          <input className="h-4 w-4 accent-ocean" type="checkbox" {...register("hypertension")} />
          {t("patientForm.hypertension")}
        </label>
        <label className="flex min-h-11 items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700">
          <input className="h-4 w-4 accent-ocean" type="checkbox" {...register("diabetes")} />
          {t("patientForm.diabetes")}
        </label>
        <label className="flex min-h-11 items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700">
          <input
            className="h-4 w-4 accent-ocean"
            type="checkbox"
            {...register("pregnancy_or_lactation")}
          />
          {t("patientForm.pregnancyLactation")}
        </label>
      </div>

      <label className="grid gap-1.5">
        <span className="label">{t("patientForm.adverseReactions")}</span>
        <input className="field" {...register("adverse_reactions")} />
      </label>

      <label className="grid gap-1.5">
        <span className="label">{t("patientForm.clinicalNotes")}</span>
        <textarea className="field min-h-20 resize-y" {...register("clinical_notes")} />
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

function localizedOptions(options: typeof renalOptions, t: TFunction) {
  return options.map((option) => ({
    ...option,
    label: t(`clinicalVocabulary.${option.value || "not_reported"}`),
  }));
}
