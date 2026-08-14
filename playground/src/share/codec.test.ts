import { describe, expect, it } from "vitest";
import { decodeShare, encodeShare } from "./codec";

describe("share codec", () => {
  it("roundtrips code through encode/decode", () => {
    const code = 'from diagrams import Diagram\nwith Diagram("웹", show=False):\n    pass\n';
    expect(decodeShare(encodeShare(code))).toBe(code);
  });

  it("produces URL-safe output (no +, /, =)", () => {
    const encoded = encodeShare("a".repeat(500));
    expect(encoded).not.toMatch(/[+/=]/);
  });

  it("decodes a full '#code=...' fragment", () => {
    const encoded = encodeShare("x = 1");
    expect(decodeShare(`#code=${encoded}`)).toBe("x = 1");
  });

  it("returns null for garbage input", () => {
    expect(decodeShare("#code=!!notbase64!!")).toBeNull();
    expect(decodeShare("")).toBeNull();
  });
});
