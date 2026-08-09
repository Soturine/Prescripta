import { ChevronRight, CircleHelp, LogOut, Menu, ShieldCheck, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";

import { APP_ROUTES, findRoute } from "../config/routes";
import { useAuth } from "../context/AuthContext";
import type { Capability } from "../types/user";
import { formatRole } from "../utils/formatters";
import LanguageSelector from "./LanguageSelector";
import Sidebar from "./Sidebar";
import Badge from "./ui/Badge";

const SIDEBAR_PREFERENCE = "prescripta:sidebar-collapsed";

export default function Layout() {
  const { logout, user, can } = useAuth();
  const { t } = useTranslation();
  const location = useLocation();
  const route = findRoute(location.pathname);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [online, setOnline] = useState(() => navigator.onLine);
  const [collapsed, setCollapsed] = useState(
    () => window.localStorage.getItem(SIDEBAR_PREFERENCE) === "true",
  );
  const visibleRoutes = APP_ROUTES.filter(
    (item) => item.capability === null || can(item.capability as Capability),
  );
  const mobileRoutes = visibleRoutes
    .filter((item) => ["/", "/patients", "/prescription-check", "/pharmacy", "/help"].includes(item.to))
    .slice(0, 4);

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
      <a className="skip-link" href="#main-content">{t("shell.skipContent")}</a>
      <Sidebar
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onCollapsedChange={setCollapsed}
        onMobileOpenChange={setMobileOpen}
      />
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-30 border-b border-cyan-950/10 bg-white/95 backdrop-blur-xl">
          <div className="flex min-h-16 items-center gap-2 px-4 sm:gap-3 sm:px-6 lg:px-8">
            <button
              aria-expanded={mobileOpen}
              aria-label={t("shell.openNavigation")}
              className="icon-button lg:hidden"
              onClick={() => setMobileOpen(true)}
              type="button"
            >
              <Menu aria-hidden="true" className="h-5 w-5" />
            </button>

            <nav aria-label={t("shell.breadcrumb")} className="min-w-0 flex-1">
              <ol className="flex items-center gap-1.5 text-sm">
                <li className="hidden font-semibold text-slate-500 sm:block">Prescripta</li>
                <li className="hidden sm:block"><ChevronRight aria-hidden="true" className="h-4 w-4 text-slate-300" /></li>
                <li aria-current="page" className="truncate font-black text-ink">
                  {route ? t(route.labelKey) : t("shell.workspaceFallback")}
                </li>
              </ol>
            </nav>

            {!online ? <Badge tone="warning">{t("common.offline")}</Badge> : null}
            <span className="hidden sm:inline-flex"><Badge tone="info">{t("common.demoEnvironment")}</Badge></span>
            <Link aria-label={t("common.help")} className="icon-button hidden sm:inline-flex" to="/help"><CircleHelp aria-hidden="true" className="h-5 w-5" /></Link>
            <LanguageSelector compact />

            <details className="group relative">
              <summary className="flex min-h-11 list-none items-center gap-2 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-left shadow-xs transition hover:border-cyan-300">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-50 text-ocean"><UserRound aria-hidden="true" className="h-4 w-4" /></span>
                <span className="hidden max-w-44 sm:block">
                  <span className="block truncate text-xs font-extrabold text-ink">{user?.name}</span>
                  <span className="block truncate text-[0.6875rem] text-slate-500">{formatRole(user?.role)}</span>
                </span>
              </summary>
              <div className="absolute right-0 mt-2 w-[min(19rem,calc(100vw-2rem))] rounded-2xl border border-slate-200 bg-white p-3 shadow-xl">
                <div className="border-b border-slate-100 px-2 pb-3">
                  <p className="font-extrabold text-ink">{user?.name}</p>
                  <p className="mt-0.5 break-all text-xs text-slate-500">{user?.email}</p>
                  <p className="mt-2 text-xs font-semibold text-slate-600">{formatRole(user?.role)}{user?.specialty_codes?.length ? ` · ${user.specialty_codes.join(", ")}` : ""}</p>
                </div>
                <div className="my-3 flex items-center gap-2 px-2 text-xs font-semibold text-emerald-800"><ShieldCheck aria-hidden="true" className="h-4 w-4" />{t("shell.protectedSession")}</div>
                <button className="btn-secondary w-full" onClick={logout} type="button"><LogOut aria-hidden="true" className="h-4 w-4" />{t("shell.logout")}</button>
              </div>
            </details>
          </div>
        </header>

        <main className="min-h-[calc(100vh-4rem)] px-4 py-6 pb-24 outline-none sm:px-6 lg:px-8 lg:py-8" id="main-content" tabIndex={-1}>
          <div className="page-enter mx-auto w-full max-w-[90rem]" key={location.pathname}>
            {!online ? <div className="mb-5 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-950" role="status">{t("shell.offlineWarning")}</div> : null}
            <Outlet />
          </div>
        </main>

        <nav aria-label={t("shell.mobileNavigation")} className="fixed inset-x-0 bottom-0 z-30 grid min-h-16 border-t border-cyan-950/10 bg-white/97 px-2 pb-[env(safe-area-inset-bottom)] shadow-[0_-8px_24px_-20px_rgba(15,23,42,.45)] lg:hidden" style={{ gridTemplateColumns: `repeat(${Math.max(mobileRoutes.length, 1)}, minmax(0, 1fr))` }}>
          {mobileRoutes.map((item) => {
            const Icon = item.icon;
            return <NavLink className={({ isActive }) => `flex min-h-16 flex-col items-center justify-center gap-1 px-1 text-[0.6875rem] font-extrabold ${isActive ? "text-ocean" : "text-slate-500"}`} end={item.to === "/"} key={item.to} to={item.to}><Icon aria-hidden="true" className="h-5 w-5" /><span className="max-w-full truncate">{t(item.shortLabelKey ?? item.labelKey)}</span></NavLink>;
          })}
        </nav>
      </div>
    </div>
  );
}
