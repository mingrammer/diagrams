import { describe, expect, it } from "vitest";
import { clampRatio, clampSidebarWidth, DEFAULT_SIDEBAR_WIDTH } from "./layout";

describe("clampRatio", () => {
  it("passes through values within the 25-75 range", () => {
    expect(clampRatio(50)).toBe(50);
    expect(clampRatio(30)).toBe(30);
    expect(clampRatio(70)).toBe(70);
  });

  it("clamps values below 25 up to 25", () => {
    expect(clampRatio(10)).toBe(25);
    expect(clampRatio(-100)).toBe(25);
  });

  it("clamps values above 75 down to 75", () => {
    expect(clampRatio(90)).toBe(75);
    expect(clampRatio(1000)).toBe(75);
  });

  it("clamps exactly at the boundaries", () => {
    expect(clampRatio(25)).toBe(25);
    expect(clampRatio(75)).toBe(75);
  });

  it("defaults to 50 for NaN input", () => {
    expect(clampRatio(NaN)).toBe(50);
  });
});

describe("clampSidebarWidth", () => {
  it("passes through in-range widths", () => {
    expect(clampSidebarWidth(260)).toBe(260);
    expect(clampSidebarWidth(300)).toBe(300);
  });

  it("clamps to the 180-420 bounds", () => {
    expect(clampSidebarWidth(50)).toBe(180);
    expect(clampSidebarWidth(9999)).toBe(420);
  });

  it("falls back to the default for NaN", () => {
    expect(clampSidebarWidth(Number.NaN)).toBe(DEFAULT_SIDEBAR_WIDTH);
  });
});
