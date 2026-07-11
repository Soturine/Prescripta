import {
  ClipboardCheck,
  DatabaseZap,
  FileClock,
  FileText,
  LayoutDashboard,
  Pill,
  Settings,
  ShieldCheck,
  Siren,
  Users,
} from "lucide-react";

import type { UserRole } from "../types/user";

export const APP_ROUTES = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, roles: ["admin", "medico", "enfermagem", "auditor"] },
  { to: "/patients", label: "Pacientes", icon: Users, roles: ["admin", "medico", "enfermagem"] },
  { to: "/medications", label: "Medicamentos", icon: Pill, roles: ["admin", "medico", "enfermagem"] },
  { to: "/prescription-check", label: "Checagem", icon: ClipboardCheck, roles: ["admin", "medico", "enfermagem"] },
  { to: "/clinical-imports", label: "Importações", icon: DatabaseZap, roles: ["admin", "medico", "enfermagem", "auditor"] },
  { to: "/settings/ai", label: "IA assistiva", icon: Settings, roles: ["admin", "medico", "enfermagem", "auditor"] },
  { to: "/protocols", label: "Protocolos", icon: Siren, roles: ["admin", "medico", "enfermagem", "auditor"] },
  { to: "/reports", label: "Relatórios", icon: FileText, roles: ["admin", "medico", "enfermagem", "auditor"] },
  { to: "/audit", label: "Auditoria", icon: FileClock, roles: ["admin", "auditor"] },
  { to: "/users", label: "Usuários", icon: ShieldCheck, roles: ["admin"] },
] satisfies Array<{
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  roles: UserRole[];
}>;
