type SourceBadgeProps = {
  source: string | null | undefined;
  jurisdiction?: string | null;
  status?: string | null;
};

const sourceLabels: Record<string, string> = {
  anvisa_bulario: "Anvisa",
  dcb: "DCB",
  manual_curated: "Manual",
  demo_seed: "Demo",
  external_reference: "Externa",
  rag_demo: "RAG demo",
  seed_demo: "Seed demo",
  ai_provider: "IA",
  fallback_deterministic: "Fallback",
};

export default function SourceBadge({ source, jurisdiction, status }: SourceBadgeProps) {
  const sourceValue = source ?? "demo_seed";
  const label = sourceLabels[sourceValue] ?? sourceValue;
  const pending = status === "pending_review";
  return (
    <span
      className={`inline-flex min-h-7 items-center rounded-lg px-2.5 py-1 text-xs font-bold ${
        pending
          ? "border border-amber-200 bg-amber-50 text-amber-900"
          : "border border-cyan-100 bg-cyan-50 text-cyan-900"
      }`}
    >
      {label}
      {jurisdiction ? ` · ${jurisdiction}` : ""}
      {pending ? " · pendente" : ""}
    </span>
  );
}
