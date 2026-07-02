import { ShieldX } from "lucide-react";
import { Link } from "react-router-dom";

export default function AccessDenied() {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 text-amber-900">
      <ShieldX aria-hidden="true" className="h-8 w-8" />
      <h1 className="mt-3 text-2xl font-bold tracking-normal">Acesso negado</h1>
      <p className="mt-2 max-w-2xl text-sm leading-6">
        Seu perfil não tem permissão para acessar esta área. O backend também bloqueia essa ação.
      </p>
      <Link className="btn-secondary mt-5 w-fit" to="/">
        Voltar ao dashboard
      </Link>
    </div>
  );
}
