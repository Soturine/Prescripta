import type { RagEvidence } from "../types/prescription";
import { joinList } from "../utils/formatters";
import SourceBadge from "./SourceBadge";

export default function RagEvidencePanel({ evidence }: { evidence: RagEvidence[] }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-bold text-ink">Evidencias internas/RAG</h2>
      <div className="mt-3 grid gap-3">
        {evidence.map((item) => (
          <article className="rounded-lg border border-slate-100 bg-slate-50 p-4" key={item.source}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-bold text-ink">{item.source_name || item.source}</h3>
                <p className="mt-1 text-xs font-semibold text-slate-500">
                  {item.active_ingredient ? `Principio ativo: ${item.active_ingredient}` : item.source}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <SourceBadge
                  jurisdiction={item.jurisdiction}
                  source={item.evidence_type}
                  status={item.validation_status}
                />
                <span className="text-xs font-semibold text-slate-500">score {item.score}</span>
              </div>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.excerpt}</p>
            <div className="mt-3 grid gap-1 text-xs font-semibold text-slate-500">
              <span>Comerciais: {joinList(item.commercial_names) || "-"}</span>
              <span>Secoes: {joinList(item.extracted_sections) || "-"}</span>
              <span>Versao: {item.version}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
