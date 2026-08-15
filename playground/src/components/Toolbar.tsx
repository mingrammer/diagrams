import { useEffect, useState } from "react";
import { formatStars } from "../utils/format";
import { toggleTheme } from "../utils/theme";

interface Props {
  status: string;
  onShare: () => void;
  shared: boolean;
}

function statusVariant(status: string): "ready" | "busy" | "error" {
  if (status === "Ready") return "ready";
  if (status.startsWith("Failed")) return "error";
  return "busy";
}

const STARS_CACHE_KEY = "dgp-gh-stars";
const STARS_TTL_MS = 60 * 60 * 1000; // 1h
const STARS_API_URL = "https://api.github.com/repos/mingrammer/diagrams";
// The badge must always render — when the API is unreachable (e.g. rate
// limited) and no cache exists yet, fall back to this approximate count;
// it self-corrects on the next successful fetch.
const FALLBACK_STARS = 42_500;

interface StarsCache {
  count: number;
  ts: number;
}

function readCachedStars(ignoreTtl = false): number | null {
  try {
    const raw = localStorage.getItem(STARS_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StarsCache;
    if (typeof parsed.count !== "number" || typeof parsed.ts !== "number") return null;
    if (!ignoreTtl && Date.now() - parsed.ts > STARS_TTL_MS) return null;
    return parsed.count;
  } catch {
    return null;
  }
}

// GitHub's official octocat mark, inlined so it renders crisp at 16px with
// no extra request and follows `currentColor` in both themes.
function GitHubMark() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z" />
    </svg>
  );
}

// Small filled star, used ahead of the formatted count.
function StarMark() {
  return (
    <svg width="10" height="10" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M8 .5l2.2 4.7 5.1.6-3.8 3.6.9 5.1L8 12l-4.4 2.5.9-5.1L.7 5.8l5.1-.6L8 .5Z" />
    </svg>
  );
}

export default function Toolbar({ status, onShare, shared }: Props) {
  const isLoading = status === "Rendering…";
  const variant = statusVariant(status);
  // Stale-while-error: fresh cache → stale cache (expired TTL) → baked-in
  // fallback, so the count is always visible; a successful fetch replaces it.
  const [stars, setStars] = useState<number>(
    () => readCachedStars() ?? readCachedStars(true) ?? FALLBACK_STARS
  );

  useEffect(() => {
    if (readCachedStars() !== null) return; // fresh cache already applied above
    let cancelled = false;
    fetch(STARS_API_URL)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: { stargazers_count?: unknown }) => {
        if (cancelled) return;
        const count = data.stargazers_count;
        if (typeof count !== "number") return;
        setStars(count);
        localStorage.setItem(STARS_CACHE_KEY, JSON.stringify({ count, ts: Date.now() } satisfies StarsCache));
      })
      .catch(() => {
        // Fetch failed (network, rate limit, bad shape): keep whatever count
        // is already displayed — a fresh/stale cached value or the baked-in
        // fallback — rather than surfacing an error.
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <header className={`toolbar${isLoading ? " is-loading" : ""}`}>
      {/* The real diagrams project logo (copied from assets/img/diagrams.png)
          on a white chip so its dark strokes stay legible in dark theme. */}
      <span className="app-mark" aria-hidden="true">
        <img src="diagrams-logo.png" alt="" width={22} height={22} />
      </span>
      <strong className="toolbar-title">Diagrams Playground</strong>
      <div className={`status-pill status-pill--${variant}`}>
        <span className="status-dot" aria-hidden="true" />
        <span data-testid="status">{status}</span>
      </div>
      <span className="toolbar-spacer" />
      <div className="toolbar-actions">
        <button onClick={toggleTheme} aria-label="Toggle theme" className="btn-ghost" data-testid="theme-toggle">
          ◐ Theme
        </button>
        <a
          href="https://github.com/mingrammer/diagrams"
          target="_blank"
          rel="noreferrer"
          className="btn-ghost"
          aria-label={`GitHub repository, ${stars} stars`}
        >
          <GitHubMark />
          GitHub
          <span className="gh-stars">
            <StarMark />
            {formatStars(stars)}
          </span>
        </a>
        <a
          href="https://diagrams.mingrammer.com"
          target="_blank"
          rel="noreferrer"
          className="btn-ghost"
          aria-label="Documentation"
        >
          Docs ↗
        </a>
        <button onClick={onShare} className="btn-share" data-testid="share-button">
          {shared ? "Link copied!" : "Share"}
        </button>
      </div>
    </header>
  );
}
