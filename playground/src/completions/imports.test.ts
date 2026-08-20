import { CompletionContext, CompletionResult } from "@codemirror/autocomplete";
import { EditorState } from "@codemirror/state";
import { describe, expect, it } from "vitest";
import type { Catalog } from "../types";
import { diagramsCompletions, moduleSegments, parseImports } from "./imports";

function ctx(doc: string, pos = doc.length, explicit = false): CompletionContext {
  return new CompletionContext(EditorState.create({ doc }), pos, explicit);
}

const CATALOG: Catalog = {
  modules: {
    "diagrams.aws.compute": [
      { name: "EC2", aliases: [], icon: "aws/compute/ec2.png" },
      { name: "ElasticContainerService", aliases: ["ECS"], icon: "aws/compute/x.png" },
    ],
    "diagrams.aws.database": [{ name: "RDS", aliases: [], icon: "aws/database/rds.png" }],
    "diagrams.gcp.compute": [{ name: "GCE", aliases: [], icon: "gcp/compute/gce.png" }],
  },
  signatures: { Diagram: [], Cluster: [], Edge: [] },
};

describe("parseImports", () => {
  it("collects plain and aliased names", () => {
    const doc = "from diagrams import Diagram\nfrom diagrams.aws.compute import EC2, ElasticContainerService as ECS\n";
    const names = parseImports(doc);
    expect(names.get("Diagram")).toBe("diagrams.Diagram");
    expect(names.get("EC2")).toBe("diagrams.aws.compute.EC2");
    expect(names.get("ECS")).toBe("diagrams.aws.compute.ElasticContainerService");
  });

  it("ignores non-import lines", () => {
    expect(parseImports("x = 1\n# from fake import Y\n").size).toBe(0);
  });
});

describe("moduleSegments", () => {
  it("lists next segments for a prefix", () => {
    expect(moduleSegments(CATALOG, "diagrams.")).toEqual(["aws", "gcp"]);
    expect(moduleSegments(CATALOG, "diagrams.aws.")).toEqual(["compute", "database"]);
  });
});

describe("diagramsCompletions", () => {
  const source = diagramsCompletions(CATALOG);

  it("completes next segments after a dotted prefix", () => {
    const r = source(ctx("from diagrams.aws.")) as CompletionResult;
    expect(r.options.map((o) => o.label)).toEqual(["compute", "database"]);
    expect(r.from).toBe("from diagrams.aws.".length);
  });

  it("offers the root module while typing it (no corruption)", () => {
    const r = source(ctx("from diag")) as CompletionResult;
    expect(r.options.map((o) => o.label)).toEqual(["diagrams"]);
    expect(r.from).toBe("from ".length);
  });

  it("handles extra whitespace after from", () => {
    const r = source(ctx("from  diagrams.")) as CompletionResult;
    expect(r.from).toBe("from  diagrams.".length);
    expect(r.options.map((o) => o.label)).toEqual(["aws", "gcp"]);
  });

  it("completes classes when an earlier name is aliased", () => {
    const r = source(ctx("from diagrams.aws.compute import EC2 as E, EC")) as CompletionResult;
    expect(r.options.some((o) => o.label === "ElasticContainerService")).toBe(true);
    expect(r.from).toBe("from diagrams.aws.compute import EC2 as E, ".length);
  });
});

describe("parseImports parenthesized", () => {
  it("handles multiline parenthesized imports with aliases", () => {
    const doc = "from diagrams.aws.compute import (\n    EC2,\n    ElasticContainerService as ECS,\n)\n";
    const names = parseImports(doc);
    expect(names.get("EC2")).toBe("diagrams.aws.compute.EC2");
    expect(names.get("ECS")).toBe("diagrams.aws.compute.ElasticContainerService");
  });
});
