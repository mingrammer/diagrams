import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  timeout: 180_000, // pyodide 초기 로드 포함
  // Conservative default: each spec cold-loads Pyodide (runtime + wheel
  // install) in its own context, so parallel workers mean simultaneous
  // large downloads/WASM boots competing for CPU and network — a known
  // flakiness source on constrained CI runners, though parallel runs do
  // pass locally. Serial trades wall-clock time for determinism.
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://localhost:4173",
    // Headless Chromium does not grant clipboard-write by default, so
    // navigator.clipboard.writeText() rejects with NotAllowedError unless
    // explicitly granted here (needed for the "share link" test's
    // writeText().then(...) success path).
    permissions: ["clipboard-read", "clipboard-write"],
  },
  webServer: {
    command: "npm run preview",
    port: 4173,
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
