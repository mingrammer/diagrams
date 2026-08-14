import { Graphviz } from "@hpcc-js/wasm-graphviz";
import DOMPurify from "dompurify";
import { extractImagePaths, rewriteSvgImages } from "./rewrite";

let graphvizPromise: Promise<Graphviz> | null = null;

function getGraphviz(): Promise<Graphviz> {
  graphvizPromise ??= Graphviz.load().catch((err) => {
    graphvizPromise = null; // allow retry on the next render call
    throw err;
  });
  return graphvizPromise;
}

export async function renderDot(dot: string): Promise<string> {
  const graphviz = await getGraphviz();
  // Register each referenced icon as a stub file so Graphviz emits the
  // <image> element. Node sizes are fixed (fixedsize=true) so the stub
  // dimensions do not affect layout.
  const images = extractImagePaths(dot).map((path) => ({
    path,
    width: "256px",
    height: "256px",
  }));
  const svg = graphviz.layout(dot, "svg", "dot", { images });
  if (!svg) throw new Error("Graphviz returned empty output");
  return DOMPurify.sanitize(rewriteSvgImages(svg), {
    USE_PROFILES: { svg: true, svgFilters: true },
    ADD_TAGS: ["image"],
    ADD_ATTR: ["xlink:href"],
  });
}
