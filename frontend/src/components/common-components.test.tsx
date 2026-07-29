import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import EmptyState from "./EmptyState";
import LoadingState from "./LoadingState";
import PageHeader from "./PageHeader";
import RiskBadge from "./RiskBadge";
import SourceBadge from "./SourceBadge";

describe("estados comuns", () => {
  it("expõe loading e vazio semanticamente", () => {
    const { rerender } = render(<LoadingState label="Carregando pacientes" />);
    expect(screen.getByText("Carregando pacientes")).toBeVisible();
    rerender(<EmptyState description="Solicite um vínculo." title="Nenhum paciente autorizado" />);
    expect(screen.getByRole("heading", { name: "Nenhum paciente autorizado" })).toBeVisible();
  });

  it("mantém heading focável e ação contextual", () => {
    render(<MemoryRouter><PageHeader actions={<a href="/patients">Voltar</a>} description="Descrição" title="Workspace" /></MemoryRouter>);
    expect(screen.getByRole("heading", { name: "Workspace" })).toHaveAttribute("tabindex", "-1");
    expect(screen.getByRole("link", { name: "Voltar" })).toBeVisible();
  });

  it("não usa apenas cor para risco e fonte", () => {
    render(<><RiskBadge level="critico" /><SourceBadge jurisdiction="BR" source="Anvisa" status="pending_review" /></>);
    expect(screen.getByText("Crítico")).toBeVisible();
    expect(screen.getByText(/Anvisa · BR · pendente/)).toBeVisible();
  });
});
