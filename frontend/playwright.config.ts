import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  fullyParallel: false,
  workers: 1,
  reporter: "line",
  use: { baseURL: "http://127.0.0.1:5177", trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "python -c \"from pathlib import Path; Path('playwright-v860.db').unlink(missing_ok=True)\" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8013",
      cwd: "../backend",
      url: "http://127.0.0.1:8013/api/health",
      env: {
        PRESCRIPTA_DATABASE_URL: "sqlite:///./playwright-v860.db",
        PRESCRIPTA_CORS_ORIGINS: "http://127.0.0.1:5177",
        PRESCRIPTA_AI_ENABLE_EXTERNAL_CALLS: "false",
      },
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5177",
      url: "http://127.0.0.1:5177",
      env: { VITE_API_URL: "http://127.0.0.1:8013/api" },
      reuseExistingServer: false,
    },
  ],
});
