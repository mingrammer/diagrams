import { describe, expect, it } from "vitest";
import type { Catalog } from "../types";
import { searchCatalog } from "./search";

const CATALOG: Catalog = {
  modules: {
    "diagrams.aws.compute": [
      { name: "EC2", aliases: [], icon: "aws/compute/ec2.png" },
      { name: "EC2AutoScaling", aliases: [], icon: "aws/compute/ec2-auto-scaling.png" },
      { name: "ElasticContainerService", aliases: ["ECS"], icon: "aws/compute/ecs.png" },
    ],
    "diagrams.onprem.database": [{ name: "PostgreSQL", aliases: ["Postgresql"], icon: "onprem/database/postgresql.png" }],
  },
  signatures: { Diagram: [], Cluster: [], Edge: [] },
};

describe("searchCatalog", () => {
  it("ranks exact match first, then prefix, then substring", () => {
    const hits = searchCatalog(CATALOG, "ec2");
    expect(hits[0].name).toBe("EC2");
    expect(hits[1].name).toBe("EC2AutoScaling");
  });

  it("matches aliases and reports the alias as name", () => {
    const hits = searchCatalog(CATALOG, "ecs");
    expect(hits.some((h) => h.name === "ECS")).toBe(true);
  });

  it("builds a ready-to-paste import statement", () => {
    const [hit] = searchCatalog(CATALOG, "postgresql");
    expect(hit.importStmt).toBe("from diagrams.onprem.database import PostgreSQL");
  });

  it("returns empty for blank query", () => {
    expect(searchCatalog(CATALOG, "  ")).toEqual([]);
  });

  it("builds importStmt from the matched alias so insert binds the shown name", () => {
    const hit = searchCatalog(CATALOG, "ecs").find((h) => h.name === "ECS");
    expect(hit?.importStmt).toBe("from diagrams.aws.compute import ECS");
  });

  it("dedupes case-insensitively identical alias/name pairs", () => {
    const hits = searchCatalog(CATALOG, "postgresql");
    expect(hits).toHaveLength(1);
    expect(hits[0].name).toBe("PostgreSQL");
    expect(hits[0].importStmt).toBe("from diagrams.onprem.database import PostgreSQL");
  });
});
