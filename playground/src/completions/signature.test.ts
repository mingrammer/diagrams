import { describe, expect, it } from "vitest";
import { findCallContext, lookupSignature } from "./signature";

describe("findCallContext", () => {
  it("returns the innermost open call", () => {
    expect(findCallContext('with Diagram("web", ')).toBe("Diagram");
    expect(findCallContext("Edge(color=")).toBe("Edge");
    expect(findCallContext('Cluster("db", graph_attr={')).toBe("Cluster");
  });

  it("ignores completed calls", () => {
    expect(findCallContext('EC2("web") >> ')).toBeNull();
    expect(findCallContext("x = 1")).toBeNull();
  });

  it("handles nesting", () => {
    expect(findCallContext('Diagram("a", graph_attr=dict(')).toBe("dict");
  });
});

describe("lookupSignature", () => {
  it("returns params for known functions", () => {
    expect(lookupSignature({ Diagram: ["name: str = ''"] }, "Diagram")).toEqual(["name: str = ''"]);
  });

  it("ignores prototype-chain names", () => {
    expect(lookupSignature({}, "constructor")).toBeNull();
    expect(lookupSignature({}, "toString")).toBeNull();
  });

  it("returns null for null or unknown names", () => {
    expect(lookupSignature({ Diagram: [] }, null)).toBeNull();
    expect(lookupSignature({ Diagram: [] }, "Edge")).toBeNull();
  });
});
