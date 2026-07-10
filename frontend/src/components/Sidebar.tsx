import {
  ClipboardCheck,
  DatabaseZap,
  FileClock,
  FileText,
  LayoutDashboard,
  Pill,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import type { UserRole } from "../types/user";

const links = [
  {
    to: "/",
    label: "Dashboard",
    icon: LayoutDashboard,
    roles: ["admin", "medico", "enfermagem", "auditor"],
  },
  { to: "/patients", label: "Pacientes", icon: Users, roles: ["admin", "medico", "enfermagem"] },
  {
    to: "/medications",
    label: "Medicamentos",
    icon: Pill,
    roles: ["admin", "medico", "enfermagem"],
  },
  {
    to: "/prescription-check",
    label: "Checagem",
    icon: ClipboardCheck,
    roles: ["admin", "medico", "enfermagem"],
  },
  {
    to: "/clinical-imports",
    label: "Importações",
    icon: DatabaseZap,
    roles: ["admin", "medico", "enfermagem", "auditor"],
  },
  {
    to: "/settings/ai",
    label: "IA",
    icon: Settings,
    roles: ["admin", "medico", "enfermagem", "auditor"],
  },
  {
    to: "/reports",
    label: "Relatórios",
    icon: FileText,
    roles: ["admin", "medico", "enfermagem", "auditor"],
  },
  { to: "/audit", label: "Auditoria", icon: FileClock, roles: ["admin", "auditor"] },
  { to: "/users", label: "Usuários", icon: ShieldCheck, roles: ["admin"] },
] satisfies Array<{
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  roles: UserRole[];
}>;

export default function Sidebar() {
  const { canAccess } = useAuth();
  const visibleLinks = links.filter((item) => canAccess(item.roles));

  return (
    <aside className="border-b border-slate-200 bg-white/95 lg:min-h-screen lg:w-72 lg:border-b-0 lg:border-r">
      <div className="flex h-full flex-col gap-6 px-4 py-4 lg:px-6 lg:py-7">
        <div>
          <div className="text-2xl font-bold tracking-normal text-ink">Prescripta</div>
          <div className="mt-1 text-xs font-medium text-slate-500">Uso educacional</div>
        </div>

        <nav className="flex gap-2 overflow-x-auto lg:flex-col lg:overflow-visible">
          {visibleLinks.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  [
                    "inline-flex min-h-11 shrink-0 items-center gap-3 rounded-lg px-3 py-2 text-sm font-semibold transition",
                    isActive
                      ? "bg-ocean text-white shadow-soft"
                      : "text-slate-600 hover:bg-slate-100 hover:text-ink",
                  ].join(" ")
                }
              >
                <Icon aria-hidden="true" className="h-5 w-5" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
