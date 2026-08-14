import type { Catalog } from "../types";

export interface SearchHit {
  module: string;
  name: string;
  icon: string;
  importStmt: string;
}

function rank(candidate: string, query: string): number {
  const lower = candidate.toLowerCase();
  if (lower === query) return 0;
  if (lower.startsWith(query)) return 1;
  if (lower.includes(query)) return 2;
  return -1;
}

export function searchCatalog(catalog: Catalog, query: string, limit = 50): SearchHit[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const scored: (SearchHit & { score: number })[] = [];
  for (const [module, classes] of Object.entries(catalog.modules)) {
    for (const cls of classes) {
      const candidates = [
        cls.name,
        ...cls.aliases.filter((a) => a.toLowerCase() !== cls.name.toLowerCase()),
      ];
      for (const name of candidates) {
        const score = rank(name, q);
        if (score >= 0) {
          scored.push({
            module,
            name,
            icon: cls.icon,
            importStmt: `from ${module} import ${name}`,
            score,
          });
        }
      }
    }
  }
  scored.sort((a, b) => a.score - b.score || a.name.length - b.name.length || a.name.localeCompare(b.name));
  return scored.slice(0, limit).map(({ score: _score, ...hit }) => hit);
}
