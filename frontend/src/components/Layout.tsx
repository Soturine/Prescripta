import { ChevronRight, LogOut, Menu, ShieldCheck, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { findRoute } from "../config/routes";
import { useAuth } from "../context/AuthContext";
import { PROFESSION_LABELS } from "../config/labels";
import { formatRole } from "../utils/formatters";
import Badge from "./ui/Badge";
import Sidebar from "./Sidebar";

const SIDEBAR_PREFERENCE = "prescripta:sidebar-collapsed";

export default function Layout() {
  const { logout, user } = useAuth();
  const location = useLocation();
  const route = findRoute(location.pathname);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [online, setOnline] = useState(() => navigator.onLine);
  const [collapsed, setCollapsed] = useState(
    () => window.localStorage.getItem(SIDEBAR_PREFERENCE) === "true",
  );

  useEffect(() => {
    window.localStorage.setItem(SIDEBAR_PREFERENCE, String(collapsed));
  }, [collapsed]);

  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  useEffect(() => {
    setMobileOpen(false);
    const frame = window.requestAnimationFrame(() => {
      document.getElementById("page-title")?.focus();
    });
    return () => window.cancelAnimationFrame(frame);
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-canvas text-ink lg:flex">
      <a className="skip-link" href="#main-content">Pular para o conteúdo</a>
      <Sidebar
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onCollapsedChange={setCollapsed}
        onMobileOpenChange={setMobileOpen}
      />
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-30 border-b border-slate-200/90 bg-white/95 backdrop-blur-xl">
          <div className="flex min-h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
            <button
              aria-expanded={mobileOpen}
              aria-label="Abrir navegação"
              className="icon-button lg:hidden"
              onClick={() => setMobileOpen(true)}
              type="button"
            >
              <Menu aria-hidden="true" className="h-5 w-5" />
            </button>

            <nav aria-label="Breadcrumb" className="min-w-0 flex-1">
              <ol className="flex items-center gap-1.5 text-sm">
                <li className="hidden font-semibold text-slate-500 sm:block">Prescripta</li>
                <li className="hidden sm:block">
                  <ChevronRight aria-hidden="true" className="h-4 w-4 text-slate-300" />
                </li>
                <li aria-current="page" className="truncate font-bold text-ink">
                  {route?.label ?? "Workspace"}
                </li>
              </ol>
            </nav>

            {!online ? <Badge tone="warning">Offline</Badge> : null}
            <Badge tone="info">Ambiente demo</Badge>

            <details className="group relative">
              <summary className="flex min-h-11 list-none items-center gap-2 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-left shadow-xs transition hover:border-slate-300">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-50 text-ocean">
                  <UserRound aria-hidden="true" className="h-4 w-4" />
                </span>
                <span className="hidden max-w-44 sm:block">
                  <span className="block truncate text-xs font-extrabold text-ink">{user?.name}</span>
                  <span className="block truncate text-[0.6875rem] text-slate-500">{formatRole(user?.role)}</span>
                </span>
              </summary>
              <div className="absolute right-0 mt-2 w-[min(19rem,calc(100vw-2rem))] rounded-2xl border border-slate-200 bg-white p-3 shadow-xl">
                <div className="border-b border-slate-100 px-2 pb-3">
                  <p className="font-extrabold text-ink">{user?.name}</p>
                  <p className="mt-0.5 break-all text-xs text-slate-500">{user?.email}</p>
                  <p className="mt-2 text-xs font-semibold text-slate-600">
                    {user?.profession ? PROFESSION_LABELS[user.profession] : formatRole(user?.role)}
                    {user?.specialty_codes?.length ? ` · ${user.specialty_codes.join(", ")}` : ""}
                  </p>
                </div>
                <div className="my-3 flex items-center gap-2 px-2 text-xs font-semibold text-emerald-800">
                  <ShieldCheck aria-hidden="true" className="h-4 w-4" />
                  Sessão protegida · cookie HttpOnly
                </div>
                <button className="btn-secondary w-full" onClick={logout} type="button">
                  <LogOut aria-hidden="true" className="h-4 w-4" />
                  Encerrar sessão
                </button>
              </div>
            </details>
          </div>
        </header>

        <main
          className="min-h-[calc(100vh-4rem)] px-4 py-6 outline-none sm:px-6 lg:px-8 lg:py-8"
          id="main-content"
          tabIndex={-1}
        >
          <div className="page-enter mx-auto w-full max-w-[90rem]" key={location.pathname}>
            {!online ? (
              <div className="mb-5 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-950" role="status">
                Sem conexão. Dados em tela podem estar desatualizados; reconecte para executar ações.
              </div>
            ) : null}
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
