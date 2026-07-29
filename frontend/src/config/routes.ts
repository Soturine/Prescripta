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

import type { LucideIcon } from "lucide-react";

import type { Capability } from "../types/user";

export const APP_ROUTES = [
  { to: "/", label: "Visão geral", shortLabel: "Início", icon: LayoutDashboard, section: "workspace", capability: "dashboard.view" },
  { to: "/patients", label: "Pacientes", icon: Users, section: "clinical", capability: "patient.read" },
  { to: "/medications", label: "Medicamentos", icon: Pill, section: "clinical", capability: "medication.read" },
  { to: "/prescription-check", label: "Checagem", icon: ClipboardCheck, section: "clinical", capability: "prescription.check" },
  { to: "/clinical-imports", label: "Reconciliação", icon: DatabaseZap, section: "clinical", capability: "reconciliation.review" },
  { to: "/protocols", label: "Protocolos", icon: Siren, section: "evidence", capability: "report.read" },
  { to: "/reports", label: "Relatórios", icon: FileText, section: "evidence", capability: "report.read" },
  { to: "/audit", label: "Auditoria", icon: FileClock, section: "governance", capability: "audit.read" },
  { to: "/settings/ai", label: "IA assistiva", icon: Settings, section: "governance", capability: "ai.status.view" },
  { to: "/users", label: "Acessos e perfis", icon: ShieldCheck, section: "governance", capability: "user.manage" },
] satisfies Array<{
  to: string;
  label: string;
  shortLabel?: string;
  icon: LucideIcon;
  section: "workspace" | "clinical" | "evidence" | "governance";
  capability: Capability;
}>;

export const NAV_SECTION_LABELS = {
  workspace: "Workspace",
  clinical: "Cuidado e segurança",
  evidence: "Evidência e orientação",
  governance: "Governança",
} as const;

export function findRoute(pathname: string) {
  return [...APP_ROUTES]
    .sort((left, right) => right.to.length - left.to.length)
    .find((route) => route.to === "/" ? pathname === "/" : pathname.startsWith(route.to));
}
