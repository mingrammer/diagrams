import { describe, expect, it } from "vitest";
import type { Catalog } from "../types";
import { catalogTree } from "./tree";

const CATALOG: Catalog = {
  modules: {
    "diagrams.aws.compute": [
      { name: "EC2", aliases: [], icon: "aws/compute/ec2.png" },
      { name: "EC2AutoScaling", aliases: [], icon: "aws/compute/ec2-auto-scaling.png" },
    ],
    "diagrams.aws.database": [{ name: "RDS", aliases: [], icon: "aws/database/rds.png" }],
    // Two-segment module: diagrams.<provider> with no category segment.
    "diagrams.aws": [{ name: "AWS", aliases: [], icon: "aws/aws.png" }],
    "diagrams.gcp.compute": [{ name: "GCE", aliases: [], icon: "gcp/compute/gce.png" }],
    // Provider that only ever appears as a two-segment module.
    "diagrams.c4": [
      { name: "Person", aliases: [], icon: "c4/person.png" },
      { name: "System", aliases: [], icon: "c4/system.png" },
    ],
  },
  signatures: {},
};

describe("catalogTree", () => {
  const tree = catalogTree(CATALOG);

  it("groups modules by provider (the segment after 'diagrams')", () => {
    expect(tree.map((p) => p.provider)).toEqual(["aws", "c4", "gcp"]);
  });

  it("sorts providers alphabetically", () => {
    const providers = tree.map((p) => p.provider);
    expect(providers).toEqual([...providers].sort());
  });

  it("sorts categories alphabetically within a provider", () => {
    const aws = tree.find((p) => p.provider === "aws")!;
    const categories = aws.categories.map((c) => c.category);
    expect(categories).toEqual([...categories].sort());
  });

  it("counts total classes under each provider, across all its modules", () => {
    const aws = tree.find((p) => p.provider === "aws")!;
    // 2 (compute) + 1 (database) + 1 (bare diagrams.aws) = 4
    expect(aws.count).toBe(4);

    const gcp = tree.find((p) => p.provider === "gcp")!;
    expect(gcp.count).toBe(1);

    const c4 = tree.find((p) => p.provider === "c4")!;
    expect(c4.count).toBe(2);
  });

  it("handles the two-segment module case (diagrams.<provider> with no category) gracefully", () => {
    const aws = tree.find((p) => p.provider === "aws")!;
    const bareCategory = aws.categories.find((c) => c.module === "diagrams.aws")!;
    expect(bareCategory).toBeDefined();
    expect(bareCategory.classes.map((c) => c.name)).toEqual(["AWS"]);

    const c4 = tree.find((p) => p.provider === "c4")!;
    expect(c4.categories).toHaveLength(1);
    expect(c4.categories[0].module).toBe("diagrams.c4");
    expect(c4.categories[0].classes.map((c) => c.name)).toEqual(["Person", "System"]);
  });

  it("preserves each category's module key and classes", () => {
    const aws = tree.find((p) => p.provider === "aws")!;
    const compute = aws.categories.find((c) => c.module === "diagrams.aws.compute")!;
    expect(compute.category).toBe("compute");
    expect(compute.classes.map((c) => c.name)).toEqual(["EC2", "EC2AutoScaling"]);
  });

  it("returns an empty array for an empty catalog", () => {
    expect(catalogTree({ modules: {}, signatures: {} })).toEqual([]);
  });
});
