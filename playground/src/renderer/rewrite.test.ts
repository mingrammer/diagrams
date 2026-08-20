import { describe, expect, it } from "vitest";
import { extractImagePaths, rewriteSvgImages, toIconUrl } from "./rewrite";

const DOT = `digraph "Web Service" {
  a [label=lb image="/lib/python3.12/site-packages/resources/aws/network/elastic-load-balancing.png" shape=none]
  b [label=web image="/lib/python3.12/site-packages/resources/aws/compute/ec2.png" shape=none]
  c [label=web2 image="/lib/python3.12/site-packages/resources/aws/compute/ec2.png" shape=none]
}`;

describe("extractImagePaths", () => {
  it("finds unique image attribute values", () => {
    expect(extractImagePaths(DOT)).toEqual([
      "/lib/python3.12/site-packages/resources/aws/network/elastic-load-balancing.png",
      "/lib/python3.12/site-packages/resources/aws/compute/ec2.png",
    ]);
  });

  it("returns empty array when no images", () => {
    expect(extractImagePaths("digraph { a -> b }")).toEqual([]);
  });
});

describe("toIconUrl", () => {
  it("maps resources paths to icons/ urls", () => {
    expect(toIconUrl("/x/site-packages/resources/aws/compute/ec2.png")).toBe("icons/aws/compute/ec2.png");
  });

  it("returns null for non-resources paths", () => {
    expect(toIconUrl("/etc/passwd")).toBeNull();
  });
});

describe("rewriteSvgImages", () => {
  it("rewrites xlink:href to hosted icon urls", () => {
    const svg = `<svg><image xlink:href="/a/resources/aws/compute/ec2.png" width="66px"/></svg>`;
    expect(rewriteSvgImages(svg)).toContain(`xlink:href="icons/aws/compute/ec2.png"`);
  });

  it("blanks external image hrefs so no off-origin requests fire", () => {
    const svg = `<svg><image xlink:href="https://evil.example/x.png"/></svg>`;
    const result = rewriteSvgImages(svg);
    expect(result).not.toContain("evil.example");
    expect(result).toContain(`xlink:href=""`);
  });

  it("passes through already-local icons/ and data: hrefs", () => {
    const svg = `<svg><image href="icons/aws/compute/ec2.png"/><image href="data:image/png;base64,AAAA"/></svg>`;
    const result = rewriteSvgImages(svg);
    expect(result).toContain(`href="icons/aws/compute/ec2.png"`);
    expect(result).toContain(`href="data:image/png;base64,AAAA"`);
  });

  it("does not rewrite hrefs outside <image> elements", () => {
    const svg = `<svg><a xlink:href="https://example.com/resources/aws/page.png"><text>n</text></a><image xlink:href="/x/resources/aws/compute/ec2.png"/></svg>`;
    const result = rewriteSvgImages(svg);
    expect(result).toContain(`<a xlink:href="https://example.com/resources/aws/page.png">`);
    expect(result).toContain(`<image xlink:href="icons/aws/compute/ec2.png"`);
  });
});
