import type { ClinicalContextGraph as PrescriptionGraph } from "../types/prescription";
import type { ClinicalContextGraph as PatientGraph } from "../types/patient";

type Graph = PrescriptionGraph | PatientGraph;

export default function ClinicalContextGraphCard({ graph }: { graph: Graph }) {
  const nodeLabels = Object.fromEntries(graph.nodes.map((node) => [node.id, node.label]));

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-bold text-ink">Mapa de contexto clínico</h2>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div>
          <h3 className="text-sm font-bold text-ink">Nós</h3>
          <ul className="mt-2 grid gap-2 text-sm text-slate-600">
            {graph.nodes.map((node) => (
              <li className="rounded-lg bg-slate-50 px-3 py-2" key={node.id}>
                <span className="font-semibold text-ink">{node.type}:</span> {node.label}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-sm font-bold text-ink">Relações</h3>
          <ul className="mt-2 grid gap-2 text-sm text-slate-600">
            {graph.edges.map((edge, index) => (
              <li className="rounded-lg bg-slate-50 px-3 py-2" key={`${edge.from}-${edge.to}-${index}`}>
                {nodeLabels[edge.from] ?? edge.from} → {nodeLabels[edge.to] ?? edge.to}: {edge.label}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
