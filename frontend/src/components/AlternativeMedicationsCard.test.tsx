import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import i18n from "../i18n";
import type { AlternativeMedication } from "../types/prescription";
import AlternativeMedicationsCard from "./AlternativeMedicationsCard";
import { formatStatus } from "../utils/formatters";

const base: AlternativeMedication = {
  medication_id: 2,
  name: "Alternativa Demo",
  active_ingredient: "substância B",
  therapeutic_class: "classe",
  similarity_reason: "texto legado",
  similarity_kind: "alternative_group",
  status: "atencao",
  review_status: "candidate_for_human_review",
  dose_assessment: "not_evaluated_for_alternative",
  risk_level: "baixo",
  top_alerts: [],
  observation: "",
};

describe("alternativas para revisão humana", () => {
  it("nunca exibe liberado, mesmo com payload legado", () => {
    render(<AlternativeMedicationsCard alternatives={[{ ...base, status: "liberado" }]} />);
    const row = screen.getByRole("row", { name: /Alternativa Demo/ });
    expect(within(row).queryByText(formatStatus("liberado"))).toBeNull();
    expect(within(row).getByText(formatStatus("atencao"))).toBeInTheDocument();
    expect(within(row).getByText("Candidato para revisão")).toBeInTheDocument();
    expect(within(row).getByText("Não avaliada")).toBeInTheDocument();
    expect(screen.getByText(/não são recomendação nem substituição automática/i)).toBeInTheDocument();
  });

  it("preserva bloqueio e localiza em EN-US sem enum cru", async () => {
    await i18n.changeLanguage("en-US");
    render(<AlternativeMedicationsCard alternatives={[{ ...base, status: "bloqueado" }]} />);
    const row = screen.getByRole("row", { name: /Alternativa Demo/ });
    expect(within(row).getByText(formatStatus("bloqueado"))).toBeInTheDocument();
    expect(within(row).getByText("Same alternative group (demo)")).toBeInTheDocument();
    expect(within(row).getByText("Not evaluated")).toBeInTheDocument();
    expect(screen.queryByText(/alternative_group|not_evaluated_for_alternative/)).toBeNull();
    await i18n.changeLanguage("pt-BR");
  });
});
