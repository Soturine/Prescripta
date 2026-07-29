import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import Badge from "./Badge";
import Modal from "./Modal";
import StatusPanel from "./StatusPanel";
import Tabs from "./Tabs";
import Tooltip from "./Tooltip";

describe("design system acessível", () => {
  it("combina texto e ícone no badge", () => {
    render(<Badge icon={<span aria-hidden="true">!</span>} tone="warning">Pendente</Badge>);
    expect(screen.getByText("Pendente")).toBeVisible();
  });

  it("mantém bloqueio crítico persistente como alerta", () => {
    render(<StatusPanel title="Prescrição bloqueada" tone="critical">Revisão obrigatória</StatusPanel>);
    expect(screen.getByRole("alert")).toHaveTextContent("Prescrição bloqueada");
    expect(screen.getByText("Revisão obrigatória")).toBeVisible();
  });

  it("navega pelas tabs com teclado", () => {
    function Example() {
      const [value, setValue] = useState("summary");
      return <Tabs label="Resultado" onChange={setValue} options={[{ id: "summary", label: "Resumo" }, { id: "sources", label: "Fontes", badge: 2 }]} value={value} />;
    }
    render(<Example />);
    fireEvent.keyDown(screen.getByRole("tab", { name: "Resumo" }), { key: "ArrowRight" });
    expect(screen.getByRole("tab", { name: /Fontes/ })).toHaveAttribute("aria-selected", "true");
  });

  it("abre e fecha dialog sem perder rótulo", () => {
    const onClose = vi.fn();
    render(<Modal description="Confirmação auditável" onClose={onClose} open title="Revisar override"><button type="button">Confirmar</button></Modal>);
    expect(screen.getByRole("dialog", { name: "Revisar override" })).toHaveAttribute("open");
    fireEvent.click(screen.getByRole("button", { name: "Fechar" }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("oferece descrição sem depender de hover", () => {
    render(<Tooltip label="Explicação"><button type="button">Fonte</button></Tooltip>);
    expect(screen.getByText("Explicação")).toBeInTheDocument();
  });
});
