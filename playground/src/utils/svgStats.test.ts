import { describe, expect, it } from "vitest";
import { svgStats } from "./svgStats";

const SAMPLE_SVG = `<svg>
<g id="graph0" class="graph">
<g id="node1" class="node"><title>a</title></g>
<g id="node2" class="node"><title>b</title></g>
<g id="node3" class="node"><title>c</title></g>
<g id="edge1" class="edge"><title>a-&gt;b</title></g>
<g id="edge2" class="edge"><title>b-&gt;c</title></g>
</g>
</svg>`;

describe("svgStats", () => {
  it("counts node and edge groups in a rendered graphviz svg", () => {
    expect(svgStats(SAMPLE_SVG)).toEqual({ nodes: 3, edges: 2 });
  });

  it("returns zeros for an empty string", () => {
    expect(svgStats("")).toEqual({ nodes: 0, edges: 0 });
  });

  it("returns zeros when there are no node/edge groups", () => {
    expect(svgStats(`<svg><g id="graph0" class="graph"></g></svg>`)).toEqual({ nodes: 0, edges: 0 });
  });

  it("does not count unrelated classes like graph or cluster", () => {
    const svg = `<g class="graph"></g><g class="cluster"></g><g class="node"></g>`;
    expect(svgStats(svg)).toEqual({ nodes: 1, edges: 0 });
  });

  it("counts single node and single edge", () => {
    const svg = `<g class="node"></g><g class="edge"></g>`;
    expect(svgStats(svg)).toEqual({ nodes: 1, edges: 1 });
  });
});
