// Pure helper for the preview pane's header meta line. Graphviz marks every
// node and edge group with an exact class="node"/class="edge" attribute
// (verified against @hpcc-js/wasm-graphviz output — see render.test.ts for
// the same SVG shape), so a literal substring count is enough and avoids
// pulling in a DOM/XML parser just to count groups.
export interface SvgStats {
  nodes: number;
  edges: number;
}

function countOccurrences(haystack: string, needle: string): number {
  if (!haystack) return 0;
  let count = 0;
  let index = haystack.indexOf(needle);
  while (index !== -1) {
    count++;
    index = haystack.indexOf(needle, index + needle.length);
  }
  return count;
}

export function svgStats(svg: string): SvgStats {
  return {
    nodes: countOccurrences(svg, 'class="node"'),
    edges: countOccurrences(svg, 'class="edge"'),
  };
}
