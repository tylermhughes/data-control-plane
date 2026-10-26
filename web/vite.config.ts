/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Node's process.env, declared here rather than adding @types/node for one line.
declare const process: { env: Record<string, string | undefined> };

// In development (./scripts/web.sh run dev) the API is proxied to a running DCP.
const api = process.env.DCP_API_PROXY ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: { "/v1": api, "/healthz": api, "/readyz": api },
  },
  build: { outDir: "dist", sourcemap: true },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
    setupFiles: ["src/test/setup.ts"],
    restoreMocks: true,
  },
});
