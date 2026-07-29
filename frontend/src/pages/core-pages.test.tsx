import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { DashboardSummary } from "../types/audit";
import type { Patient } from "../types/patient";
import type { User } from "../types/user";
import AccessDenied from "./AccessDenied";
import Dashboard from "./Dashboard";
import Login from "./Login";
import Patients from "./Patients";
import Users from "./Users";

const apiMocks = vi.hoisted(() => ({
  createPatient: vi.fn(),
  createUser: vi.fn(),
  fetchApiHealth: vi.fn(),
  fetchDashboard: vi.fn(),
  fetchPatients: vi.fn(),
  fetchUsers: vi.fn(),
  updateUserClinicalProfile: vi.fn(),
  updateUserRole: vi.fn(),
  updateUserStatus: vi.fn(),
}));
const authMock = vi.hoisted(() => vi.fn());

vi.mock("../services/api", () => apiMocks);
vi.mock("../context/AuthContext", () => ({ useAuth: authMock }));

const allCapabilities = new Set([
  "dashboard.view", "patient.create", "patient.read", "patient.write", "prescription.check",
  "medication.read", "medication.manage", "audit.read", "safety.review", "report.read",
  "system.health.view", "user.manage", "ai.status.view",
]);

const user = {
  id: 1,
  name: "Administradora Demo",
  email: "admin@prescripta.local",
  role: "admin",
  profession: "administration",
  capabilities: [...allCapabilities],
  capability_policy_version: "v1",
  is_active: true,
  created_at: "2026-07-29T12:00:00Z",
  specialty_code: null,
  specialty_codes: [],
  credential_type: null,
  credential_code_demo: null,
  credential_region: null,
  credential_expires_at: null,
  institutional_policy: {},
  sensitive_data_segments: [],
  crm_demo: null,
  crm_uf: null,
  rqe_demo: null,
  credential_verification_status: "demo_unverified",
  institution_id: "demo",
  mfa_enabled: false,
} as User;

const dashboard: DashboardSummary = {
  patient_count: 9,
  medication_count: 5,
  prescription_checks: 12,
  alerts_by_severity: { baixo: 2, moderado: 3, alto: 1, critico: 1 },
  catalog_quality: {
    active_ingredients_total: 8,
    active_ingredients_curated: 4,
    active_ingredients_pending: 4,
    medications_demo: 5,
    medications_without_source: 2,
    medications_without_dose_rule: 1,
    medications_without_policy: 1,
    counseling_summaries: 3,
  },
};

function patientFixture(id = 1): Patient {
  return {
    id,
    name: `Paciente Fictícia ${id}`,
    birth_date: "1980-01-01",
    age: 46,
    weight_kg: 70,
    height_cm: 165,
    sex_for_dosing_calculation: "female",
    phone: null,
    email: null,
    mother_name: null,
    allergies: id % 2 ? ["dipirona"] : [],
    comorbidities: ["hipertensão"],
    current_medications: ["medicamento demo"],
    renal_condition: null,
    hepatic_condition: null,
    cardiac_condition: null,
    gastrointestinal_history: null,
    hypertension: true,
    diabetes: false,
    pregnancy_or_lactation: false,
    mental_health_factors: [],
    reproductive_gynecologic_factors: [],
    adverse_reactions: [],
    clinical_notes: null,
    clinical_profile_reviewed_at: null,
    clinical_profile_completeness_score: id === 2 ? 45 : 85,
    clinical_profile_badge: id === 2 ? "Incompleto" : "Adequado",
    identifiers: [],
    possible_duplicate_matches: [],
  };
}

function renderPage(node: React.ReactNode, initialEntry = "/") {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}><MemoryRouter initialEntries={[initialEntry]}>{node}</MemoryRouter></QueryClientProvider>);
}

beforeEach(() => {
  authMock.mockReturnValue({
    user,
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    can: (...capabilities: string[]) => capabilities.every((item) => allCapabilities.has(item)),
    canAny: (...capabilities: string[]) => capabilities.some((item) => allCapabilities.has(item)),
  });
  apiMocks.fetchDashboard.mockResolvedValue(dashboard);
  apiMocks.fetchApiHealth.mockResolvedValue({ version: "0.8.7", database: "ok", ai_provider: "fallback" });
  apiMocks.fetchPatients.mockResolvedValue([]);
  apiMocks.fetchUsers.mockResolvedValue([user]);
  apiMocks.createPatient.mockResolvedValue(patientFixture());
  apiMocks.createUser.mockResolvedValue(user);
  apiMocks.updateUserClinicalProfile.mockResolvedValue(user);
  apiMocks.updateUserRole.mockResolvedValue(user);
  apiMocks.updateUserStatus.mockResolvedValue(user);
});

afterEach(() => vi.unstubAllGlobals());

describe("dashboard e estados de acesso", () => {
  it("renderiza somente métricas e ações derivadas de capacidade", async () => {
    renderPage(<Dashboard />);
    expect(await screen.findByRole("heading", { name: "Olá, Administradora" })).toBeVisible();
    expect(screen.getByText("Pacientes atribuídos")).toBeVisible();
    expect(screen.getByText("Saúde do sistema")).toBeVisible();
    expect(screen.getByText("Regra de dose pendente")).toBeVisible();
    expect(screen.getAllByText("Crítico").length).toBeGreaterThan(0);
  });

  it("não consulta health sem capacidade e oferece retry no erro", async () => {
    apiMocks.fetchDashboard.mockRejectedValue(new Error("offline"));
    authMock.mockReturnValue({ user, isAuthenticated: true, isLoading: false, can: () => false, canAny: () => false });
    renderPage(<Dashboard />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Não foi possível carregar");
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(apiMocks.fetchApiHealth).not.toHaveBeenCalled();
  });

  it("explica a negação profissional sem prometer acesso por tenant", () => {
    renderPage(<AccessDenied />);
    expect(screen.getByRole("heading", { name: "Acesso negado" })).toBeVisible();
    expect(screen.getByText(/vínculo e finalidade/)).toBeVisible();
  });
});

describe("lista autorizada de pacientes", () => {
  it("diferencia vazio de falha e permite retry", async () => {
    const { unmount } = renderPage(<Patients />);
    expect(await screen.findByRole("heading", { name: "Nenhum paciente autorizado" })).toBeVisible();
    unmount();
    apiMocks.fetchPatients.mockRejectedValue(new Error("erro"));
    renderPage(<Patients />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Falha ao carregar pacientes");
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(apiMocks.fetchPatients).toHaveBeenCalled();
  });

  it("busca, filtra, pagina e abre o workspace", async () => {
    apiMocks.fetchPatients.mockResolvedValue(Array.from({ length: 9 }, (_, index) => patientFixture(index + 1)));
    renderPage(<Patients />);
    expect((await screen.findAllByText("Paciente Fictícia 1")).length).toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText("Buscar no escopo autorizado"), { target: { value: "Fictícia 2" } });
    expect(await screen.findByText("1 paciente")).toBeVisible();
    fireEvent.change(screen.getByLabelText("Filtro clínico"), { target: { value: "incomplete" } });
    expect(screen.getAllByText("Paciente Fictícia 2").length).toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText("Buscar no escopo autorizado"), { target: { value: "" } });
    fireEvent.change(screen.getByLabelText("Filtro clínico"), { target: { value: "all" } });
    fireEvent.click(screen.getByRole("button", { name: "Próxima página" }));
    expect(await screen.findByText("Página 2 de 2")).toBeVisible();
  });

  it("abre cadastro somente com capacidade explícita", async () => {
    renderPage(<Patients />);
    fireEvent.click(await screen.findByRole("button", { name: "Novo paciente" }));
    expect(screen.getByRole("dialog", { name: "Novo paciente" })).toBeVisible();
    expect(screen.getByLabelText("Nome")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Fechar" }));
  });
});

describe("perfis profissionais", () => {
  it("altera status e substitui template de papel com confirmação", async () => {
    vi.stubGlobal("confirm", vi.fn(() => true));
    renderPage(<Users />);
    expect(await screen.findByText("Administradora Demo")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Inativar" }));
    await waitFor(() => expect(apiMocks.updateUserStatus).toHaveBeenCalledWith(1, false));
    fireEvent.change(screen.getAllByLabelText("Papel global")[0], { target: { value: "farmaceutico" } });
    await waitFor(() => expect(apiMocks.updateUserRole).toHaveBeenCalledWith(1, "farmaceutico"));
  });

  it("edita o subconjunto de capacidades", async () => {
    renderPage(<Users />);
    fireEvent.click(await screen.findByRole("button", { name: "Capacidades" }));
    const dialog = screen.getByRole("dialog", { name: /Capacidades de Administradora/ });
    expect(dialog).toBeVisible();
    fireEvent.click(within(dialog).getByRole("checkbox", { name: /Ver dashboard/ }));
    fireEvent.click(within(dialog).getByRole("button", { name: "Salvar menor privilégio" }));
    await waitFor(() => expect(apiMocks.updateUserClinicalProfile).toHaveBeenCalled());
    expect(apiMocks.updateUserClinicalProfile.mock.calls.at(-1)?.[1].capabilities).not.toContain("dashboard.view");
  });

  it("cria perfil a partir de template e preserva dados digitados ao trocar papel", async () => {
    renderPage(<Users />);
    fireEvent.click(await screen.findByRole("button", { name: "Novo usuário" }));
    const dialog = screen.getByRole("dialog", { name: "Novo usuário" });
    fireEvent.change(within(dialog).getByLabelText("Nome"), { target: { value: "Psicóloga Demo" } });
    fireEvent.change(within(dialog).getByLabelText("E-mail"), { target: { value: "psicologa@prescripta.local" } });
    fireEvent.change(within(dialog).getByLabelText("Senha inicial"), { target: { value: "Senha@123" } });
    fireEvent.change(within(dialog).getByLabelText("Papel global"), { target: { value: "psicologo" } });
    fireEvent.submit(within(dialog).getByRole("button", { name: "Criar usuário" }).closest("form")!);
    await waitFor(() => expect(apiMocks.createUser).toHaveBeenCalled());
    expect(apiMocks.createUser.mock.calls[0][0]).toMatchObject({ name: "Psicóloga Demo", role: "psicologo", profession: "psychology" });
  });
});

describe("login e expiração", () => {
  it("preenche credencial demo e informa falha sem navegar", async () => {
    const login = vi.fn().mockRejectedValue(new Error("inválido"));
    authMock.mockReturnValue({ isAuthenticated: false, login });
    renderPage(<Routes><Route path="/login" element={<Login />} /></Routes>, "/login");
    fireEvent.click(screen.getByRole("button", { name: /Médico ·/ }));
    expect(screen.getByLabelText("E-mail")).toHaveValue("medico@prescripta.local");
    fireEvent.click(screen.getByRole("button", { name: /^Entrar$/ }));
    expect(await screen.findByText(/E-mail ou senha inválidos/)).toBeVisible();
  });

  it("retorna à rota originalmente solicitada após autenticar", async () => {
    const login = vi.fn().mockResolvedValue(undefined);
    authMock.mockReturnValue({ isAuthenticated: false, login });
    renderPage(<Routes><Route path="/login" element={<Login />} /><Route path="/patients" element={<p>Destino autorizado</p>} /></Routes>, { pathname: "/login", state: { from: { pathname: "/patients" } } } as never);
    fireEvent.click(screen.getByRole("button", { name: /^Entrar$/ }));
    expect(await screen.findByText("Destino autorizado")).toBeVisible();
  });
});
