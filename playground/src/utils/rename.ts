// Pure text-rewrite helper for the preview header's click-to-edit diagram
// title. Deliberately does not parse Python — it locates the (index+1)-th
// `Diagram(` call and, only when its first argument is a plain quoted string
// literal, replaces the literal's contents. Anything it can't confidently
// rewrite (missing occurrence, non-literal argument such as `Diagram(name)`)
// returns null so the caller can silently revert the UI edit rather than risk
// corrupting the user's code.
const DIAGRAM_CALL_RE = /\bDiagram\(\s*/g;

function escapeForQuote(value: string, quote: string): string {
  return value.replace(/\\/g, "\\\\").split(quote).join(`\\${quote}`);
}

export function renameDiagramInCode(code: string, index: number, newName: string): string | null {
  DIAGRAM_CALL_RE.lastIndex = 0;
  let match: RegExpExecArray | null;
  let occurrence = -1;
  while ((match = DIAGRAM_CALL_RE.exec(code)) !== null) {
    occurrence++;
    if (occurrence !== index) continue;

    const literalStart = match.index + match[0].length;
    const quote = code[literalStart];
    if (quote !== '"' && quote !== "'") return null;

    let i = literalStart + 1;
    let closed = false;
    while (i < code.length) {
      const ch = code[i];
      if (ch === "\\" && i + 1 < code.length) {
        i += 2;
        continue;
      }
      if (ch === quote) {
        closed = true;
        break;
      }
      i++;
    }
    if (!closed) return null;

    const escaped = escapeForQuote(newName, quote);
    return code.slice(0, literalStart + 1) + escaped + code.slice(i);
  }
  return null;
}
