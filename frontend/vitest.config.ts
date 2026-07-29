import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    exclude: ["e2e/**", "node_modules/**", "dist/**"],
    clearMocks: true,
    restoreMocks: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary", "lcov"],
      reportsDirectory: "./coverage",
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.test.{ts,tsx}",
        "src/config/**",
        "src/design-system/**",
        "src/main.tsx",
        "src/types/**",
        "src/vite-env.d.ts",
      ],
      thresholds: {
        lines: 75,
        statements: 75,
        functions: 70,
        branches: 65,
      },
    },
  },
});
