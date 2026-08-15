// DOM-only theme mechanism: data-theme="light"|"dark" on <html>.
// Not pure logic (reads/writes localStorage + matchMedia + the DOM), so it's
// exercised via the app + e2e/manual verification rather than unit tests.
const STORAGE_KEY = "dgp-theme";

type Theme = "light" | "dark";

function isTheme(value: string | null): value is Theme {
  return value === "light" || value === "dark";
}

function systemTheme(): Theme {
  return window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function apply(theme: Theme): void {
  document.documentElement.setAttribute("data-theme", theme);
}

export function initTheme(): void {
  const stored = localStorage.getItem(STORAGE_KEY);
  apply(isTheme(stored) ? stored : systemTheme());
}

export function toggleTheme(): void {
  const current = document.documentElement.getAttribute("data-theme");
  const next: Theme = current === "dark" ? "light" : "dark";
  apply(next);
  localStorage.setItem(STORAGE_KEY, next);
}
