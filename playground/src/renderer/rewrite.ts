const IMAGE_ATTR = /image="([^"]+)"/g;
const RESOURCES_SEGMENT = /\/resources\/(.+)$/;
const IMAGE_TAG = /<image\b[^>]*>/g;

export function extractImagePaths(dot: string): string[] {
  const paths = new Set<string>();
  for (const match of dot.matchAll(IMAGE_ATTR)) paths.add(match[1]);
  return [...paths];
}

export function toIconUrl(absPath: string): string | null {
  const match = absPath.match(RESOURCES_SEGMENT);
  return match ? `icons/${match[1]}` : null;
}

export function rewriteSvgImages(svg: string): string {
  return svg.replace(IMAGE_TAG, (tag) =>
    tag.replace(/(xlink:href|href)="([^"]*)"/g, (_full, attr, value) => {
      const iconUrl = toIconUrl(value);
      if (iconUrl) return `${attr}="${iconUrl}"`;
      // Pass through already-safe local/inline references; blank anything
      // else. The sanitized SVG is injected into the DOM, so an external
      // href from user-controlled DOT could otherwise fire off-origin
      // image requests (tracking pixels, etc.).
      if (value.startsWith("icons/") || value.startsWith("data:")) return `${attr}="${value}"`;
      return `${attr}=""`;
    })
  );
}
