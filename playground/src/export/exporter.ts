const ICON_HREF = /(xlink:href|href)="(icons\/[^"]+)"/g;

async function toDataUri(url: string, fetcher: typeof fetch): Promise<string> {
  const res = await fetcher(url);
  if (!res.ok) throw new Error(`Failed to fetch icon ${url}: HTTP ${res.status}`);
  const mime = url.endsWith(".svg") ? "image/svg+xml" : "image/png";
  const bytes = new Uint8Array(await res.arrayBuffer());
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return `data:${mime};base64,${btoa(binary)}`;
}

export async function inlineIcons(svg: string, fetcher: typeof fetch = fetch): Promise<string> {
  const urls = new Set<string>();
  for (const match of svg.matchAll(ICON_HREF)) urls.add(match[2]);
  if (!urls.size) return svg;
  const dataUris = new Map<string, string>();
  await Promise.all(
    [...urls].map(async (url) => dataUris.set(url, await toDataUri(url, fetcher)))
  );
  return svg.replace(ICON_HREF, (_full, attr, url) => `${attr}="${dataUris.get(url)}"`);
}

export interface OutputSize {
  w: number;
  h: number;
}

const MIN_OUTPUT_SIZE = 16;
const MAX_OUTPUT_SIZE = 8192;

function clampAxis(n: number): number {
  return Math.min(MAX_OUTPUT_SIZE, Math.max(MIN_OUTPUT_SIZE, Math.round(n)));
}

// Resolves the raster output size for an export from the optional
// user-provided WIDTH/HEIGHT fields (both in px):
//  - neither set (or not a positive finite number) -> defaults to 2x the
//    diagram's natural size, matching the export bar's previous default
//    output.
//  - only one axis set -> the other axis is derived from the diagram's
//    natural aspect ratio, so the diagram is never stretched by accident.
//  - both axes set -> used exactly as given; the user explicitly asked for
//    both dimensions, so aspect distortion is allowed.
// A degenerate natural size (<=0 on either axis, e.g. before an <img> has
// finished loading) can't produce a meaningful aspect ratio, so it's guarded
// by always falling back to the default-2x branch, which is itself then
// clamped, so the result is still a valid, positive canvas size.
// Every result is rounded and clamped per-axis to [MIN_OUTPUT_SIZE,
// MAX_OUTPUT_SIZE] so callers can hand it straight to a <canvas>.
export function resolveSize(naturalW: number, naturalH: number, width?: number, height?: number): OutputSize {
  const validWidth = width !== undefined && Number.isFinite(width) && width > 0;
  const validHeight = height !== undefined && Number.isFinite(height) && height > 0;
  const naturalOk = naturalW > 0 && naturalH > 0;

  let w: number;
  let h: number;
  if (naturalOk && validWidth && validHeight) {
    w = width as number;
    h = height as number;
  } else if (naturalOk && validWidth) {
    w = width as number;
    h = ((width as number) * naturalH) / naturalW;
  } else if (naturalOk && validHeight) {
    h = height as number;
    w = ((height as number) * naturalW) / naturalH;
  } else {
    w = naturalW * 2;
    h = naturalH * 2;
  }
  return { w: clampAxis(w), h: clampAxis(h) };
}

export interface PngExportOptions {
  width?: number;
  height?: number;
  mime?: "image/png" | "image/jpeg";
}

export async function svgToPngBlob(svg: string, options?: PngExportOptions): Promise<Blob> {
  const { mime = "image/png", width, height } = options ?? {};
  const inlined = await inlineIcons(svg);
  const svgBlob = new Blob([inlined], { type: "image/svg+xml" });
  const url = URL.createObjectURL(svgBlob);
  try {
    const img = new Image();
    await new Promise<void>((resolve, reject) => {
      img.onload = () => resolve();
      img.onerror = () => reject(new Error("Failed to load SVG for export"));
      img.src = url;
    });
    const { w, h } = resolveSize(img.naturalWidth, img.naturalHeight, width, height);
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = "white";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.scale(w / img.naturalWidth, h / img.naturalHeight);
    ctx.drawImage(img, 0, 0);
    return await new Promise<Blob>((resolve, reject) =>
      canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("toBlob failed"))), mime)
    );
  } finally {
    URL.revokeObjectURL(url);
  }
}

export function download(filename: string, blob: Blob): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
