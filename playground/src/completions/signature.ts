import { StateField } from "@codemirror/state";
import { EditorView, Tooltip, showTooltip } from "@codemirror/view";
import type { Extension } from "@codemirror/state";

/** Finds the name of the innermost call that is still open (unclosed) in the
 * text before the cursor.
 *
 * v1 known limitations:
 * (a) No string-literal awareness — unbalanced brackets inside Python strings can
 *     produce a false function context (worst case: wrong/absent tooltip, never a buffer write).
 * (b) buildTooltip is line-scoped — multiline calls lose the tooltip.
 */
export function findCallContext(textBeforeCursor: string): string | null {
  const stack: string[] = [];
  const re = /([A-Za-z_]\w*)?\s*(\(|\)|\[|\]|\{|\})/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(textBeforeCursor))) {
    const [, name, bracket] = match;
    if (bracket === "(") stack.push(name ?? "");
    else if (bracket === "[" || bracket === "{") stack.push("");
    else stack.pop();
  }
  for (let i = stack.length - 1; i >= 0; i--) {
    if (stack[i]) return stack[i];
  }
  return null;
}

/** Own-property, array-checked signature lookup — guards against
 *  prototype-chain names like "constructor" or "toString". */
export function lookupSignature(
  signatures: Record<string, string[]>,
  funcName: string | null
): string[] | null {
  if (!funcName || !Object.hasOwn(signatures, funcName)) return null;
  const params = signatures[funcName];
  return Array.isArray(params) ? params : null;
}

function buildTooltip(signatures: Record<string, string[]>, view: { state: EditorView["state"] }): Tooltip | null {
  const { state } = view;
  const pos = state.selection.main.head;
  const line = state.doc.lineAt(pos);
  const funcName = findCallContext(line.text.slice(0, pos - line.from));
  const params = lookupSignature(signatures, funcName);
  if (!funcName || !params) return null;
  return {
    pos,
    above: true,
    create: () => {
      const dom = document.createElement("div");
      dom.className = "cm-signature-hint";
      dom.textContent = `${funcName}(${params.join(", ")})`;
      return { dom };
    },
  };
}

export function signatureTooltip(signatures: Record<string, string[]>): Extension {
  const field = StateField.define<Tooltip | null>({
    create: (state) => buildTooltip(signatures, { state }),
    update(value, tr) {
      if (!tr.docChanged && !tr.selection) return value;
      return buildTooltip(signatures, { state: tr.state });
    },
    provide: (f) => showTooltip.from(f),
  });
  return [field];
}
