import { describe, expect, it } from "vitest";
import { renameDiagramInCode } from "./rename";

describe("renameDiagramInCode", () => {
  it("renames a double-quoted Diagram name", () => {
    const code = 'with Diagram("Web Service", show=False):\n    pass\n';
    expect(renameDiagramInCode(code, 0, "Renamed Arch")).toBe(
      'with Diagram("Renamed Arch", show=False):\n    pass\n'
    );
  });

  it("renames a single-quoted Diagram name", () => {
    const code = "with Diagram('Web Service', show=False):\n    pass\n";
    expect(renameDiagramInCode(code, 0, "Renamed Arch")).toBe(
      "with Diagram('Renamed Arch', show=False):\n    pass\n"
    );
  });

  it("renames the second occurrence (index 1), leaving the first untouched", () => {
    const code =
      'with Diagram("First", show=False):\n    pass\n\nwith Diagram("Second", show=False):\n    pass\n';
    expect(renameDiagramInCode(code, 1, "Renamed")).toBe(
      'with Diagram("First", show=False):\n    pass\n\nwith Diagram("Renamed", show=False):\n    pass\n'
    );
  });

  it("returns null when the argument is a variable, not a string literal", () => {
    const code = "name = \"Web Service\"\nwith Diagram(name, show=False):\n    pass\n";
    expect(renameDiagramInCode(code, 0, "Renamed")).toBeNull();
  });

  it("returns null when the requested occurrence doesn't exist", () => {
    const code = 'with Diagram("Only One", show=False):\n    pass\n';
    expect(renameDiagramInCode(code, 1, "Renamed")).toBeNull();
  });

  it("escapes double quotes and backslashes when rewriting a double-quoted literal", () => {
    const code = 'with Diagram("Web Service", show=False):\n    pass\n';
    expect(renameDiagramInCode(code, 0, 'He said "hi" \\ there')).toBe(
      'with Diagram("He said \\"hi\\" \\\\ there", show=False):\n    pass\n'
    );
  });

  it("escapes single quotes and backslashes when rewriting a single-quoted literal", () => {
    const code = "with Diagram('Web Service', show=False):\n    pass\n";
    expect(renameDiagramInCode(code, 0, "It's a \\ test")).toBe(
      "with Diagram('It\\'s a \\\\ test', show=False):\n    pass\n"
    );
  });

  it("allows an empty new name", () => {
    const code = 'with Diagram("Web Service", show=False):\n    pass\n';
    expect(renameDiagramInCode(code, 0, "")).toBe('with Diagram("", show=False):\n    pass\n');
  });

  it("tolerates whitespace between Diagram( and the string literal", () => {
    const code = 'with Diagram(  "Web Service", show=False):\n    pass\n';
    expect(renameDiagramInCode(code, 0, "Renamed")).toBe(
      'with Diagram(  "Renamed", show=False):\n    pass\n'
    );
  });
});
