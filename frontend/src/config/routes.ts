import {
  BookOpenCheck,
  CircleHelp,
  ClipboardCheck,
  DatabaseZap,
  FileClock,
  FileText,
  FlaskConical,
  LayoutDashboard,
  MessagesSquare,
  Pill,
  Settings,
  ShieldCheck,
  Siren,
  Users,
} from "lucide-react";

import type { LucideIcon } from "lucide-react";

import type { Capability } from "../types/user";

export const APP_ROUTES = [
  { to: "/", labelKey: "nav.overview", shortLabelKey: "nav.overviewShort", icon: LayoutDashboard, section: "workspace", capability: "dashboard.view" },
  { to: "/patients", labelKey: "nav.patients", icon: Users, section: "clinical", capability: "patient.read" },
  { to: "/medications", labelKey: "nav.medications", icon: Pill, section: "clinical", capability: "medication.read" },
  { to: "/prescription-check", labelKey: "nav.prescriptionCheck", icon: ClipboardCheck, section: "clinical", capability: "prescription.check" },
  { to: "/pharmacy", labelKey: "nav.pharmacy", icon: MessagesSquare, section: "clinical", capability: "pharmacy.intervention.read" },
  { to: "/clinical-imports", labelKey: "nav.reconciliation", icon: DatabaseZap, section: "clinical", capability: "reconciliation.review" },
  { to: "/protocols", labelKey: "nav.protocols", icon: Siren, section: "evidence", capability: "report.read" },
  { to: "/reports", labelKey: "nav.reports", icon: FileText, section: "evidence", capability: "report.read" },
  { to: "/evidence", labelKey: "nav.evidence", icon: BookOpenCheck, section: "evidence", capability: "evidence.read" },
  { to: "/research", labelKey: "nav.research", icon: FlaskConical, section: "research", capability: "research.study.read" },
  { to: "/audit", labelKey: "nav.audit", icon: FileClock, section: "governance", capability: "audit.read" },
  { to: "/settings/ai", labelKey: "nav.ai", icon: Settings, section: "governance", capability: "ai.status.view" },
  { to: "/users", labelKey: "nav.users", icon: ShieldCheck, section: "governance", capability: "user.manage" },
  { to: "/help", labelKey: "nav.help", icon: CircleHelp, section: "help", capability: null },
] satisfies Array<{
  to: string;
  labelKey: string;
  shortLabelKey?: string;
  icon: LucideIcon;
  section: "workspace" | "clinical" | "evidence" | "research" | "governance" | "help";
  capability: Capability | null;
}>;

export const NAV_SECTION_KEYS = {
  workspace: "nav.sections.workspace",
  clinical: "nav.sections.clinical",
  evidence: "nav.sections.evidence",
  research: "nav.sections.research",
  governance: "nav.sections.governance",
  help: "nav.sections.help",
} as const;

export function findRoute(pathname: string) {
  return [...APP_ROUTES]
    .sort((left, right) => right.to.length - left.to.length)
    .find((route) => route.to === "/" ? pathname === "/" : pathname.startsWith(route.to));
}
