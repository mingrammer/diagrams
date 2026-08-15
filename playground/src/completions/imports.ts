import { Completion, CompletionContext, CompletionResult, CompletionSource } from "@codemirror/autocomplete";
import type { Catalog } from "../types";

const IMPORT_LINE = /^from\s+(diagrams(?:\.\w+)*)\s+import\s+(.+)$/;
const PAREN_IMPORT = /from\s+(diagrams(?:\.\w+)*)\s+import\s*\(([^)]*)\)/g;

function addImportNames(names: Map<string, string>, module: string, imports: string): void {
  for (const part of imports.split(",")) {
    const [original, alias] = part.split(/\s+as\s+/).map((s) => s.trim());
    if (!original || !/^\w+$/.test(original)) continue;
    if (alias && !/^\w+$/.test(alias)) continue;
    names.set(alias ?? original, `${module}.${original}`);
  }
}

export function parseImports(doc: string): Map<string, string> {
  const names = new Map<string, string>();

  // Handle parenthesized (possibly multiline) imports first, then strip them
  // from the doc so the per-line pass below doesn't double-process them.
  let remaining = doc;
  for (const match of doc.matchAll(PAREN_IMPORT)) {
    const [whole, module, imports] = match;
    addImportNames(names, module, imports);
    remaining = remaining.replace(whole, "");
  }

  for (const line of remaining.split("\n")) {
    const match = line.trim().match(IMPORT_LINE);
    if (!match) continue;
    const [, module, imports] = match;
    addImportNames(names, module, imports);
  }
  return names;
}

export function moduleSegments(catalog: Catalog, prefix: string): string[] {
  const segments = new Set<string>();
  for (const moduleName of Object.keys(catalog.modules)) {
    const withDot = moduleName + ".";
    if (withDot.startsWith(prefix)) {
      const rest = moduleName.slice(prefix.length);
      if (rest) segments.add(rest.split(".")[0]);
    }
  }
  return [...segments].sort();
}

function iconInfo(icon: string): Completion["info"] {
  return () => {
    const img = document.createElement("img");
    img.src = `icons/${icon}`;
    img.width = 48;
    img.height = 48;
    return img;
  };
}

export function diagramsCompletions(catalog: Catalog): CompletionSource {
  return (context: CompletionContext): CompletionResult | null => {
    // 1) `from diagrams.aws.` — module path segments
    const modMatch = context.matchBefore(/from\s+[\w.]*$/);
    if (modMatch) {
      const typed = modMatch.text.replace(/^from\s+/, "");
      const consumed = modMatch.text.length - typed.length; // actual "from<ws>" width
      const lastDot = typed.lastIndexOf(".");
      const prefix = lastDot === -1 ? "" : typed.slice(0, lastDot + 1);
      const options = moduleSegments(catalog, prefix).map((seg) => ({
        label: seg,
        type: "namespace",
      }));
      if (!options.length) return null;
      return { from: modMatch.from + consumed + prefix.length, options };
    }

    // 2) `from diagrams.aws.compute import EC` — class names
    const clsMatch = context.matchBefore(
      /from\s+(diagrams[\w.]+)\s+import\s+(?:\w+(?:\s+as\s+\w+)?\s*,\s*)*\w*$/,
    );
    if (clsMatch) {
      const module = clsMatch.text.match(/from\s+([\w.]+)/)![1];
      const classes = catalog.modules[module];
      if (!classes) return null;
      const word = context.matchBefore(/\w*$/)!;
      const options: Completion[] = classes.flatMap((cls) => [
        { label: cls.name, type: "class", info: iconInfo(cls.icon) },
        ...cls.aliases.map((alias) => ({
          label: alias,
          type: "class" as const,
          detail: cls.name,
          info: iconInfo(cls.icon),
        })),
      ]);
      return { from: word.from, options };
    }

    // 3) general position — imported names
    const word = context.matchBefore(/\w+$/);
    if (!word && !context.explicit) return null;
    const imported = parseImports(context.state.doc.toString());
    if (!imported.size) return null;
    return {
      from: word?.from ?? context.pos,
      options: [...imported.entries()].map(([name, origin]) => ({
        label: name,
        type: "class",
        detail: origin,
      })),
      validFor: /^\w*$/,
    };
  };
}
