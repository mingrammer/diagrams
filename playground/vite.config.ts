import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Deployment note: base "./" means all asset URLs are resolved relative to
// the current document path, so this app must be served from a path with a
// trailing slash (e.g. /playground/, not /playground). GitHub Pages
// auto-redirects directory URLs to add the trailing slash, but other static
// hosts do not — without a redirect, /playground resolves assets relative to
// the parent path and catalog.json, wheels/, and icons/ 404 (often into the
// SPA's own index.html fallback instead of a clean 404). If deploying
// elsewhere, configure the host to redirect /playground -> /playground/.
export default defineConfig({
  plugins: [react()],
  base: "./",
  test: {
    globals: true,
    environment: "jsdom",
    // e2e/*.spec.ts uses @playwright/test, not vitest — keep vitest's
    // default *.spec.ts glob from picking it up.
    exclude: ["**/node_modules/**", "**/dist/**", "e2e/**"],
  },
});
