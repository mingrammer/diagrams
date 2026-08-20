import type { KeyboardEvent, ReactNode } from "react";
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { svgStats } from "../utils/svgStats";
import { fitView, zoomAt, type ViewTransform } from "../utils/zoom";

interface Props {
  svgs: { name: string; svg: string }[];
  loading: boolean;
  renderMs: number | null;
  onRenameDiagram?: (index: number, name: string) => void;
  /** Rendered docked at the bottom of the pane, below the canvas
   *  (the ExportBar lives here per the design mockup). */
  children?: ReactNode;
}

// True infinite canvas: the container is a fixed, overflow:hidden viewport;
// all pan/zoom state lives in `view` (tx/ty/scale) and is applied as a
// single CSS transform on the absolutely-positioned content layer. Unlike
// the old scrollLeft/scrollTop-based pan, tx/ty are unbounded — content can
// be dragged past the left/top edge (negative translate) with no clamping.
export default function PreviewPane({ svgs, loading, renderMs, onRenameDiagram, children }: Props) {
  const [view, setView] = useState<ViewTransform>({ tx: 0, ty: 0, scale: 1 });
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef(view);
  viewRef.current = view;

  // Click-to-edit for the fixed header's diagram name (always index 0 — the
  // per-sheet `.sheet-label`s below stay read-only). `titleDraft` is local
  // input state so typing doesn't touch `svgs`/App state until commit.
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState("");
  const titleInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isEditingTitle) return;
    const input = titleInputRef.current;
    input?.focus();
    input?.select();
  }, [isEditingTitle]);

  function startEditingTitle() {
    if (!onRenameDiagram) return;
    setTitleDraft(svgs[0]?.name ?? "");
    setIsEditingTitle(true);
  }

  function commitTitleEdit() {
    setIsEditingTitle(false);
    const nextName = titleDraft;
    const previousName = svgs[0]?.name ?? "";
    if (nextName !== previousName) onRenameDiagram?.(0, nextName);
  }

  function handleTitleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      commitTitleEdit();
    } else if (e.key === "Escape") {
      e.preventDefault();
      setIsEditingTitle(false);
    }
  }

  // Fits the content layer entirely inside the canvas viewport (scaled down
  // for large diagrams, scaled up — capped at 2x — for tiny ones) and
  // centers it on both axes. offsetWidth/Height read the content's
  // untransformed layout size (CSS transforms don't affect layout), so this
  // is correct regardless of the view's current scale. Used both for the
  // initial/on-new-svgs sizing and for the "%" fit button.
  const fitToView = useCallback(() => {
    const container = containerRef.current;
    const content = contentRef.current;
    if (!container || !content) return;
    const rect = container.getBoundingClientRect();
    setView(fitView(rect.width, rect.height, content.offsetWidth, content.offsetHeight));
  }, []);

  useLayoutEffect(() => {
    fitToView();
  }, [svgs, fitToView]);

  // ctrl+wheel (trackpad pinch) zooms at the cursor; a plain wheel pans
  // (natural two-finger trackpad scroll). Must be a real (non-passive) DOM
  // listener — not React's onWheel — so preventDefault() actually stops the
  // browser's own page-zoom/scroll for the gesture.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    function handleWheel(e: WheelEvent) {
      e.preventDefault();
      const rect = container!.getBoundingClientRect();
      if (e.ctrlKey) {
        const factor = Math.exp(-e.deltaY * 0.01);
        setView((v) => zoomAt(v, e.clientX - rect.left, e.clientY - rect.top, factor));
      } else {
        setView((v) => ({ ...v, tx: v.tx - e.deltaX, ty: v.ty - e.deltaY }));
      }
    }
    container.addEventListener("wheel", handleWheel, { passive: false });
    return () => container.removeEventListener("wheel", handleWheel);
  }, []);

  // Two-pointer touch pinch: track active pointers' positions, and on each
  // move with exactly two active pointers, derive a scale factor from the
  // change in distance between them and zoom at their midpoint.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const pointers = new Map<number, { x: number; y: number }>();
    let lastDistance: number | null = null;

    function distance(): number {
      const [a, b] = [...pointers.values()];
      return Math.hypot(a.x - b.x, a.y - b.y);
    }
    function midpoint(): { x: number; y: number } {
      const [a, b] = [...pointers.values()];
      return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
    }

    function handlePointerDown(e: PointerEvent) {
      if (e.pointerType !== "touch") return;
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      lastDistance = pointers.size === 2 ? distance() : null;
    }
    function handlePointerMove(e: PointerEvent) {
      if (!pointers.has(e.pointerId)) return;
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pointers.size !== 2) return;
      const dist = distance();
      if (lastDistance === null || lastDistance === 0) {
        lastDistance = dist;
        return;
      }
      const factor = dist / lastDistance;
      const { x, y } = midpoint();
      const rect = container!.getBoundingClientRect();
      setView((v) => zoomAt(v, x - rect.left, y - rect.top, factor));
      lastDistance = dist;
    }
    function handlePointerEnd(e: PointerEvent) {
      pointers.delete(e.pointerId);
      lastDistance = pointers.size === 2 ? distance() : null;
    }

    container.addEventListener("pointerdown", handlePointerDown);
    container.addEventListener("pointermove", handlePointerMove);
    container.addEventListener("pointerup", handlePointerEnd);
    container.addEventListener("pointercancel", handlePointerEnd);
    container.addEventListener("pointerleave", handlePointerEnd);
    return () => {
      container.removeEventListener("pointerdown", handlePointerDown);
      container.removeEventListener("pointermove", handlePointerMove);
      container.removeEventListener("pointerup", handlePointerEnd);
      container.removeEventListener("pointercancel", handlePointerEnd);
      container.removeEventListener("pointerleave", handlePointerEnd);
    };
  }, []);

  // One-pointer drag-to-pan: tx/ty move freely with the pointer — no bounds,
  // so dragging toward the left/top can carry content into negative
  // translate space (this is exactly what fixes "can't pan left/up past the
  // edge" from the old scrollLeft/scrollTop approach). A 3px move threshold
  // keeps incidental clicks (zoom buttons, etc.) from starting a drag; those
  // targets are also excluded outright. If a second pointer comes down
  // mid-drag, pan disengages immediately and hands off to the pinch effect.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let draggingId: number | null = null;
    let engaged = false;
    let originX = 0;
    let originY = 0;
    let originTx = 0;
    let originTy = 0;

    function disengage() {
      if (draggingId !== null && container!.hasPointerCapture(draggingId)) {
        container!.releasePointerCapture(draggingId);
      }
      container!.classList.remove("is-panning");
      draggingId = null;
      engaged = false;
    }

    function handlePointerDown(e: PointerEvent) {
      if (draggingId !== null) {
        disengage();
        return;
      }
      if (e.button !== 0) return;
      if ((e.target as Element).closest("button, a, input, select, [role=menu]")) return;
      draggingId = e.pointerId;
      engaged = false;
      originX = e.clientX;
      originY = e.clientY;
      originTx = viewRef.current.tx;
      originTy = viewRef.current.ty;
      container!.setPointerCapture(draggingId);
    }

    function handlePointerMove(e: PointerEvent) {
      if (draggingId === null || e.pointerId !== draggingId) return;
      const dx = e.clientX - originX;
      const dy = e.clientY - originY;
      if (!engaged) {
        if (Math.hypot(dx, dy) < 3) return;
        engaged = true;
        container!.classList.add("is-panning");
      }
      setView((v) => ({ ...v, tx: originTx + dx, ty: originTy + dy }));
    }

    function handlePointerEnd(e: PointerEvent) {
      if (draggingId !== e.pointerId) return;
      disengage();
    }

    container.addEventListener("pointerdown", handlePointerDown);
    container.addEventListener("pointermove", handlePointerMove);
    container.addEventListener("pointerup", handlePointerEnd);
    container.addEventListener("pointercancel", handlePointerEnd);
    return () => {
      container.removeEventListener("pointerdown", handlePointerDown);
      container.removeEventListener("pointermove", handlePointerMove);
      container.removeEventListener("pointerup", handlePointerEnd);
      container.removeEventListener("pointercancel", handlePointerEnd);
    };
  }, []);

  // Zoom segment (−/+) buttons zoom around the container's center.
  function zoomByFactor(factor: number) {
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    setView((v) => zoomAt(v, rect.width / 2, rect.height / 2, factor));
  }

  const pct = Math.round(view.scale * 100);
  const first = svgs[0];
  const firstStats = first ? svgStats(first.svg) : null;
  const showSheetLabels = svgs.length > 1;

  return (
    <div className="preview-pane">
      <div className="preview-header">
        <div className="diagram-header-left">
          {isEditingTitle ? (
            <input
              ref={titleInputRef}
              className="diagram-name-input"
              data-testid="diagram-title"
              value={titleDraft}
              onChange={(e) => setTitleDraft(e.target.value)}
              onBlur={commitTitleEdit}
              onKeyDown={handleTitleKeyDown}
            />
          ) : (
            <span
              className={onRenameDiagram ? "diagram-name diagram-name--editable" : "diagram-name"}
              data-testid="diagram-title"
              tabIndex={onRenameDiagram ? 0 : undefined}
              role={onRenameDiagram ? "button" : undefined}
              aria-label={onRenameDiagram ? "Rename diagram" : undefined}
              onClick={onRenameDiagram ? startEditingTitle : undefined}
              onKeyDown={
                onRenameDiagram
                  ? (e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        startEditingTitle();
                      }
                    }
                  : undefined
              }
              title={onRenameDiagram ? "Click to rename" : undefined}
            >
              {first?.name || "diagram"}
              {onRenameDiagram && (
                <span className="diagram-name-edit-icon" aria-hidden="true">
                  ✎
                </span>
              )}
            </span>
          )}
          {firstStats && (
            <span className="diagram-meta">
              · {firstStats.nodes} nodes · {firstStats.edges} edges
            </span>
          )}
        </div>
        <div className="diagram-header-right">
          <div className="zoom-segment">
            <button onClick={() => zoomByFactor(1 / 1.2)} aria-label="Zoom out">
              −
            </button>
            <button className="zoom-pct" onClick={fitToView} aria-label="Fit">
              {pct}%
            </button>
            <button onClick={() => zoomByFactor(1.2)} aria-label="Zoom in">
              +
            </button>
          </div>
        </div>
      </div>
      {/* testid lives on the canvas (not the pane root) so e2e's
          `preview svg` matches only rendered diagram SVGs — the ExportBar
          docked below carries its own decorative icon <svg>s. */}
      <div
        className="preview-canvas"
        data-testid="preview"
        ref={containerRef}
        style={{ backgroundPosition: `${view.tx}px ${view.ty}px` }}
      >
        <div
          className="preview-content"
          ref={contentRef}
          style={{ transform: `translate(${view.tx}px, ${view.ty}px) scale(${view.scale})` }}
        >
          {svgs.map(({ name, svg }, i) => (
            <section key={`${name}-${i}`} className="diagram-block">
              {showSheetLabels && <div className="sheet-label">{name || "diagram"}</div>}
              <div className="diagram-card">
                <div className="preview-svg" dangerouslySetInnerHTML={{ __html: svg }} />
              </div>
            </section>
          ))}
        </div>
        {loading && <span className="preview-overlay-chip">Rendering…</span>}
        {renderMs != null && <span className="render-ms-chip">rendered in {renderMs}ms</span>}
      </div>
      {children}
    </div>
  );
}
