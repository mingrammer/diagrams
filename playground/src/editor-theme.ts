import type { Extension } from "@codemirror/state";
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { EditorView } from "@codemirror/view";
import { tags as t } from "@lezer/highlight";

// Blueprint engineering drawing theme for CodeMirror.
// Static module-level constant — imported once into EditorPane's static
// extension list at mount time (see HARD CONSTRAINT #4 in the redesign spec).
//
// Every color below is a var(--cm-*)/var(--syn-*) reference into app.css's
// per-theme token blocks (:root[data-theme="dark"|"light"]). CodeMirror's
// theme values are plain CSS strings, so var() resolves live against
// document.documentElement's data-theme attribute — flipping the theme
// re-paints the editor instantly with no remount required.

const blueprintEditorTheme = EditorView.theme(
  {
    "&": {
      backgroundColor: "var(--cm-bg)",
      color: "var(--cm-fg)",
      height: "100%",
    },
    ".cm-content": {
      caretColor: "var(--cm-caret)",
      fontFamily: "'IBM Plex Mono', ui-monospace, monospace",
      fontSize: "13px",
    },
    ".cm-cursor, .cm-dropCursor": {
      borderLeftColor: "var(--cm-caret)",
      borderLeftWidth: "2px",
    },
    // `!important` is required here: @codemirror/view's own baseTheme (part
    // of basicSetup) ships a same-named `&dark.cm-focused > .cm-scroller >
    // .cm-selectionLayer .cm-selectionBackground` rule with strictly higher
    // selector specificity (it targets the internal DOM chain, not just the
    // class) that otherwise wins the cascade and paints an opaque `#233`
    // regardless of this token's value or insertion order — that mismatch,
    // not the token color itself, was the actual cause of "selection too
    // dark/opaque" (confirmed via getComputedStyle: it read `rgb(34,51,51)`
    // — CodeMirror's literal default — in both app themes before this fix).
    "&.cm-focused .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection": {
      backgroundColor: "var(--cm-selection) !important",
    },
    ".cm-activeLine": {
      backgroundColor: "var(--cm-active-line)",
    },
    ".cm-gutters": {
      backgroundColor: "var(--cm-gutter-bg)",
      color: "var(--cm-gutter-fg)",
      border: "none",
      borderRight: "1px solid var(--cm-gutter-border)",
    },
    ".cm-activeLineGutter": {
      backgroundColor: "var(--cm-active-gutter-bg)",
      color: "var(--cm-active-gutter-fg)",
    },
    ".cm-lineNumbers .cm-gutterElement": {
      fontFamily: "'IBM Plex Mono', ui-monospace, monospace",
    },
    ".cm-selectionMatch": {
      backgroundColor: "var(--cm-selection-match)",
    },
    ".cm-matchingBracket, .cm-nonmatchingBracket": {
      backgroundColor: "var(--cm-matching-bracket-bg)",
      outline: "1px solid var(--cm-matching-bracket-outline)",
    },
    ".cm-tooltip": {
      backgroundColor: "var(--cm-tooltip-bg)",
      border: "1px solid var(--cm-tooltip-border)",
      color: "var(--cm-tooltip-fg)",
      fontFamily: "'IBM Plex Mono', ui-monospace, monospace",
    },
    ".cm-tooltip-autocomplete ul li[aria-selected]": {
      backgroundColor: "var(--cm-autocomplete-selected-bg)",
      color: "var(--cm-autocomplete-selected-fg)",
    },
  },
  { dark: true }
);

const blueprintHighlightStyle = HighlightStyle.define([
  { tag: t.keyword, color: "var(--syn-keyword)" },
  { tag: [t.string, t.special(t.string)], color: "var(--syn-string)" },
  { tag: [t.comment, t.lineComment, t.blockComment, t.docComment], color: "var(--syn-comment)", fontStyle: "italic" },
  {
    tag: [t.function(t.variableName), t.function(t.definition(t.variableName)), t.className, t.definition(t.className)],
    color: "var(--syn-function)",
  },
  { tag: [t.number, t.integer, t.float], color: "var(--syn-number)" },
  { tag: [t.operator, t.punctuation, t.bracket], color: "var(--syn-operator)" },
  { tag: t.variableName, color: "var(--syn-variable)" },
  { tag: t.propertyName, color: "var(--syn-property)" },
  { tag: [t.bool, t.null], color: "var(--syn-bool)" },
  { tag: t.definition(t.variableName), color: "var(--syn-variable)" },
  { tag: t.atom, color: "var(--syn-atom)" },
]);

export const blueprintTheme: Extension = [blueprintEditorTheme, syntaxHighlighting(blueprintHighlightStyle)];
