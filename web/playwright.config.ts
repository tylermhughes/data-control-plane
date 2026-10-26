import { defineConfig } from "@playwright/test";

// Run by tests/e2e/test_ui.py, which starts DCP with seeded data and sets BASE_URL and
// DCP_API_KEY, inside the official Playwright Docker image.
declare const process: { env: Record<string, string | undefined> };

export default defineConfig({
  testDir: "e2e",
  timeout: 30_000,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:8000",
    trace: "retain-on-failure",
  },
});
