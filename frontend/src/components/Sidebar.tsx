import { Menu, X } from "lucide-react";
import { useState } from "react";
import { NavLink } from "react-router-dom";

import { APP_SUBTITLE, APP_VERSION } from "../config/appVersion";
import { APP_ROUTES } from "../config/routes";
import { useAuth } from "../context/AuthContext";

export default function Sidebar() {
  const { canAccess } = useAuth();
  const [open, setOpen] = useState(false);
  const visibleLinks = APP_ROUTES.filter((item) => canAccess(item.roles));
  const navigation = (
    <nav aria-label="Navegação principal" className="grid gap-1.5">
      {visibleLinks.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            onClick={() => setOpen(false)}
            className={({ isActive }) =>
              [
                "inline-flex min-h-11 items-center gap-3 rounded-xl px-3 py-2 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ocean",
                isActive
                  ? "bg-ocean text-white shadow-soft"
                  : "text-slate-600 hover:bg-cyan-50 hover:text-ink",
              ].join(" ")
            }
          >
            <Icon aria-hidden="true" className="h-5 w-5" />
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );

  return (
    <>
      <div className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur lg:hidden">
        <div>
          <p className="font-bold text-ink">Prescripta</p>
          <p className="text-xs text-slate-500">{APP_VERSION}</p>
        </div>
        <button aria-expanded={open} aria-label="Abrir menu" className="btn-secondary min-h-11 min-w-11 px-3" onClick={() => setOpen(true)} type="button">
          <Menu aria-hidden="true" className="h-5 w-5" />
        </button>
      </div>
      {open ? <button aria-label="Fechar menu" className="fixed inset-0 z-40 bg-slate-950/35 backdrop-blur-sm lg:hidden" onClick={() => setOpen(false)} type="button" /> : null}
      <aside className={`${open ? "translate-x-0" : "-translate-x-full"} fixed inset-y-0 left-0 z-50 w-[min(88vw,19rem)] border-r border-slate-200 bg-white p-5 shadow-2xl transition-transform lg:sticky lg:top-0 lg:z-20 lg:min-h-screen lg:w-72 lg:translate-x-0 lg:shadow-none`}>
        <div className="flex h-full flex-col gap-7">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-2xl font-bold tracking-tight text-ink">Prescripta</div>
              <div className="mt-1 text-xs font-medium text-slate-500">{APP_SUBTITLE}</div>
              <div className="mt-3 inline-flex rounded-lg bg-cyan-50 px-2.5 py-1 text-xs font-bold text-ocean">{APP_VERSION}</div>
            </div>
            <button aria-label="Fechar menu" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden" onClick={() => setOpen(false)} type="button"><X aria-hidden="true" className="h-5 w-5" /></button>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto">{navigation}</div>
          <p className="text-xs leading-5 text-slate-400">Ambiente demonstrativo. IA não decide.</p>
        </div>
      </aside>
    </>
  );
}
