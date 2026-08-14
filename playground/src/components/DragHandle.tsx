import { useRef, useState, type PointerEvent, type RefObject } from "react";

interface Props {
  containerRef: RefObject<HTMLElement>;
  onChange: (value: number) => void;
  ariaLabel: string;
  /** Derives the next value from the pointer's clientX and containerRef's
   *  current bounding rect — ratio math for the editor/preview split, px
   *  math for the sidebar. Callers own their own clamping. */
  valueFromPointer: (clientX: number, rect: DOMRect) => number;
  /** Value reported on double-click, and the fallback reported mid-drag if
   *  containerRef briefly has no rect (e.g. mid-unmount). */
  resetValue: number;
}

// Shared flush 1px vertical divider / drag handle: used both between
// .editor-column and .preview-pane (ratio math, 25-75 clamp) and on the
// node-list sidebar's right edge (px math, clampSidebarWidth). Drags
// compute the next value via the caller-supplied valueFromPointer and
// report it through onChange; double-click resets to resetValue.
export default function DragHandle({ containerRef, onChange, ariaLabel, valueFromPointer, resetValue }: Props) {
  const [active, setActive] = useState(false);
  const draggingRef = useRef(false);

  function handlePointerDown(e: PointerEvent<HTMLDivElement>) {
    draggingRef.current = true;
    setActive(true);
    e.currentTarget.setPointerCapture(e.pointerId);
  }

  function handlePointerMove(e: PointerEvent<HTMLDivElement>) {
    if (!draggingRef.current) return;
    const rect = containerRef.current?.getBoundingClientRect();
    onChange(rect ? valueFromPointer(e.clientX, rect) : resetValue);
  }

  function endDrag(e: PointerEvent<HTMLDivElement>) {
    if (!draggingRef.current) return;
    draggingRef.current = false;
    setActive(false);
    if (e.currentTarget.hasPointerCapture(e.pointerId)) {
      e.currentTarget.releasePointerCapture(e.pointerId);
    }
  }

  return (
    <div
      className={`split-handle${active ? " is-active" : ""}`}
      role="separator"
      aria-orientation="vertical"
      aria-label={ariaLabel}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      onDoubleClick={() => onChange(resetValue)}
    />
  );
}
