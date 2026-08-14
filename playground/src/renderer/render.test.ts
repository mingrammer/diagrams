import { describe, expect, it } from "vitest";
import { renderDot } from "./render";

describe("renderDot", () => {
  it("renders plain dot to svg", async () => {
    const svg = await renderDot("digraph { a -> b }");
    expect(svg).toContain("<svg");
    // Graphviz emits the edge title as "a&#45;&gt;b" (hyphen as a numeric
    // character reference), but DOMPurify's DOM parse/serialize round-trip
    // normalizes "&#45;" to the literal "-" character, since re-encoding a
    // plain hyphen is never required for well-formed XML/HTML. This is true
    // of any spec-compliant DOM serializer, not just DOMPurify (verified
    // directly with jsdom's DOMParser/XMLSerializer). See task-5-report.md.
    expect(svg).toContain("a-&gt;b");
  }, 30_000);

  it("keeps image nodes and rewrites their hrefs", async () => {
    const dot = `digraph {
      n [label="web" height="1.9" image="/site-packages/resources/aws/compute/ec2.png" shape=none fixedsize=true width="1.4"]
    }`;
    const svg = await renderDot(dot);
    expect(svg).toContain(`icons/aws/compute/ec2.png`);
  }, 30_000);

  it("strips script elements injected via labels", async () => {
    const svg = await renderDot(`digraph { a [label="<<script>alert(1)</script>x>"] }`);
    expect(svg).not.toContain("<script");
  }, 30_000);

  it("throws on invalid dot", async () => {
    await expect(renderDot("digraph {")).rejects.toThrow();
  }, 30_000);
});
