import { ChevronLeft, ChevronRight, HeartPulse, ShieldCheck, X } from "lucide-react";
import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";

import { APP_VERSION } from "../config/appVersion";
import { APP_ROUTES, NAV_SECTION_KEYS } from "../config/routes";
import { useAuth } from "../context/AuthContext";
import type { Capability } from "../types/user";

type SidebarProps = {
  collapsed: boolean;
  mobileOpen: boolean;
  onCollapsedChange: (value: boolean) => void;
  onMobileOpenChange: (value: boolean) => void;
};

const sections = ["workspace", "clinical", "evidence", "research", "governance", "help"] as const;

export default function Sidebar({ collapsed, mobileOpen, onCollapsedChange, onMobileOpenChange }: SidebarProps) {
  const { can } = useAuth();
  const { t } = useTranslation();
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const visibleLinks = APP_ROUTES.filter((item) => item.capability === null || can(item.capability as Capability));

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
      {mobileOpen ? <button aria-label={t("shell.closeNavigation")} className="fixed inset-0 z-40 bg-slate-950/35 backdrop-blur-xs lg:hidden" onClick={() => onMobileOpenChange(false)} type="button" /> : null}
      <aside
        aria-label={t("shell.navigation")}
        aria-modal={mobileOpen ? "true" : undefined}
        className={`${mobileOpen ? "translate-x-0" : "-translate-x-full"} fixed inset-y-0 left-0 z-50 flex w-[min(88vw,20rem)] flex-col border-r border-cyan-950/10 bg-[#f7fbfb] text-ink shadow-2xl transition-[width,transform] duration-200 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 lg:shadow-none ${collapsed ? "lg:w-[5.25rem]" : "lg:w-72"}`}
      >
        <div className="flex min-h-20 items-center gap-3 border-b border-cyan-950/10 px-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-ocean text-white shadow-soft"><HeartPulse aria-hidden="true" className="h-6 w-6" /></div>
          <div className={`${collapsed ? "lg:hidden" : ""} min-w-0 flex-1`}>
            <p className="truncate text-lg font-black tracking-[-0.03em]">Prescripta</p>
            <p className="truncate text-[0.6875rem] font-medium text-slate-500">{t("shell.subtitle")}</p>
          </div>
          <button aria-label={t("shell.closeNavigation")} className="icon-button lg:hidden" onClick={() => onMobileOpenChange(false)} ref={closeButtonRef} type="button"><X aria-hidden="true" className="h-5 w-5" /></button>
        </div>

        <nav aria-label={t("shell.primaryNavigation")} className="min-h-0 flex-1 overflow-y-auto px-3 py-5">
          {sections.map((section) => {
            const links = visibleLinks.filter((item) => item.section === section);
            if (!links.length) return null;
            return (
              <div className="mb-6" key={section}>
                <p className={`${collapsed ? "lg:sr-only" : ""} mb-2 px-3 text-[0.625rem] font-extrabold uppercase tracking-[0.16em] text-slate-500`}>{t(NAV_SECTION_KEYS[section])}</p>
                <div className="grid gap-1">
                  {links.map((item) => {
                    const Icon = item.icon;
                    const label = t(item.labelKey);
                    return (
                      <NavLink
                        aria-label={collapsed ? label : undefined}
                        className={({ isActive }) => [
                          "group relative flex min-h-11 items-center gap-3 rounded-xl px-3 py-2 text-sm font-bold outline-hidden transition-colors focus-visible:ring-2 focus-visible:ring-cyan-700",
                          isActive ? "bg-white text-ocean shadow-xs ring-1 ring-cyan-900/10" : "text-slate-600 hover:bg-white hover:text-ocean",
                          collapsed ? "lg:justify-center" : "",
                        ].join(" ")}
                        end={item.to === "/"}
                        key={item.to}
                        onClick={() => onMobileOpenChange(false)}
                        title={collapsed ? label : undefined}
                        to={item.to}
                      >
                        {({ isActive }) => <>{isActive ? <span aria-hidden="true" className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-ocean" /> : null}<Icon aria-hidden="true" className="h-5 w-5 shrink-0" /><span className={collapsed ? "lg:sr-only" : ""}>{label}</span></>}
                      </NavLink>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </nav>

        <div className="border-t border-cyan-950/10 p-3">
          <div className={`${collapsed ? "lg:hidden" : ""} rounded-xl border border-emerald-900/10 bg-emerald-50/70 p-3`}>
            <div className="flex items-center gap-2 text-xs font-bold text-emerald-900"><ShieldCheck aria-hidden="true" className="h-4 w-4" />{t("shell.safetyTitle")}</div>
            <p className="mt-2 text-[0.6875rem] leading-5 text-slate-600">{t("shell.safetyText", { version: APP_VERSION })}</p>
          </div>
          <button aria-label={collapsed ? t("shell.expandSidebar") : t("shell.collapseSidebar")} className="mt-2 hidden min-h-10 w-full items-center justify-center gap-2 rounded-xl text-xs font-bold text-slate-500 transition hover:bg-white hover:text-ocean lg:flex" onClick={() => onCollapsedChange(!collapsed)} type="button">
            {collapsed ? <ChevronRight aria-hidden="true" className="h-4 w-4" /> : <ChevronLeft aria-hidden="true" className="h-4 w-4" />}<span className={collapsed ? "sr-only" : ""}>{collapsed ? t("common.expand") : t("common.collapse")}</span>
          </button>
        </div>
      </aside>
    </>
  );
}
