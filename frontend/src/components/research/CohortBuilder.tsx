import { ArrowDown, ArrowUp, Copy, Plus, Trash2 } from "lucide-react";
import type { ReactElement } from "react";
import { useTranslation } from "react-i18next";

import type {
  CohortCriterion,
  CohortDefinitionV2,
  CohortGroup,
} from "../../types/research";

const kinds: CohortCriterion["criterion"][] = [
  "age",
  "sex",
  "condition",
  "drug_exposure",
  "measurement",
  "procedure",
  "visit",
  "medication_concurrency",
  "date_window",
];

function criterion(id: string): CohortCriterion {
  return {
    id,
    criterion: "age",
    operator: "gte",
    value: 18,
    window: {},
    temporal_relationship: null,
    label: "18+",
  };
}

function isGroup(item: CohortCriterion | CohortGroup): item is CohortGroup {
  return "items" in item;
}

export function initialCohortDefinition(): CohortDefinitionV2 {
  return {
    schema_version: "2",
    inclusion: {
      id: "inclusion",
      operator: "all",
      label: "Inclusão",
      items: [criterion("criterion-1")],
    },
    exclusion: {
      id: "exclusion",
      operator: "any",
      label: "Exclusão",
      items: [],
    },
  };
}

type Props = {
  value: CohortDefinitionV2;
  conceptVersions: Array<{ id: string; label: string }>;
  onChange: (value: CohortDefinitionV2) => void;
};

export default function CohortBuilder({
  value,
  conceptVersions,
  onChange,
}: Props) {
  const { t } = useTranslation();
  const count = [...value.inclusion.items, ...value.exclusion.items].reduce(
    (total, item) => total + (isGroup(item) ? item.items.length : 1),
    0,
  );
  const estimatedCost = count * 4 + 2;

  function updateGroup(phase: "inclusion" | "exclusion", group: CohortGroup) {
    onChange({ ...value, [phase]: group });
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap gap-2 text-xs font-bold text-slate-600">
        <span className="rounded-full bg-slate-100 px-3 py-1">DSL v2</span>
        <span className="rounded-full bg-slate-100 px-3 py-1">
          {t("research.builder.criteriaCount", { count })}
        </span>
        <span className="rounded-full bg-slate-100 px-3 py-1">
          {t("research.builder.cost", { cost: estimatedCost })}
        </span>
        <span className="rounded-full bg-slate-100 px-3 py-1">
          {t("research.builder.depth")}
        </span>
      </div>
      {(["inclusion", "exclusion"] as const).map((phase) => (
        <CriteriaGroup
          conceptVersions={conceptVersions}
          group={value[phase]}
          key={phase}
          onChange={(group) => updateGroup(phase, group)}
          phase={phase}
        />
      ))}
      {estimatedCost > 100 ? (
        <p className="text-sm font-bold text-red-700" role="alert">
          {t("research.builder.costExceeded")}
        </p>
      ) : null}
    </div>
  );
}

function CriteriaGroup({
  group,
  phase,
  conceptVersions,
  onChange,
}: {
  group: CohortGroup;
  phase: "inclusion" | "exclusion";
  conceptVersions: Array<{ id: string; label: string }>;
  onChange: (group: CohortGroup) => void;
}) {
  const { t } = useTranslation();
  function setItems(items: Array<CohortCriterion | CohortGroup>) {
    onChange({ ...group, items });
  }

  function addCriterion() {
    setItems([...group.items, criterion(`${phase}-${Date.now()}`)]);
  }

  function addGroup() {
    setItems([
      ...group.items,
      {
        id: `${phase}-group-${Date.now()}`,
        operator: "any",
        label: t("research.builder.alternativeGroup"),
        items: [criterion(`${phase}-nested-${Date.now()}`)],
      },
    ]);
  }

  function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= group.items.length) return;
    const next = [...group.items];
    [next[index], next[target]] = [next[target], next[index]];
    setItems(next);
  }

  return (
    <fieldset className="rounded-2xl border border-slate-200 p-4">
      <legend className="px-2 text-sm font-black">
        {phase === "inclusion"
          ? t("research.builder.inclusion")
          : t("research.builder.exclusion")}
      </legend>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <label className="text-xs font-bold">
          {t("research.builder.combination")}
          <select
            className="field ml-2"
            onChange={(event) =>
              onChange({
                ...group,
                operator: event.target.value as "all" | "any",
              })
            }
            value={group.operator}
          >
            <option value="all">{t("research.builder.all")}</option>
            <option value="any">{t("research.builder.any")}</option>
          </select>
        </label>
        <button className="btn-secondary" onClick={addCriterion} type="button">
          <Plus aria-hidden="true" className="h-4 w-4" />{" "}
          {t("research.builder.criterion")}
        </button>
        <button className="btn-secondary" onClick={addGroup} type="button">
          <Plus aria-hidden="true" className="h-4 w-4" />{" "}
          {t("research.builder.group")}
        </button>
      </div>
      <div className="grid gap-3">
        {group.items.map((item, index) => (
          <div className="rounded-xl bg-slate-50 p-3" key={item.id ?? index}>
            {isGroup(item) ? (
              <NestedGroup
                conceptVersions={conceptVersions}
                group={item}
                onChange={(next) => {
                  const items = [...group.items];
                  items[index] = next;
                  setItems(items);
                }}
              />
            ) : (
              <CriterionEditor
                conceptVersions={conceptVersions}
                criterionValue={item}
                onChange={(next) => {
                  const items = [...group.items];
                  items[index] = next;
                  setItems(items);
                }}
              />
            )}
            <div className="mt-2 flex justify-end gap-1">
              <IconButton
                label={t("research.builder.moveUp")}
                onClick={() => move(index, -1)}
              >
                <ArrowUp />
              </IconButton>
              <IconButton
                label={t("research.builder.moveDown")}
                onClick={() => move(index, 1)}
              >
                <ArrowDown />
              </IconButton>
              <IconButton
                label={t("research.builder.duplicate")}
                onClick={() => {
                  const clone = structuredClone(item);
                  clone.id = `${phase}-copy-${Date.now()}`;
                  setItems([
                    ...group.items.slice(0, index + 1),
                    clone,
                    ...group.items.slice(index + 1),
                  ]);
                }}
              >
                <Copy />
              </IconButton>
              <IconButton
                label={t("research.builder.delete")}
                onClick={() =>
                  setItems(
                    group.items.filter((_, itemIndex) => itemIndex !== index),
                  )
                }
              >
                <Trash2 />
              </IconButton>
            </div>
          </div>
        ))}
        {!group.items.length ? (
          <p className="text-sm text-slate-500">
            {t("research.builder.empty")}
          </p>
        ) : null}
      </div>
    </fieldset>
  );
}

function NestedGroup({
  group,
  conceptVersions,
  onChange,
}: {
  group: CohortGroup;
  conceptVersions: Array<{ id: string; label: string }>;
  onChange: (group: CohortGroup) => void;
}) {
  const { t } = useTranslation();
  return (
    <div>
      <label className="text-xs font-bold">
        {t("research.builder.nestedGroup")}
        <select
          className="field ml-2"
          onChange={(event) =>
            onChange({
              ...group,
              operator: event.target.value as "all" | "any",
            })
          }
          value={group.operator}
        >
          <option value="all">{t("research.builder.all")}</option>
          <option value="any">{t("research.builder.any")}</option>
        </select>
      </label>
      <div className="mt-3 grid gap-2">
        {group.items
          .filter((item): item is CohortCriterion => !isGroup(item))
          .map((item, index) => (
            <CriterionEditor
              conceptVersions={conceptVersions}
              criterionValue={item}
              key={item.id ?? index}
              onChange={(next) => {
                const items = [...group.items];
                items[index] = next;
                onChange({ ...group, items });
              }}
            />
          ))}
      </div>
    </div>
  );
}

function CriterionEditor({
  criterionValue,
  conceptVersions,
  onChange,
}: {
  criterionValue: CohortCriterion;
  conceptVersions: Array<{ id: string; label: string }>;
  onChange: (criterionValue: CohortCriterion) => void;
}) {
  const { t } = useTranslation();
  const needsConcept = [
    "condition",
    "drug_exposure",
    "measurement",
    "procedure",
    "medication_concurrency",
  ].includes(criterionValue.criterion);

  function selectKind(kind: CohortCriterion["criterion"]) {
    const exists = !["age", "sex", "date_window"].includes(kind);
    onChange({
      ...criterionValue,
      criterion: kind,
      operator: exists ? "exists" : kind === "age" ? "gte" : "eq",
      value: exists ? null : kind === "age" ? 18 : "",
      concept_set_version_id: exists ? (conceptVersions[0]?.id ?? null) : null,
      label: t(`research.builder.criteria.${kind}`),
    });
  }

  return (
    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
      <label className="grid gap-1 text-xs font-bold">
        {t("research.builder.type")}
        <select
          className="field"
          onChange={(event) =>
            selectKind(event.target.value as CohortCriterion["criterion"])
          }
          value={criterionValue.criterion}
        >
          {kinds.map((item) => (
            <option key={item} value={item}>
              {t(`research.builder.criteria.${item}`)}
            </option>
          ))}
        </select>
      </label>
      <label className="grid gap-1 text-xs font-bold">
        {t("research.builder.operator")}
        <select
          className="field"
          disabled={needsConcept}
          onChange={(event) =>
            onChange({ ...criterionValue, operator: event.target.value })
          }
          value={criterionValue.operator}
        >
          {(criterionValue.criterion === "age"
            ? ["eq", "gte", "lte", "between"]
            : criterionValue.criterion === "sex"
              ? ["eq", "in"]
              : criterionValue.criterion === "date_window"
                ? ["before", "after", "between"]
                : ["exists"]
          ).map((operator) => (
            <option key={operator}>{operator}</option>
          ))}
        </select>
      </label>
      {needsConcept ? (
        <label className="grid gap-1 text-xs font-bold sm:col-span-2">
          {t("research.builder.reviewedConcept")}
          <select
            className="field"
            onChange={(event) =>
              onChange({
                ...criterionValue,
                concept_set_version_id: event.target.value,
              })
            }
            value={criterionValue.concept_set_version_id ?? ""}
          >
            <option value="">{t("research.builder.select")}</option>
            {conceptVersions.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      ) : (
        <label className="grid gap-1 text-xs font-bold">
          {t("research.builder.value")}
          <input
            className="field"
            onChange={(event) =>
              onChange({
                ...criterionValue,
                value:
                  criterionValue.criterion === "age"
                    ? Number(event.target.value)
                    : event.target.value,
              })
            }
            type={criterionValue.criterion === "age" ? "number" : "text"}
            value={String(criterionValue.value ?? "")}
          />
        </label>
      )}
      <label className="grid gap-1 text-xs font-bold">
        {t("research.builder.temporality")}
        <select
          className="field"
          onChange={(event) =>
            onChange({
              ...criterionValue,
              temporal_relationship: (event.target.value ||
                null) as CohortCriterion["temporal_relationship"],
            })
          }
          value={criterionValue.temporal_relationship ?? ""}
        >
          <option value="">{t("research.builder.notApplicable")}</option>
          <option value="before_index">
            {t("research.builder.beforeIndex")}
          </option>
          <option value="after_index">
            {t("research.builder.afterIndex")}
          </option>
          <option value="on_index">{t("research.builder.onIndex")}</option>
          <option value="during_window">
            {t("research.builder.duringWindow")}
          </option>
        </select>
      </label>
    </div>
  );
}

function IconButton({
  label,
  onClick,
  children,
}: {
  label: string;
  onClick: () => void;
  children: ReactElement;
}) {
  return (
    <button
      aria-label={label}
      className="rounded-lg p-2 text-slate-500 hover:bg-white hover:text-ocean"
      onClick={onClick}
      type="button"
    >
      {children}
    </button>
  );
}
