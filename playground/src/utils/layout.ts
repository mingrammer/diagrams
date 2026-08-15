// Pure helper for the editor/preview split-pane ratio (percent, 0-100).
// Keeps both panes usable — never let a drag collapse one side entirely.
const MIN_RATIO = 25;
const MAX_RATIO = 75;
export const DEFAULT_RATIO = 50;

export function clampRatio(r: number): number {
  if (Number.isNaN(r)) return DEFAULT_RATIO;
  return Math.min(MAX_RATIO, Math.max(MIN_RATIO, r));
}

// Node-list sidebar width (px). Same idea: resizable but never collapsed
// into uselessness on either extreme.
const MIN_SIDEBAR_WIDTH = 180;
const MAX_SIDEBAR_WIDTH = 420;
export const DEFAULT_SIDEBAR_WIDTH = 260;

export function clampSidebarWidth(w: number): number {
  if (Number.isNaN(w)) return DEFAULT_SIDEBAR_WIDTH;
  return Math.min(MAX_SIDEBAR_WIDTH, Math.max(MIN_SIDEBAR_WIDTH, w));
}
