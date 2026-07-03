import type { RagEvidence } from "../types/prescription";

export default function RagEvidencePanel({ evidence }: { evidence: RagEvidence[] }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-bold text-ink">Evidências internas/RAG</h2>
      <div className="mt-3 grid gap-3">
        {evidence.map((item) => (
          <article className="rounded-lg border border-slate-100 bg-slate-50 p-4" key={item.source}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-bold text-ink">{item.source}</h3>
              <span className="text-xs font-semibold text-slate-500">score {item.score}</span>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.excerpt}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
