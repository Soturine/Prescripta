export default function MedicationOrganProcessingCard({ factors }: { factors: string[] }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-bold text-ink">Fatores do medicamento considerados</h2>
      <div className="mt-3 flex flex-wrap gap-2">
        {factors.length ? (
          factors.map((factor) => (
            <span className="rounded-lg bg-cyan-50 px-3 py-2 text-sm font-semibold text-ocean" key={factor}>
              {factor}
            </span>
          ))
        ) : (
          <p className="text-sm text-slate-500">Nenhum fator farmacológico estruturado.</p>
        )}
      </div>
    </section>
  );
}
