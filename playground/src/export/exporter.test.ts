import { describe, expect, it, vi } from "vitest";
import { inlineIcons, resolveSize } from "./exporter";

const PNG_BYTES = new Uint8Array([137, 80, 78, 71]);

function fakeFetch(): typeof fetch {
  return vi.fn(async () => new Response(PNG_BYTES.buffer, { status: 200 })) as unknown as typeof fetch;
}

describe("inlineIcons", () => {
  it("replaces icons/ hrefs with data URIs", async () => {
    const svg = `<svg><image xlink:href="icons/aws/compute/ec2.png"/></svg>`;
    const result = await inlineIcons(svg, fakeFetch());
    expect(result).toContain("data:image/png;base64,iVBORw==".slice(0, 30));
    expect(result).not.toContain("icons/aws");
  });

  it("fetches each unique icon once", async () => {
    const fetcher = fakeFetch();
    const svg = `<svg><image xlink:href="icons/a.png"/><image xlink:href="icons/a.png"/><image xlink:href="icons/b.png"/></svg>`;
    await inlineIcons(svg, fetcher);
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("leaves svg without icons untouched", async () => {
    const svg = "<svg><text>hi</text></svg>";
    expect(await inlineIcons(svg, fakeFetch())).toBe(svg);
  });

  it("rejects when an icon fetch returns non-ok", async () => {
    const fetcher = vi.fn(async () => new Response("nope", { status: 404 })) as unknown as typeof fetch;
    const svg = `<svg><image xlink:href="icons/a.png"/></svg>`;
    await expect(inlineIcons(svg, fetcher)).rejects.toThrow("HTTP 404");
  });

  it("uses svg mime for .svg icons", async () => {
    const svg = `<svg><image xlink:href="icons/gis/georchestra/datafeeder.svg"/></svg>`;
    const result = await inlineIcons(svg, fakeFetch());
    expect(result).toContain("data:image/svg+xml;base64,");
  });
});

describe("resolveSize", () => {
  it("defaults to 2x the natural size when both axes are unset", () => {
    expect(resolveSize(100, 50)).toEqual({ w: 200, h: 100 });
  });

  it("treats invalid (non-finite / non-positive) axes as unset, falling back to the 2x default", () => {
    expect(resolveSize(200, 100, 0, Number.NaN)).toEqual({ w: 400, h: 200 });
  });

  it("derives height from the natural aspect ratio when only width is given", () => {
    expect(resolveSize(200, 100, 50)).toEqual({ w: 50, h: 25 });
  });

  it("derives width from the natural aspect ratio when only height is given", () => {
    expect(resolveSize(200, 100, undefined, 25)).toEqual({ w: 50, h: 25 });
  });

  it("uses both axes exactly, allowing aspect distortion", () => {
    expect(resolveSize(200, 100, 300, 50)).toEqual({ w: 300, h: 50 });
  });

  it("clamps each axis to the 16px minimum independently after computation", () => {
    // width=5 -> derived height = round(5 * 100 / 200) = 3, both below 16.
    expect(resolveSize(200, 100, 5)).toEqual({ w: 16, h: 16 });
  });

  it("clamps each axis to the 8192px maximum independently after computation", () => {
    expect(resolveSize(200, 100, 20_000)).toEqual({ w: 8192, h: 8192 });
  });

  it("falls back to the (clamped) 2x default when the natural size is degenerate, ignoring width/height", () => {
    expect(resolveSize(0, 100, 300, 150)).toEqual({ w: 16, h: 200 });
    expect(resolveSize(-10, -20)).toEqual({ w: 16, h: 16 });
  });
});
