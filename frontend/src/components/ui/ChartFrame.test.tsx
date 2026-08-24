import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ChartFrame from "./ChartFrame";

describe("ChartFrame", () => {
  it("associates its explanation and exposes an equivalent table", () => {
    render(<ChartFrame description="Same values below" fallback={<table><tbody><tr><td>42</td></tr></tbody></table>} title="Distribution"><div>visual</div></ChartFrame>);
    const figure = screen.getByRole("figure", { name: "Distribution" });
    expect(figure).toHaveAccessibleDescription("Same values below");
    expect(screen.getByRole("table")).toHaveTextContent("42");
  });
});
