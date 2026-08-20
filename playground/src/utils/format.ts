// Pure display-formatting helpers. `formatStars` renders a GitHub-style
// star count: plain below 1000, one decimal "k" above it with a trailing
// ".0" stripped (24340 -> "24.3k", 24040 -> "24k"). Rounds to the nearest
// hundred before dividing by 1000 (rather than rounding the divided value)
// to avoid float-precision artifacts like 24.299999999999997.
export function formatStars(n: number): string {
  if (n < 1000) return String(n);
  const tenths = Math.round(n / 100);
  const k = tenths / 10;
  const str = Number.isInteger(k) ? String(k) : k.toFixed(1);
  return `${str}k`;
}
