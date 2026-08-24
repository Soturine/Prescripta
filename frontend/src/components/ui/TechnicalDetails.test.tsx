import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import TechnicalDetails from "./TechnicalDetails";

describe("TechnicalDetails", () => {
  it("keeps internals collapsed and copies the canonical value on demand", () => {
    const writeText = vi.fn();
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
    render(<TechnicalDetails copyValue="internal-42"><code>internal-42</code></TechnicalDetails>);
    const disclosure = screen.getByText("Detalhes técnicos").closest("details");
    expect(disclosure).not.toHaveAttribute("open");
    fireEvent.click(screen.getByRole("button", { name: "Copiar" }));
    expect(writeText).toHaveBeenCalledWith("internal-42");
  });
});
