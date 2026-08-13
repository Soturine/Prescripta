import { defineConfig, devices } from "@playwright/test";

const python = JSON.stringify(process.env.PRESCRIPTA_PYTHON ?? "python");

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  expect: {
    timeout: 10_000,
    toHaveScreenshot: { animations: "disabled", maxDiffPixelRatio: 0.01 },
  },
  fullyParallel: false,
  workers: 1,
  reporter: [["line"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  outputDir: "test-results",
  use: {
    baseURL: "http://127.0.0.1:5177",
    colorScheme: "light",
    locale: "pt-BR",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1000 } } },
    { name: "mobile-chromium", grep: /@responsive/, use: { ...devices["Pixel 7"], colorScheme: "light" } },
    { name: "tablet-chromium", grep: /@responsive/, use: { ...devices["iPad (gen 7)"], browserName: "chromium", colorScheme: "light" } },
    { name: "reduced-motion", grep: /@reduced/, use: { ...devices["Desktop Chrome"], reducedMotion: "reduce", viewport: { width: 1280, height: 900 } } },
  ],
  webServer: [
    {
      command: `${python} -c "from pathlib import Path; Path('playwright-v088.db').unlink(missing_ok=True)" && ${python} -m uvicorn app.main:app --host 127.0.0.1 --port 8013`,
      cwd: "../backend",
      url: "http://127.0.0.1:8013/api/health",
      env: {
        PRESCRIPTA_DATABASE_URL: "sqlite:///./playwright-v088.db",
        PRESCRIPTA_CORS_ORIGINS: "http://127.0.0.1:5177",
        PRESCRIPTA_AI_ENABLE_EXTERNAL_CALLS: "false",
      },
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5177",
      url: "http://127.0.0.1:5177",
      env: { VITE_API_URL: "http://127.0.0.1:8013/api" },
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
