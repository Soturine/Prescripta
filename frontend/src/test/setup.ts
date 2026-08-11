import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

import i18n from "../i18n";

const unexpectedConsole: string[] = [];
const allowedConsolePatterns: RegExp[] = [];

export function allowConsoleMessage(pattern: RegExp) {
  allowedConsolePatterns.push(pattern);
}

beforeEach(async () => {
  unexpectedConsole.length = 0;
  allowedConsolePatterns.length = 0;
  for (const level of ["warn", "error"] as const) {
    vi.spyOn(console, level).mockImplementation((...args: unknown[]) => {
      const message = args.map(String).join(" ");
      if (!allowedConsolePatterns.some((pattern) => pattern.test(message))) {
        unexpectedConsole.push(`${level}: ${message}`);
      }
    });
  }
  window.localStorage.removeItem("prescripta:locale");
  await i18n.changeLanguage("pt-BR");
  document.documentElement.lang = "pt-BR";
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  if (unexpectedConsole.length) {
    throw new Error(`Unexpected browser console output:\n${unexpectedConsole.join("\n")}`);
  }
});

window.requestAnimationFrame = (callback: FrameRequestCallback) => {
  callback(0);
  return 0;
};

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: query.includes("reduce"),
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

HTMLDialogElement.prototype.showModal = function showModal() {
  this.setAttribute("open", "");
};

HTMLDialogElement.prototype.close = function close() {
  this.removeAttribute("open");
  this.dispatchEvent(new Event("close"));
};
