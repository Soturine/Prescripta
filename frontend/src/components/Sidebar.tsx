import { ChevronLeft, ChevronRight, ShieldCheck, X } from "lucide-react";
import { useEffect, useRef } from "react";
import { NavLink } from "react-router-dom";

import { APP_SUBTITLE, APP_VERSION } from "../config/appVersion";
import { APP_ROUTES, NAV_SECTION_LABELS } from "../config/routes";
import { useAuth } from "../context/AuthContext";
import type { Capability } from "../types/user";

type SidebarProps = {
  collapsed: boolean;
  mobileOpen: boolean;
  onCollapsedChange: (value: boolean) => void;
  onMobileOpenChange: (value: boolean) => void;
};

const sections = ["workspace", "clinical", "evidence", "governance"] as const;

export default function Sidebar({
  collapsed,
  mobileOpen,
  onCollapsedChange,
  onMobileOpenChange,
}: SidebarProps) {
  const { can } = useAuth();
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const visibleLinks = APP_ROUTES.filter((item) => can(item.capability as Capability));

  useEffect(() => {
    if (!mobileOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onMobileOpenChange(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [mobileOpen, onMobileOpenChange]);

  return (
    <>
      {mobileOpen ? (
        <button
          aria-label="Fechar navegação"
          className="fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-xs lg:hidden"
          onClick={() => onMobileOpenChange(false)}
          type="button"
        />
      ) : null}
      <aside
        aria-label="Navegação da aplicação"
        aria-modal={mobileOpen ? "true" : undefined}
        className={`${mobileOpen ? "translate-x-0" : "-translate-x-full"} fixed inset-y-0 left-0 z-50 flex w-[min(88vw,20rem)] flex-col border-r border-slate-800 bg-ink text-white shadow-2xl transition-[width,transform] duration-200 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 lg:shadow-none ${collapsed ? "lg:w-[5.25rem]" : "lg:w-72"}`}
      >
        <div className="flex min-h-20 items-center gap-3 border-b border-white/10 px-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-400 text-lg font-black text-slate-950 shadow-[inset_0_0_0_1px_rgba(255,255,255,.3)]">
            P
          </div>
          <div className={`${collapsed ? "lg:hidden" : ""} min-w-0 flex-1`}>
            <p className="truncate text-lg font-black tracking-[-0.03em]">Prescripta</p>
            <p className="truncate text-[0.6875rem] font-medium text-slate-400">{APP_SUBTITLE}</p>
          </div>
          <button
            aria-label="Fechar navegação"
            className="icon-button border-white/10 bg-white/5 text-white hover:bg-white/10 lg:hidden"
            onClick={() => onMobileOpenChange(false)}
            ref={closeButtonRef}
            type="button"
          >
            <X aria-hidden="true" className="h-5 w-5" />
          </button>
        </div>

        <nav aria-label="Navegação principal" className="min-h-0 flex-1 overflow-y-auto px-3 py-5">
          {sections.map((section) => {
            const links = visibleLinks.filter((item) => item.section === section);
            if (!links.length) return null;
            return (
              <div className="mb-6" key={section}>
                <p className={`${collapsed ? "lg:sr-only" : ""} mb-2 px-3 text-[0.625rem] font-extrabold uppercase tracking-[0.16em] text-slate-500`}>
                  {NAV_SECTION_LABELS[section]}
                </p>
                <div className="grid gap-1">
                  {links.map((item) => {
                    const Icon = item.icon;
                    return (
                      <NavLink
                        aria-label={collapsed ? item.label : undefined}
                        className={({ isActive }) => [
                          "group relative flex min-h-11 items-center gap-3 rounded-xl px-3 py-2 text-sm font-bold outline-hidden transition-colors focus-visible:ring-2 focus-visible:ring-cyan-300",
                          isActive
                            ? "bg-white/12 text-white"
                            : "text-slate-300 hover:bg-white/7 hover:text-white",
                          collapsed ? "lg:justify-center" : "",
                        ].join(" ")}
                        end={item.to === "/"}
                        key={item.to}
                        onClick={() => onMobileOpenChange(false)}
                        title={collapsed ? item.label : undefined}
                        to={item.to}
                      >
                        {({ isActive }) => (
                          <>
                            {isActive ? <span aria-hidden="true" className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-cyan-300" /> : null}
                            <Icon aria-hidden="true" className="h-5 w-5 shrink-0" />
                            <span className={collapsed ? "lg:sr-only" : ""}>{item.label}</span>
                          </>
                        )}
                      </NavLink>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </nav>

        <div className="border-t border-white/10 p-3">
          <div className={`${collapsed ? "lg:hidden" : ""} rounded-xl bg-white/6 p-3`}>
            <div className="flex items-center gap-2 text-xs font-bold text-cyan-200">
              <ShieldCheck aria-hidden="true" className="h-4 w-4" />
              Segurança demonstrativa
            </div>
            <p className="mt-2 text-[0.6875rem] leading-5 text-slate-400">IA explica; regras determinísticas decidem. {APP_VERSION}</p>
          </div>
          <button
            aria-label={collapsed ? "Expandir barra lateral" : "Recolher barra lateral"}
            className="mt-2 hidden min-h-10 w-full items-center justify-center gap-2 rounded-xl text-xs font-bold text-slate-400 transition hover:bg-white/7 hover:text-white lg:flex"
            onClick={() => onCollapsedChange(!collapsed)}
            type="button"
          >
            {collapsed ? <ChevronRight aria-hidden="true" className="h-4 w-4" /> : <ChevronLeft aria-hidden="true" className="h-4 w-4" />}
            <span className={collapsed ? "sr-only" : ""}>{collapsed ? "Expandir" : "Recolher"}</span>
          </button>
        </div>
      </aside>
    </>
  );
}
