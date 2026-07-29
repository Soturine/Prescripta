import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { User } from "../types/user";
import Layout from "./Layout";
import ProtectedRoute from "./ProtectedRoute";
import Sidebar from "./Sidebar";

const authMock = vi.hoisted(() => vi.fn());
vi.mock("../context/AuthContext", () => ({ useAuth: authMock }));

const user = {
  id: 4, name: "Profissional Demo", email: "profissional@prescripta.local", role: "farmaceutico",
  profession: "pharmacy", capabilities: ["dashboard.view", "medication.read", "report.read"],
  capability_policy_version: "2026.1", is_active: true, created_at: "2026-07-29T12:00:00Z",
  specialty_code: "clinical_pharmacy", specialty_codes: ["clinical_pharmacy"], credential_type: "CRF-DEMO",
  credential_code_demo: "DEMO-123", credential_region: "SP", credential_expires_at: null,
  institutional_policy: {}, sensitive_data_segments: [], crm_demo: null, crm_uf: null, rqe_demo: null,
  credential_verification_status: "demo_only", institution_id: "demo", mfa_enabled: false,
} satisfies User;

function renderGuard(auth: Record<string, unknown>, props: React.ComponentProps<typeof ProtectedRoute> = {}) {
  authMock.mockReturnValue(auth);
  return render(
    <MemoryRouter initialEntries={["/restricted"]}>
      <Routes>
        <Route path="/login" element={<p>Login destino</p>} />
        <Route path="/access-denied" element={<p>Acesso negado destino</p>} />
        <Route element={<ProtectedRoute {...props} />}><Route path="/restricted" element={<p>Conteúdo autorizado</p>} /></Route>
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  window.localStorage.clear();
  authMock.mockReturnValue({
    user, logout: vi.fn(), isAuthenticated: true, isLoading: false,
    can: (...capabilities: string[]) => capabilities.every((capability) => user.capabilities.includes(capability as never)),
    canAny: (...capabilities: string[]) => capabilities.some((capability) => user.capabilities.includes(capability as never)),
    canAccess: (roles: string[]) => roles.includes(user.role),
  });
});

describe("shell e autorização de rotas", () => {
  it("distingue sessão carregando, anônima, papel negado e capacidades any/all", () => {
    const base = { can: () => false, canAny: () => false, canAccess: () => false };
    const { unmount } = renderGuard({ ...base, isLoading: true, isAuthenticated: false });
    expect(screen.getByText("Validando sessão")).toBeVisible();
    unmount();

    const anonymous = renderGuard({ ...base, isLoading: false, isAuthenticated: false });
    expect(screen.getByText("Login destino")).toBeVisible();
    anonymous.unmount();

    const wrongRole = renderGuard({ ...base, isLoading: false, isAuthenticated: true }, { roles: ["medico"] });
    expect(screen.getByText("Acesso negado destino")).toBeVisible();
    wrongRole.unmount();

    const anyAllowed = renderGuard({ ...base, isLoading: false, isAuthenticated: true, canAny: () => true }, { capabilities: ["patient.read", "report.read"], requireAnyCapability: true });
    expect(screen.getByText("Conteúdo autorizado")).toBeVisible();
    anyAllowed.unmount();

    renderGuard({ ...base, isLoading: false, isAuthenticated: true }, { capabilities: ["patient.read", "report.read"] });
    expect(screen.getByText("Acesso negado destino")).toBeVisible();
  });

  it("renderiza navegação somente por capacidade e fecha drawer por teclado", () => {
    const close = vi.fn();
    render(<MemoryRouter><Sidebar collapsed={false} mobileOpen onCollapsedChange={vi.fn()} onMobileOpenChange={close} /></MemoryRouter>);
    expect(screen.getByRole("link", { name: "Visão geral" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Medicamentos" })).toBeVisible();
    expect(screen.queryByRole("link", { name: "Pacientes" })).not.toBeInTheDocument();
    expect(document.body.style.overflow).toBe("hidden");
    fireEvent.keyDown(window, { key: "Escape" });
    expect(close).toHaveBeenCalledWith(false);
    fireEvent.click(screen.getAllByRole("button", { name: "Fechar navegação" })[0]);
    expect(close).toHaveBeenCalledTimes(2);
  });

  it("persiste preferência, informa offline e encerra sessão pelo menu", async () => {
    const logout = vi.fn();
    authMock.mockReturnValue({ ...authMock(), logout });
    render(
      <MemoryRouter initialEntries={["/medications"]}>
        <Routes><Route element={<Layout />}><Route path="medications" element={<h1 id="page-title">Catálogo demo</h1>} /></Route></Routes>
      </MemoryRouter>,
    );
    expect(screen.getByRole("navigation", { name: "Breadcrumb" })).toHaveTextContent("Medicamentos");
    fireEvent.click(screen.getByRole("button", { name: "Recolher barra lateral" }));
    await waitFor(() => expect(window.localStorage.getItem("prescripta:sidebar-collapsed")).toBe("true"));
    fireEvent(window, new Event("offline"));
    expect(await screen.findByRole("status")).toHaveTextContent("Sem conexão");
    fireEvent.click(screen.getByRole("button", { name: "Encerrar sessão" }));
    expect(logout).toHaveBeenCalledOnce();
  });
});
