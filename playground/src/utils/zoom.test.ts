import { describe, expect, it } from "vitest";
import { clampZoom, fitView, zoomAt, type ViewTransform } from "./zoom";

describe("clampZoom", () => {
  it("passes through values within the 0.2-4 range", () => {
    expect(clampZoom(1)).toBe(1);
    expect(clampZoom(0.5)).toBe(0.5);
    expect(clampZoom(3)).toBe(3);
  });

  it("clamps values below 0.2 up to 0.2", () => {
    expect(clampZoom(0.01)).toBe(0.2);
    expect(clampZoom(-5)).toBe(0.2);
  });

  it("clamps values above 4 down to 4", () => {
    expect(clampZoom(10)).toBe(4);
  });

  it("clamps exactly at the boundaries", () => {
    expect(clampZoom(0.2)).toBe(0.2);
    expect(clampZoom(4)).toBe(4);
  });
});

describe("zoomAt", () => {
  it("(a) keeps the world point under the cursor fixed across a zoom-in", () => {
    const view: ViewTransform = { tx: 10, ty: 20, scale: 1 };
    const cx = 100;
    const cy = 50;
    const worldBefore = { x: (cx - view.tx) / view.scale, y: (cy - view.ty) / view.scale };

    const next = zoomAt(view, cx, cy, 2);
    const worldAfter = { x: (cx - next.tx) / next.scale, y: (cy - next.ty) / next.scale };

    expect(worldAfter.x).toBeCloseTo(worldBefore.x, 10);
    expect(worldAfter.y).toBeCloseTo(worldBefore.y, 10);
  });

  it("(a) keeps the world point under the cursor fixed across a zoom-out", () => {
    const view: ViewTransform = { tx: -35, ty: 60, scale: 2 };
    const cx = 320;
    const cy = 140;
    const worldBefore = { x: (cx - view.tx) / view.scale, y: (cy - view.ty) / view.scale };

    const next = zoomAt(view, cx, cy, 0.5);
    const worldAfter = { x: (cx - next.tx) / next.scale, y: (cy - next.ty) / next.scale };

    expect(worldAfter.x).toBeCloseTo(worldBefore.x, 10);
    expect(worldAfter.y).toBeCloseTo(worldBefore.y, 10);
  });

  it("(b) clamps at the MAX bound and stops tx/ty from drifting further", () => {
    const view: ViewTransform = { tx: 0, ty: 0, scale: 4 };
    const next = zoomAt(view, 100, 100, 2);
    expect(next.scale).toBe(4);
    expect(next.tx).toBe(view.tx);
    expect(next.ty).toBe(view.ty);
  });

  it("(b) clamps at the MIN bound and stops tx/ty from drifting further", () => {
    const view: ViewTransform = { tx: 12, ty: -7, scale: 0.2 };
    const next = zoomAt(view, 50, 50, 0.01);
    expect(next.scale).toBe(0.2);
    expect(next.tx).toBe(view.tx);
    expect(next.ty).toBe(view.ty);
  });

  it("(c) factor 1 is a no-op (identity)", () => {
    const view: ViewTransform = { tx: 15, ty: -8, scale: 1.5 };
    const next = zoomAt(view, 123, 45, 1);
    expect(next).toEqual(view);
  });
});

describe("fitView", () => {
  it("fits-wide: a canvas-relatively-wide content is width-constrained", () => {
    // canvas 1000x1000, margin 48 -> available 904x904. Content 2000x500:
    // scaleW = 904/2000 = 0.452, scaleH = 904/500 = 1.808 -> min is scaleW.
    const view = fitView(1000, 1000, 2000, 500, 48);
    expect(view.scale).toBeCloseTo(0.452, 10);
    expect(view.tx).toBeCloseTo((1000 - 2000 * 0.452) / 2, 10);
    expect(view.ty).toBeCloseTo((1000 - 500 * 0.452) / 2, 10);
  });

  it("fits-tall: a canvas-relatively-tall content is height-constrained", () => {
    // Same canvas/margin. Content 500x2000:
    // scaleW = 904/500 = 1.808, scaleH = 904/2000 = 0.452 -> min is scaleH.
    const view = fitView(1000, 1000, 500, 2000, 48);
    expect(view.scale).toBeCloseTo(0.452, 10);
    expect(view.tx).toBeCloseTo((1000 - 500 * 0.452) / 2, 10);
    expect(view.ty).toBeCloseTo((1000 - 2000 * 0.452) / 2, 10);
  });

  it("upscale-cap: tiny content is capped at scale 2, not blown up further", () => {
    // canvas 1000x1000, margin 48 -> available 904x904. Content 10x10:
    // raw min ratio is 90.4, but the cap clamps it to 2.
    const view = fitView(1000, 1000, 10, 10, 48);
    expect(view.scale).toBe(2);
    expect(view.tx).toBeCloseTo((1000 - 10 * 2) / 2, 10);
    expect(view.ty).toBeCloseTo((1000 - 10 * 2) / 2, 10);
  });

  it("centering math: content is centered on both axes at the computed scale", () => {
    const view = fitView(1440, 900, 800, 400, 48);
    // available: 1344x804. scaleW = 1344/800 = 1.68, scaleH = 804/400 = 2.01
    // -> min is scaleW = 1.68, within [0.2, 2].
    expect(view.scale).toBeCloseTo(1.68, 10);
    expect(view.tx).toBeCloseTo((1440 - 800 * 1.68) / 2, 10);
    expect(view.ty).toBeCloseTo((900 - 400 * 1.68) / 2, 10);
  });

  it("defaults margin to 48 when omitted", () => {
    const withDefault = fitView(1000, 1000, 2000, 500);
    const withExplicit = fitView(1000, 1000, 2000, 500, 48);
    expect(withDefault).toEqual(withExplicit);
  });

  it("clamps the scale down to 0.2 for extremely oversized content", () => {
    const view = fitView(1000, 1000, 100000, 100000, 48);
    expect(view.scale).toBe(0.2);
  });
});
