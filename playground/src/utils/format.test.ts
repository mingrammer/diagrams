import { describe, expect, it } from "vitest";
import { formatStars } from "./format";

describe("formatStars", () => {
  it("returns the plain integer below 1000", () => {
    expect(formatStars(512)).toBe("512");
  });

  it("formats exactly 1000 as 1k (trailing .0 stripped)", () => {
    expect(formatStars(1000)).toBe("1k");
  });

  it("formats with one decimal when non-zero", () => {
    expect(formatStars(24340)).toBe("24.3k");
  });

  it("strips a trailing .0", () => {
    expect(formatStars(24040)).toBe("24k");
  });
});
