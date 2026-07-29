import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Medication } from "../types/medication";
import type { Patient } from "../types/patient";
import PrescriptionForm from "./PrescriptionForm";

const patient = {
  id: 7,
  name: "Paciente Fictícia",
  clinical_profile_completeness_score: 90,
} as Patient;

const medication = {
  id: 11,
  brand_name: "Medicamento Demo",
  active_ingredient: "substância teste",
} as Medication;

describe("dose estruturada", () => {
  it("produz contrato dimensional explícito", async () => {
    const onSubmit = vi.fn();
    render(<PrescriptionForm medications={[medication]} onSubmit={onSubmit} patients={[patient]} />);

    fireEvent.click(screen.getByRole("button", { name: "Executar checagem" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledOnce());
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      patient_id: 7,
      medication_id: 11,
      dose: {
        amount: 100,
        amount_unit: "mg",
        administration_kind: "intermittent",
        frequency_per_day: 1,
        rounding_policy: "prescripta-half-even-v1",
      },
    });
  });

  it("exige taxa em infusão contínua", async () => {
    render(<PrescriptionForm medications={[medication]} onSubmit={vi.fn()} patients={[patient]} />);
    fireEvent.change(screen.getByLabelText("Modalidade"), { target: { value: "continuous" } });
    await screen.findByRole("spinbutton", { name: /Taxa de infusão/ });
    fireEvent.click(screen.getByRole("button", { name: "Executar checagem" }));
    expect(await screen.findByText("Infusão contínua exige taxa explícita.")).toBeVisible();
    expect(screen.getByRole("spinbutton", { name: /Taxa de infusão/ })).toHaveFocus();
  });

  it("exige teto para PRN e o envia separado de frequência", async () => {
    const onSubmit = vi.fn();
    render(<PrescriptionForm medications={[medication]} onSubmit={onSubmit} patients={[patient]} />);
    fireEvent.change(screen.getByLabelText("Modalidade"), { target: { value: "prn" } });
    await screen.findByRole("spinbutton", { name: /Teto de administrações/ });
    fireEvent.click(screen.getByRole("button", { name: "Executar checagem" }));
    expect(await screen.findByText("PRN exige teto de administrações.")).toBeVisible();

    fireEvent.change(screen.getByRole("spinbutton", { name: /Teto de administrações/ }), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "Executar checagem" }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledOnce());
    expect(onSubmit.mock.calls[0][0].dose).toMatchObject({ prn: true, max_administrations_per_day: 3, frequency_per_day: null });
  });

  it("não aceita volume sem concentração", async () => {
    render(<PrescriptionForm medications={[medication]} onSubmit={vi.fn()} patients={[patient]} />);
    fireEvent.change(screen.getByLabelText("Unidade"), { target: { value: "mL" } });
    fireEvent.click(screen.getByRole("button", { name: "Executar checagem" }));
    expect(await screen.findByText("Quantidade em volume exige concentração para calcular massa.")).toBeVisible();
  });
});
