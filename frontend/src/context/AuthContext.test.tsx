import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { fetchMe, login as loginRequest, logoutSession } from "../services/api";
import type { User } from "../types/user";
import { AuthProvider, useAuth } from "./AuthContext";

vi.mock("../services/api", () => ({
  clearAuthToken: vi.fn(),
  fetchMe: vi.fn(),
  login: vi.fn(),
  logoutSession: vi.fn(),
}));

const doctor = {
  id: 2,
  name: "Médica Demo",
  email: "medica@prescripta.local",
  role: "medico",
  profession: "medicine",
  capabilities: ["dashboard.view", "patient.read", "prescription.check"],
  is_active: true,
} as User;

function Harness() {
  const auth = useAuth();
  return (
    <div>
      <span>{auth.isLoading ? "carregando" : auth.user?.name ?? "anônimo"}</span>
      <span>{auth.can("patient.read") ? "pode ler" : "não pode ler"}</span>
      <span>{auth.can("patient.read", "patient.write") ? "pode editar" : "não pode editar"}</span>
      <span>{auth.canAny("audit.read", "prescription.check") ? "tem fluxo" : "sem fluxo"}</span>
      <button onClick={() => void auth.login("medica@prescripta.local", "senha")} type="button">Entrar</button>
      <button onClick={auth.logout} type="button">Sair</button>
    </div>
  );
}

describe("sessão e capacidades", () => {
  it("restaura a sessão e avalia toda capacidade explicitamente", async () => {
    vi.mocked(fetchMe).mockResolvedValue(doctor);
    render(<AuthProvider><Harness /></AuthProvider>);
    expect(await screen.findByText("Médica Demo")).toBeVisible();
    expect(screen.getByText("pode ler")).toBeVisible();
    expect(screen.getByText("não pode editar")).toBeVisible();
    expect(screen.getByText("tem fluxo")).toBeVisible();
  });

  it("autentica e encerra a sessão expirada", async () => {
    vi.mocked(fetchMe).mockRejectedValue(new Error("sem sessão"));
    vi.mocked(loginRequest).mockResolvedValue({ user: doctor } as Awaited<ReturnType<typeof loginRequest>>);
    render(<AuthProvider><Harness /></AuthProvider>);
    expect(await screen.findByText("anônimo")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByText("Médica Demo")).toBeVisible();

    act(() => window.dispatchEvent(new Event("prescripta:auth-expired")));
    await waitFor(() => expect(screen.getByText("anônimo")).toBeVisible());
    expect(logoutSession).toHaveBeenCalled();
  });
});
