import { render, screen, within } from "@testing-library/react";
import { Activity } from "lucide-react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { selectLocale } from "../i18n";
import Help from "../pages/Help";
import ClinicalCheckStepper from "./clinical/ClinicalCheckStepper";
import ClinicalMetricCard from "./clinical/ClinicalMetricCard";
import AttritionFlow from "./research/AttritionFlow";

describe("healthtech domain components", () => {
  it("shows progression before and after a clinical result", () => {
    const { rerender } = render(<ClinicalCheckStepper hasResult={false} />);
    expect(screen.getByRole("listitem", { current: "step" })).toHaveTextContent("Revisão");
    rerender(<ClinicalCheckStepper hasResult />);
    expect(screen.getByRole("listitem", { current: "step" })).toHaveTextContent("Resultado");
  });

  it("presents linked metrics and accessible attrition without inventing data", () => {
    render(
      <MemoryRouter>
        <ClinicalMetricCard detail="Escopo autorizado" icon={Activity} label="Sinais" to="/audit" value={3} />
        <AttritionFlow steps={[
          { sequence: 1, label: "Adultos", before_count: 3, excluded_count: 1, after_count: 2 },
          { sequence: 2, label: "Sem baseline", before_count: 0, excluded_count: 0, after_count: 0 },
        ]} />
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: /Sinais/ })).toHaveAttribute("href", "/audit");
    expect(screen.getByLabelText(/Adultos: 3 participantes antes e 2 depois/)).toBeVisible();
    expect(screen.getByText("3 → 2")).toBeVisible();
  });

  it("renders integrated help in English while preserving canonical terminology", async () => {
    await selectLocale("en-US");
    render(<MemoryRouter><Help /></MemoryRouter>);
    expect(screen.getByRole("heading", { name: "Help and getting started" })).toBeVisible();
    expect(screen.getByText(/deterministic rules/)).toBeVisible();
    const researchCard = screen.getByRole("heading", { name: "Research and RWE" }).closest("div");
    expect(researchCard).not.toBeNull();
    expect(within(researchCard!).getByRole("link", { name: "About this page" })).toHaveAttribute("href", "/research");
  });
});
