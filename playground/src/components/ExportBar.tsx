import { useEffect, useState } from "react";
import { download, inlineIcons, svgToPngBlob } from "../export/exporter";
import type { FocusEvent, KeyboardEvent } from "react";

type DownloadFormat = "png" | "svg" | "jpeg";

const MIN_DIM = 16;
const MAX_DIM = 8192;
const COPIED_TIMEOUT_MS = 2000;

interface Props {
  svgs: { name: string; svg: string }[];
}

function slug(name: string): string {
  return name ? name.toLowerCase().replace(/\W+/g, "_") : "diagram";
}

// Parses a raw SIZE field's text into a positive pixel value. Empty (or
// not-yet-a-number, e.g. mid-typing) means "no override" — resolveSize's
// aspect-ratio-preserving default takes over for that axis. Clamping to
// [MIN_DIM, MAX_DIM] happens separately on blur (see `clampDimText`).
function parseDim(raw: string): number | undefined {
  if (raw.trim() === "") return undefined;
  const n = Number(raw);
  return Number.isFinite(n) && n > 0 ? n : undefined;
}

function clampDimText(raw: string): string {
  if (raw.trim() === "") return "";
  const n = Math.round(Number(raw));
  if (!Number.isFinite(n)) return "";
  return String(Math.min(MAX_DIM, Math.max(MIN_DIM, n)));
}

// Small download-arrow icon rendered to the right of each format button's
// label. Purely decorative — the button's accessible name still comes from
// its text content ("PNG"/"SVG"/"JPEG"), which e2e depends on — so this
// stays aria-hidden.
function DownloadIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path
        d="M7 1.6v7.1M7 8.7 3.9 5.6M7 8.7l3.1-3.1"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M2.6 11.4h8.8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

// Small copy icon rendered LEFT of "Copy" (mockup order) — decorative and
// aria-hidden for the same reason as `DownloadIcon`.
function CopyIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <rect x="4.6" y="4.6" width="7.2" height="7.2" rx="1.3" stroke="currentColor" strokeWidth="1.3" />
      <path d="M2.6 9V2.9a1 1 0 0 1 1-1H9" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

// Permanently-visible export bar docked under the editor (Mermaid-Live
// style). Two full-width rows:
//  - fields row: `SIZE [W] × [H] px  [Auto toggle]` stretched across the
//    full width (+ TARGET select when several diagrams exist). One Auto
//    switch governs BOTH dimensions: ON = inputs disabled/dimmed and the
//    exporter's aspect-preserving default (2x) applies; OFF = explicit
//    pixel inputs (either axis may be left empty for per-axis aspect
//    auto). Toggling Auto back on keeps the last typed values.
//  - actions row: PNG / SVG / JPEG download buttons (equal width) and a
//    compact "Copy Image" (clipboard PNG) button. Exports always use a
//    white background (the BACKGROUND option was dropped).
export default function ExportBar({ svgs }: Props) {
  const [auto, setAuto] = useState(true);
  const [width, setWidth] = useState("");
  const [height, setHeight] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Keep the selection valid as the diagram list changes (e.g. a script edit
  // that drops from two `with Diagram(...)` blocks down to one).
  useEffect(() => {
    if (selectedIndex >= svgs.length && svgs.length > 0) setSelectedIndex(0);
  }, [svgs.length, selectedIndex]);

  const active = svgs[selectedIndex] ?? null;
  const effectiveWidth = auto ? undefined : parseDim(width);
  const effectiveHeight = auto ? undefined : parseDim(height);

  function handleDimBlur(setter: (v: string) => void) {
    return (e: FocusEvent<HTMLInputElement>) => setter(clampDimText(e.currentTarget.value));
  }

  function handleDimKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    // Commit + clamp on Enter rather than waiting for blur, so a keyboard
    // user can confirm the value without tabbing away.
    if (e.key === "Enter") e.currentTarget.blur();
  }

  async function handleDownload(format: DownloadFormat) {
    if (!active) return;
    setError(null);
    setCopied(false);
    try {
      const fileSlug = slug(active.name);
      if (format === "svg") {
        // SVG is vector — SIZE is meaningless for it.
        const inlined = await inlineIcons(active.svg);
        download(`${fileSlug}.svg`, new Blob([inlined], { type: "image/svg+xml" }));
      } else {
        const mime = format === "jpeg" ? "image/jpeg" : "image/png";
        const blob = await svgToPngBlob(active.svg, {
          width: effectiveWidth,
          height: effectiveHeight,
          mime,
        });
        download(`${fileSlug}.${format === "jpeg" ? "jpg" : "png"}`, blob);
      }
    } catch (err) {
      setError(`Export failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  async function handleCopyImage() {
    if (!active) return;
    setError(null);
    try {
      const blob = await svgToPngBlob(active.svg, {
        width: effectiveWidth,
        height: effectiveHeight,
        mime: "image/png",
      });
      await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
      setCopied(true);
      setTimeout(() => setCopied(false), COPIED_TIMEOUT_MS);
    } catch (err) {
      setCopied(false);
      setError(`Copy failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  const message = error
    ? { text: error, tone: "error" as const }
    : copied
      ? { text: "Copied!", tone: "success" as const }
      : null;

  return (
    <div className="export-bar">
      <div className="export-bar-row export-bar-row-fields">
        <div className="export-field">
          <span className="export-field-label">Size</span>
          <input
            type="text"
            inputMode="numeric"
            className="export-size-input"
            aria-label="Export width in pixels"
            placeholder="auto"
            disabled={auto}
            value={width}
            onChange={(e) => setWidth(e.target.value.replace(/\D/g, ""))}
            onBlur={handleDimBlur(setWidth)}
            onKeyDown={handleDimKeyDown}
          />
          <span className="export-size-x" aria-hidden="true">×</span>
          <input
            type="text"
            inputMode="numeric"
            className="export-size-input"
            aria-label="Export height in pixels"
            placeholder="auto"
            disabled={auto}
            value={height}
            onChange={(e) => setHeight(e.target.value.replace(/\D/g, ""))}
            onBlur={handleDimBlur(setHeight)}
            onKeyDown={handleDimKeyDown}
          />
          <span className="export-size-px" aria-hidden="true">px</span>
          <button
            type="button"
            role="switch"
            aria-checked={auto}
            className="export-auto-toggle"
            onClick={() => setAuto((a) => !a)}
          >
            <span className="toggle-track" aria-hidden="true">
              <span className="toggle-knob" />
            </span>
            Auto
          </button>
          {svgs.length > 1 && (
            <select
              className="export-bar-select"
              aria-label="Diagram to export"
              value={selectedIndex}
              onChange={(e) => setSelectedIndex(Number(e.target.value))}
            >
              {svgs.map((s, i) => (
                <option key={`${s.name}-${i}`} value={i}>
                  {s.name || "diagram"}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      <div className="export-bar-row export-bar-row-actions">
        <button
          type="button"
          className="export-download-btn"
          disabled={!active}
          onClick={() => void handleDownload("png")}
        >
          PNG
          <DownloadIcon />
        </button>
        <button
          type="button"
          className="export-download-btn"
          disabled={!active}
          onClick={() => void handleDownload("svg")}
        >
          SVG
          <DownloadIcon />
        </button>
        <button
          type="button"
          className="export-download-btn"
          disabled={!active}
          onClick={() => void handleDownload("jpeg")}
        >
          JPEG
          <DownloadIcon />
        </button>
        <button type="button" className="export-copy-btn" disabled={!active} onClick={() => void handleCopyImage()}>
          <CopyIcon />
          Copy Image
        </button>
        {message && <span className={`export-bar-message export-bar-message-${message.tone}`}>{message.text}</span>}
      </div>
    </div>
  );
}
