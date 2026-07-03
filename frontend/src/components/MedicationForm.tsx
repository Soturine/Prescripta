import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Save } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { ActiveIngredient } from "../types/catalog";
import type { Medication, MedicationPayload } from "../types/medication";
import { joinList, splitList } from "../utils/formatters";
import Autocomplete from "./Autocomplete";
import ControlledSelect from "./ControlledSelect";
import TagInput from "./TagInput";

const medicationSchema = z.object({
  active_ingredient_id: z.number().optional(),
  brand_name: z.string().min(2, "Informe o nome comercial."),
  active_ingredient: z.string().min(2, "Informe o principio ativo."),
  commercial_aliases: z.string().optional(),
  therapeutic_class: z.string().min(2, "Informe a classe."),
  therapeutic_classes: z.string().optional(),
  source_jurisdiction: z.string().min(2),
  evidence_source_type: z.string().min(2),
  validation_status: z.string().min(2),
  concentration: z.string().optional(),
  pharmaceutical_form: z.string().optional(),
  evidence_source_url: z.string().optional(),
  max_daily_dose_mg: z.number().positive("Informe a dose maxima."),
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
  activeIngredients?: ActiveIngredient[];
  submitLabel: string;
  onSubmit: (payload: MedicationPayload) => Promise<void> | void;
};

export default function MedicationForm({
  initialMedication,
  activeIngredients = [],
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
      active_ingredient_id: initialMedication?.active_ingredient_id ?? undefined,
      brand_name: initialMedication?.brand_name ?? "",
      active_ingredient: initialMedication?.active_ingredient ?? "",
      commercial_aliases: joinList(initialMedication?.commercial_aliases),
      therapeutic_class: initialMedication?.therapeutic_class ?? "",
      therapeutic_classes: joinList(initialMedication?.therapeutic_classes),
      source_jurisdiction: initialMedication?.source_jurisdiction ?? "BR",
      evidence_source_type: initialMedication?.evidence_source_type ?? "manual_curated",
      validation_status: initialMedication?.validation_status ?? "pending_review",
      concentration: initialMedication?.concentration ?? "",
      pharmaceutical_form: initialMedication?.pharmaceutical_form ?? "",
      evidence_source_url: initialMedication?.evidence_source_url ?? "",
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
  const activeIngredientOptions = activeIngredients.map((ingredient) => ingredient.dcb_name);

  async function submit(values: MedicationFormValues) {
    const selectedIngredient = activeIngredients.find(
      (ingredient) => normalize(ingredient.dcb_name) === normalize(values.active_ingredient),
    );
    await onSubmit({
      active_ingredient_id: selectedIngredient?.id ?? values.active_ingredient_id ?? null,
      brand_name: values.brand_name,
      active_ingredient: values.active_ingredient,
      commercial_aliases: splitList(values.commercial_aliases ?? ""),
      therapeutic_class: values.therapeutic_class,
      therapeutic_classes: splitList(values.therapeutic_classes ?? ""),
      source_jurisdiction: values.source_jurisdiction,
      evidence_source_type: values.evidence_source_type,
      validation_status: values.validation_status,
      concentration: values.concentration || null,
      pharmaceutical_form: values.pharmaceutical_form || null,
      evidence_source_url: values.evidence_source_url || null,
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
        active_ingredient_id: undefined,
        brand_name: "",
        active_ingredient: "",
        commercial_aliases: "",
        therapeutic_class: "",
        therapeutic_classes: "",
        source_jurisdiction: "BR",
        evidence_source_type: "manual_curated",
        validation_status: "pending_review",
        concentration: "",
        pharmaceutical_form: "",
        evidence_source_url: "",
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
          <span className="label">Nome comercial/produto</span>
          <input className="field" placeholder="Novalgina Demo" {...register("brand_name")} />
          {errors.brand_name ? (
            <span className="text-xs text-danger">{errors.brand_name.message}</span>
          ) : null}
        </label>

        <Autocomplete
          error={errors.active_ingredient?.message}
          label="Principio ativo DCB"
          listId="active-ingredient-options"
          options={activeIngredientOptions}
          placeholder="dipirona"
          {...register("active_ingredient")}
        />

        <label className="grid gap-1.5">
          <span className="label">Classe terapeutica principal</span>
          <input
            className="field"
            placeholder="analgesico antitermico"
            {...register("therapeutic_class")}
          />
          {errors.therapeutic_class ? (
            <span className="text-xs text-danger">{errors.therapeutic_class.message}</span>
          ) : null}
        </label>

        <TagInput
          label="Aliases e nomes comerciais"
          placeholder="Novalgina, Anador, Dorflex"
          valuePreview={initialMedication ? joinList(initialMedication.commercial_aliases) : ""}
          {...register("commercial_aliases")}
        />

        <TagInput
          label="Classes controladas"
          placeholder="analgesico, antitermico"
          valuePreview={initialMedication ? joinList(initialMedication.therapeutic_classes) : ""}
          {...register("therapeutic_classes")}
        />

        <label className="grid gap-1.5">
          <span className="label">Dose maxima diaria mg</span>
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
          <span className="label">Duracao maxima dias</span>
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
          <span className="label">Dose acumulada maxima mg</span>
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

      <div className="grid gap-4 md:grid-cols-3">
        <ControlledSelect
          label="Jurisdicao da fonte"
          options={[
            { value: "BR", label: "Brasil (BR)" },
            { value: "GLOBAL", label: "Global" },
            { value: "US", label: "Estados Unidos (US)" },
            { value: "EU", label: "Uniao Europeia (EU)" },
          ]}
          {...register("source_jurisdiction")}
        />
        <ControlledSelect
          label="Fonte da evidencia"
          options={[
            { value: "manual_curated", label: "Curadoria manual" },
            { value: "anvisa_bulario", label: "Anvisa/Bulario" },
            { value: "dcb", label: "DCB" },
            { value: "demo_seed", label: "Seed demonstrativo" },
            { value: "external_reference", label: "Referencia externa" },
          ]}
          {...register("evidence_source_type")}
        />
        <ControlledSelect
          label="Status de validacao"
          options={[
            { value: "pending_review", label: "Pendente de revisao" },
            { value: "demo", label: "Demonstrativo" },
            { value: "curated", label: "Curado" },
            { value: "validated", label: "Validado" },
          ]}
          {...register("validation_status")}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <label className="grid gap-1.5">
          <span className="label">Concentracao</span>
          <input className="field" placeholder="500 mg/mL" {...register("concentration")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Forma farmaceutica</span>
          <input
            className="field"
            placeholder="comprimido, gotas"
            {...register("pharmaceutical_form")}
          />
        </label>
        <label className="grid gap-1.5">
          <span className="label">URL da fonte/bula</span>
          <input
            className="field"
            placeholder="https://consultas.anvisa.gov.br/..."
            {...register("evidence_source_url")}
          />
        </label>
      </div>

      <label className="grid gap-1.5">
        <span className="label">Limites por condicao</span>
        <input
          className="field"
          placeholder="renal:1200, hepatico:800"
          {...register("condition_specific_limits")}
        />
      </label>

      <div className="grid gap-3 md:grid-cols-3">
        {[
          ["renal_caution", "Cautela renal"],
          ["hepatic_caution", "Cautela hepatica"],
          ["cardiac_caution", "Cautela cardiaca"],
          ["gastrointestinal_caution", "Cautela gastrointestinal"],
          ["elderly_caution", "Cautela em idosos"],
        ].map(([field, label]) => (
          <label
            className="flex min-h-11 items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700"
            key={field}
          >
            <input
              className="h-4 w-4 accent-ocean"
              type="checkbox"
              {...register(field as keyof MedicationFormValues)}
            />
            {label}
          </label>
        ))}
      </div>

      <TagInput label="Vias permitidas" placeholder="oral, intravenosa" {...register("allowed_routes")} />
      {errors.allowed_routes ? (
        <span className="text-xs text-danger">{errors.allowed_routes.message}</span>
      ) : null}

      <TagInput
        label="Contraindicacoes estruturadas"
        placeholder="ulcera ativa, doenca renal grave"
        {...register("contraindications")}
      />

      <div className="grid gap-4 md:grid-cols-2">
        <TagInput label="Metabolizacao/processamento" placeholder="hepatico" {...register("metabolism_organs")} />
        <TagInput label="Eliminacao principal" placeholder="renal" {...register("elimination_organs")} />
        <TagInput label="Orgaos envolvidos" placeholder="renal, gastrointestinal" {...register("organs_involved")} />
        <TagInput
          label="Efeitos adversos relevantes"
          placeholder="sangramento gastrointestinal, gastrite"
          {...register("relevant_adverse_effects")}
        />
        <TagInput
          label="Contraindicacoes por categoria"
          placeholder="renal, gastrointestinal"
          {...register("structured_contraindications")}
        />
        <label className="grid gap-1.5">
          <span className="label">Acao/finalidade</span>
          <input className="field" placeholder="analgesia" {...register("therapeutic_action")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Grupo de alternativas</span>
          <input className="field" placeholder="analgesia" {...register("alternative_group")} />
        </label>
        <TagInput label="Medicamentos relacionados" placeholder="paracetamol, ibuprofeno" {...register("related_medications")} />
      </div>

      <label className="grid gap-1.5">
        <span className="label">Fonte demonstrativa/observacao da evidencia</span>
        <input className="field" {...register("knowledge_source")} />
      </label>

      <label className="grid gap-1.5">
        <span className="label">Observacoes clinicas</span>
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

function normalize(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}
