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

  it("fetchMe lento do carregamento não derruba um login feito depois (R1)", async () => {
    let rejectInitial: (reason: unknown) => void = () => undefined;
    vi.mocked(fetchMe).mockReturnValue(
      new Promise<User>((_, reject) => {
        rejectInitial = reject;
      }),
    );
    vi.mocked(logoutSession).mockClear().mockResolvedValue(undefined as never);
    vi.mocked(loginRequest).mockResolvedValue({ user: doctor } as Awaited<ReturnType<typeof loginRequest>>);
    render(<AuthProvider><Harness /></AuthProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByText("Médica Demo")).toBeVisible();

    await act(async () => rejectInitial(new Error("401 antigo")));
    expect(screen.getByText("Médica Demo")).toBeVisible();
    expect(logoutSession).not.toHaveBeenCalled();
  });

  it("login espera o logout em voo terminar (R2)", async () => {
    vi.mocked(fetchMe).mockResolvedValue(doctor);
    const order: string[] = [];
    let finishLogout: () => void = () => undefined;
    vi.mocked(logoutSession).mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          finishLogout = () => {
            order.push("logout-done");
            resolve();
          };
        }) as never,
    );
    vi.mocked(loginRequest).mockImplementation(async () => {
      order.push("login-sent");
      return { user: doctor } as Awaited<ReturnType<typeof loginRequest>>;
    });
    render(<AuthProvider><Harness /></AuthProvider>);
    expect(await screen.findByText("Médica Demo")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Sair" }));
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));
    await act(async () => finishLogout());
    expect(await screen.findByText("Médica Demo")).toBeVisible();
    expect(order).toEqual(["logout-done", "login-sent"]);
  });

  it("logout em outra aba limpa esta aba sem chamar o servidor de novo", async () => {
    vi.mocked(fetchMe).mockResolvedValue(doctor);
    vi.mocked(logoutSession).mockClear();
    render(<AuthProvider><Harness /></AuthProvider>);
    expect(await screen.findByText("Médica Demo")).toBeVisible();
    const otherTab = new BroadcastChannel("prescripta-auth");
    otherTab.postMessage("logout");
    await waitFor(() => expect(screen.getByText("anônimo")).toBeVisible());
    expect(logoutSession).not.toHaveBeenCalled();
    otherTab.close();
  });
});
