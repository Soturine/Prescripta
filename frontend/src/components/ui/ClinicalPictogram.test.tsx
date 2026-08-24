import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ClinicalPictogram from "./ClinicalPictogram";

describe("ClinicalPictogram", () => {
  it("is decorative and uses a local mask asset", () => {
    const { container } = render(<ClinicalPictogram kind="medicines" />);
    const icon = container.firstElementChild;
    expect(icon).toHaveAttribute("aria-hidden", "true");
    expect(icon?.getAttribute("src")).toMatch(/^data:image\/svg\+xml/);
  });
});
