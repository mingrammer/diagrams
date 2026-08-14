export interface DotResult {
  name: string;
  source: string;
}

export interface RunResult {
  dots: DotResult[];
  stdout: string;
  error: string | null;
}

export type ProgressStage = "pyodide" | "packages" | "ready";

export interface CatalogClass {
  name: string;
  aliases: string[];
  icon: string;
}

export interface Catalog {
  modules: Record<string, CatalogClass[]>;
  signatures: Record<string, string[]>;
}
