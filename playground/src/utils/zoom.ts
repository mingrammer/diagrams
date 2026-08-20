// Pure helpers for the preview pane's infinite-canvas pan/zoom transform.
const MIN_ZOOM = 0.2;
const MAX_ZOOM = 4;

export function clampZoom(z: number): number {
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z));
}

export interface ViewTransform {
  tx: number;
  ty: number;
  scale: number;
}

// Zooms `view` by `factor`, keeping the world point currently under
// (cx, cy) — container-local coordinates — fixed on screen. Standard
// "zoom toward a point" formula for a translate-then-scale transform
// (`transform: translate(tx,ty) scale(s)` with `transform-origin: 0 0`):
// worldX = (cx - tx) / scale must be equal before and after, which solves to
// tx' = cx - (cx - tx) * (scale'/scale) (same for ty). `factor` is clamped
// via clampZoom first, so at the zoom bounds the ratio collapses to 1 and
// tx/ty are left untouched (no drift once zoom is maxed/minned out).
export function zoomAt(view: ViewTransform, cx: number, cy: number, factor: number): ViewTransform {
  const scale = clampZoom(view.scale * factor);
  const ratio = scale / view.scale;
  return {
    scale,
    tx: cx - (cx - view.tx) * ratio,
    ty: cy - (cy - view.ty) * ratio,
  };
}

const FIT_MIN_SCALE = 0.2;
const FIT_MAX_SCALE = 2; // capped below zoomAt's MAX_ZOOM so small diagrams don't blow up blurry
const FIT_DEFAULT_MARGIN = 48;

// Computes the view transform that fits `contentW x contentH` inside
// `canvasW x canvasH` with `margin` px of breathing room on every side,
// centered on both axes. Used for the preview pane's initial "fit to view"
// size and its "%" button (now a re-fit rather than a reset-to-100%).
export function fitView(
  canvasW: number,
  canvasH: number,
  contentW: number,
  contentH: number,
  margin: number = FIT_DEFAULT_MARGIN
): ViewTransform {
  const availW = canvasW - 2 * margin;
  const availH = canvasH - 2 * margin;
  const rawScale = Math.min(availW / contentW, availH / contentH);
  const scale = Math.min(FIT_MAX_SCALE, Math.max(FIT_MIN_SCALE, rawScale));
  return {
    scale,
    tx: (canvasW - contentW * scale) / 2,
    ty: (canvasH - contentH * scale) / 2,
  };
}
