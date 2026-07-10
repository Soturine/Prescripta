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
  active_ingredient: z.string().min(2, "Informe o princípio ativo."),
  commercial_aliases: z.string().optional(),
  therapeutic_class: z.string().min(2, "Informe a classe."),
  therapeutic_classes: z.string().optional(),
  source_jurisdiction: z.string().min(2),
  evidence_source_type: z.string().min(2),
  validation_status: z.string().min(2),
  concentration: z.string().optional(),
  pharmaceutical_form: z.string().optional(),
  evidence_source_url: z.string().optional(),
  max_daily_dose_mg: z.number().positive("Informe a dose máxima."),
  max_duration_days: z.number().positive().optional(),
  max_cumulative_dose_mg: z.number().positive().optional(),
  continuous_use: z.boolean(),
  monitoring_required: z.boolean(),
  monitoring_notes: z.string().optional(),
  condition_specific_limits: z.string().optional(),
  allowed_routes: z.string().min(2, "Informe ao menos uma via."),
  contraindications: z.string().optional(),
  renal_caution: z.boolean(),
  hepatic_caution: z.boolean(),
  cardiac_caution: z.boolean(),
  gastrointestinal_caution: z.boolean(),
  elderly_caution: z.boolean(),
  mechanism_of_action: z.string().optional(),
  absorption_notes: z.string().optional(),
  distribution_notes: z.string().optional(),
  metabolism_organs: z.string().optional(),
  elimination_organs: z.string().optional(),
  renal_elimination_level: z.string().optional(),
  hepatic_metabolism_level: z.string().optional(),
  cyp_interactions: z.string().optional(),
  pharmacodynamic_notes: z.string().optional(),
  pharmacokinetic_notes: z.string().optional(),
  clinical_interpretation: z.string().optional(),
  neuropsychiatric_cautions: z.string().optional(),
  reproductive_cautions: z.string().optional(),
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
      continuous_use: initialMedication?.continuous_use ?? false,
      monitoring_required: initialMedication?.monitoring_required ?? false,
      monitoring_notes: initialMedication?.monitoring_notes ?? "",
      condition_specific_limits: formatLimits(initialMedication?.condition_specific_limits),
      allowed_routes: joinList(initialMedication?.allowed_routes),
      contraindications: joinList(initialMedication?.contraindications),
      renal_caution: initialMedication?.renal_caution ?? false,
      hepatic_caution: initialMedication?.hepatic_caution ?? false,
      cardiac_caution: initialMedication?.cardiac_caution ?? false,
      gastrointestinal_caution: initialMedication?.gastrointestinal_caution ?? false,
      elderly_caution: initialMedication?.elderly_caution ?? false,
      mechanism_of_action: initialMedication?.mechanism_of_action ?? "",
      absorption_notes: initialMedication?.absorption_notes ?? "",
      distribution_notes: initialMedication?.distribution_notes ?? "",
      metabolism_organs: joinList(initialMedication?.metabolism_organs),
      elimination_organs: joinList(initialMedication?.elimination_organs),
      renal_elimination_level: initialMedication?.renal_elimination_level ?? "nao_informado",
      hepatic_metabolism_level: initialMedication?.hepatic_metabolism_level ?? "nao_informado",
      cyp_interactions: joinList(initialMedication?.cyp_interactions),
      pharmacodynamic_notes: initialMedication?.pharmacodynamic_notes ?? "",
      pharmacokinetic_notes: initialMedication?.pharmacokinetic_notes ?? "",
      clinical_interpretation: initialMedication?.clinical_interpretation ?? "",
      neuropsychiatric_cautions: joinList(initialMedication?.neuropsychiatric_cautions),
      reproductive_cautions: joinList(initialMedication?.reproductive_cautions),
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
      continuous_use: values.continuous_use,
      monitoring_required: values.monitoring_required,
      monitoring_notes: values.monitoring_notes || null,
      condition_specific_limits: parseLimits(values.condition_specific_limits ?? ""),
      allowed_routes: splitList(values.allowed_routes),
      contraindications: splitList(values.contraindications ?? ""),
      renal_caution: values.renal_caution,
      hepatic_caution: values.hepatic_caution,
      cardiac_caution: values.cardiac_caution,
      gastrointestinal_caution: values.gastrointestinal_caution,
      elderly_caution: values.elderly_caution,
      mechanism_of_action: values.mechanism_of_action || null,
      absorption_notes: values.absorption_notes || null,
      distribution_notes: values.distribution_notes || null,
      metabolism_organs: splitList(values.metabolism_organs ?? ""),
      elimination_organs: splitList(values.elimination_organs ?? ""),
      renal_elimination_level: values.renal_elimination_level || "nao_informado",
      hepatic_metabolism_level: values.hepatic_metabolism_level || "nao_informado",
      cyp_interactions: splitList(values.cyp_interactions ?? ""),
      pharmacodynamic_notes: values.pharmacodynamic_notes || null,
      pharmacokinetic_notes: values.pharmacokinetic_notes || null,
      clinical_interpretation: values.clinical_interpretation || null,
      neuropsychiatric_cautions: splitList(values.neuropsychiatric_cautions ?? ""),
      reproductive_cautions: splitList(values.reproductive_cautions ?? ""),
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
        continuous_use: false,
        monitoring_required: false,
        monitoring_notes: "",
        condition_specific_limits: "",
        allowed_routes: "",
        contraindications: "",
        renal_caution: false,
        hepatic_caution: false,
        cardiac_caution: false,
        gastrointestinal_caution: false,
        elderly_caution: false,
        mechanism_of_action: "",
        absorption_notes: "",
        distribution_notes: "",
        metabolism_organs: "",
        elimination_organs: "",
        renal_elimination_level: "nao_informado",
        hepatic_metabolism_level: "nao_informado",
        cyp_interactions: "",
        pharmacodynamic_notes: "",
        pharmacokinetic_notes: "",
        clinical_interpretation: "",
        neuropsychiatric_cautions: "",
        reproductive_cautions: "",
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
          label="Princípio ativo DCB"
          listId="active-ingredient-options"
          options={activeIngredientOptions}
          placeholder="dipirona"
          {...register("active_ingredient")}
        />

        <label className="grid gap-1.5">
          <span className="label">Classe terapêutica principal</span>
          <input
            className="field"
            placeholder="analgésico antitérmico"
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
          placeholder="analgésico, antitérmico"
          valuePreview={initialMedication ? joinList(initialMedication.therapeutic_classes) : ""}
          {...register("therapeutic_classes")}
        />

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

      <div className="grid gap-4 md:grid-cols-3">
        <ControlledSelect
          label="Jurisdição da fonte"
          options={[
            { value: "BR", label: "Brasil (BR)" },
            { value: "GLOBAL", label: "Global" },
            { value: "US", label: "Estados Unidos (US)" },
            { value: "EU", label: "União Europeia (EU)" },
          ]}
          {...register("source_jurisdiction")}
        />
        <ControlledSelect
          label="Fonte da evidência"
          options={[
            { value: "manual_curated", label: "Curadoria manual" },
            { value: "anvisa_bulario", label: "Anvisa/Bulário" },
            { value: "dcb", label: "DCB" },
            { value: "demo_seed", label: "Seed demonstrativo" },
            { value: "external_reference", label: "Referência externa" },
          ]}
          {...register("evidence_source_type")}
        />
        <ControlledSelect
          label="Status de validação"
          options={[
            { value: "pending_review", label: "Pendente de revisão" },
            { value: "demo", label: "Demonstrativo" },
            { value: "curated", label: "Curado" },
            { value: "validated", label: "Validado" },
          ]}
          {...register("validation_status")}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <label className="grid gap-1.5">
          <span className="label">Concentração</span>
          <input className="field" placeholder="500 mg/mL" {...register("concentration")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Forma farmacêutica</span>
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
        <span className="label">Limites por condição</span>
        <input
          className="field"
          placeholder="renal:1200, hepatico:800"
          {...register("condition_specific_limits")}
        />
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
            <input
              className="h-4 w-4 accent-ocean"
              type="checkbox"
              {...register(field as keyof MedicationFormValues)}
            />
            {label}
          </label>
        ))}
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <label className="flex min-h-11 items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700">
          <input className="h-4 w-4 accent-ocean" type="checkbox" {...register("continuous_use")} />
          Uso contínuo
        </label>
        <label className="flex min-h-11 items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700">
          <input
            className="h-4 w-4 accent-ocean"
            type="checkbox"
            {...register("monitoring_required")}
          />
          Monitoramento necessário
        </label>
      </div>

      <label className="grid gap-1.5">
        <span className="label">Notas de monitoramento</span>
        <input
          className="field"
          placeholder="revisar função renal/hepática, sinais clínicos"
          {...register("monitoring_notes")}
        />
      </label>

      <TagInput label="Vias permitidas" placeholder="oral, intravenosa" {...register("allowed_routes")} />
      {errors.allowed_routes ? (
        <span className="text-xs text-danger">{errors.allowed_routes.message}</span>
      ) : null}

      <TagInput
        label="Contraindicações estruturadas"
        placeholder="úlcera ativa, doença renal grave"
        {...register("contraindications")}
      />

      <div className="grid gap-4 md:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="label">Mecanismo de ação</span>
          <input className="field" {...register("mechanism_of_action")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Interpretação clínica</span>
          <input className="field" {...register("clinical_interpretation")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Absorção</span>
          <input className="field" {...register("absorption_notes")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Distribuição</span>
          <input className="field" {...register("distribution_notes")} />
        </label>
        <TagInput label="Metabolização/processamento" placeholder="hepático" {...register("metabolism_organs")} />
        <TagInput label="Eliminação principal" placeholder="renal" {...register("elimination_organs")} />
        <ControlledSelect
          label="Nível de eliminação renal"
          options={[
            { value: "nao_informado", label: "Não informado" },
            { value: "baixo", label: "Baixo" },
            { value: "moderado", label: "Moderado" },
            { value: "alto", label: "Alto" },
            { value: "critico_revisar", label: "Crítico/revisar" },
          ]}
          {...register("renal_elimination_level")}
        />
        <ControlledSelect
          label="Nível de metabolismo hepático"
          options={[
            { value: "nao_informado", label: "Não informado" },
            { value: "baixo", label: "Baixo" },
            { value: "moderado", label: "Moderado" },
            { value: "alto", label: "Alto" },
            { value: "critico_revisar", label: "Crítico/revisar" },
          ]}
          {...register("hepatic_metabolism_level")}
        />
        <TagInput label="Interações CYP" placeholder="cyp2c9_a_revisar" {...register("cyp_interactions")} />
        <TagInput
          label="Cautelas neuropsiquiátricas"
          placeholder="risco_serotoninergico, limiar_convulsivo"
          {...register("neuropsychiatric_cautions")}
        />
        <TagInput
          label="Cautelas reprodutivas/ginecológicas"
          placeholder="uso_anticoncepcional_hormonal, gestante"
          {...register("reproductive_cautions")}
        />
        <TagInput label="Órgãos envolvidos" placeholder="renal, gastrointestinal" {...register("organs_involved")} />
        <TagInput
          label="Efeitos adversos relevantes"
          placeholder="sangramento gastrointestinal, gastrite"
          {...register("relevant_adverse_effects")}
        />
        <TagInput
          label="Contraindicações por categoria"
          placeholder="renal, gastrointestinal"
          {...register("structured_contraindications")}
        />
        <label className="grid gap-1.5">
          <span className="label">Ação/finalidade</span>
          <input className="field" placeholder="analgesia" {...register("therapeutic_action")} />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Grupo de alternativas</span>
          <input className="field" placeholder="analgesia" {...register("alternative_group")} />
        </label>
        <TagInput label="Medicamentos relacionados" placeholder="paracetamol, ibuprofeno" {...register("related_medications")} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="grid gap-1.5">
        <span className="label">Notas farmacodinâmicas</span>
          <textarea className="field min-h-20 resize-y" {...register("pharmacodynamic_notes")} />
        </label>
        <label className="grid gap-1.5">
        <span className="label">Notas farmacocinéticas</span>
          <textarea className="field min-h-20 resize-y" {...register("pharmacokinetic_notes")} />
        </label>
      </div>

      <label className="grid gap-1.5">
        <span className="label">Fonte demonstrativa/observação da evidência</span>
        <input className="field" {...register("knowledge_source")} />
      </label>

      <label className="grid gap-1.5">
        <span className="label">Observações clínicas</span>
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
