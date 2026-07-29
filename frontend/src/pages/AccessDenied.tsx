import { ShieldX } from "lucide-react";
import { Link } from "react-router-dom";

export default function AccessDenied() {
  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-950 shadow-sm">
      <ShieldX aria-hidden="true" className="h-8 w-8" />
      <h1 className="mt-3 text-2xl font-bold tracking-normal">Acesso negado</h1>
      <p className="mt-2 max-w-2xl text-sm leading-6">
        Sua sessão não possui a capacidade necessária para esta área. O backend aplica a mesma política e, em dados de paciente, também exige vínculo e finalidade compatíveis.
      </p>
      <Link className="btn-secondary mt-5 w-fit" to="/">
        Voltar ao dashboard
      </Link>
    </div>
  );
}
