import type { Catalog, CatalogClass } from "../types";

export interface TreeCategory {
  module: string;
  category: string;
  classes: CatalogClass[];
}

export interface TreeProvider {
  provider: string;
  count: number;
  categories: TreeCategory[];
}

// Groups catalog module keys ("diagrams.<provider>.<category>") into a
// provider -> category -> classes tree for the sidebar's collapsed browse view.
//
// Two-segment modules ("diagrams.<provider>", e.g. a provider with no
// sub-category — diagrams.c4 in some catalogs) have no category segment;
// they're grouped under the provider with category "" so they still surface
// as a (single) expandable row instead of being dropped.
export function catalogTree(catalog: Catalog): TreeProvider[] {
  const byProvider = new Map<string, TreeCategory[]>();

  for (const [module, classes] of Object.entries(catalog.modules)) {
    const parts = module.split(".");
    const provider = parts[1] ?? module;
    const category = parts.slice(2).join(".");
    const categories = byProvider.get(provider);
    const entry: TreeCategory = { module, category, classes };
    if (categories) categories.push(entry);
    else byProvider.set(provider, [entry]);
  }

  return [...byProvider.entries()]
    .map(([provider, categories]) => ({
      provider,
      count: categories.reduce((sum, c) => sum + c.classes.length, 0),
      categories: [...categories].sort((a, b) => a.category.localeCompare(b.category)),
    }))
    .sort((a, b) => a.provider.localeCompare(b.provider));
}
