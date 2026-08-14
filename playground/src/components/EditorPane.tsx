import { indentWithTab } from "@codemirror/commands";
import { python } from "@codemirror/lang-python";
import { Extension } from "@codemirror/state";
import { EditorView, keymap } from "@codemirror/view";
import { basicSetup } from "codemirror";
import { useEffect, useRef } from "react";
import { blueprintTheme } from "../editor-theme";

interface Props {
  initialCode: string;
  extensions?: Extension[];
  lineCount: number;
  onChange: (code: string) => void;
  onReplaceRef?: (replace: (code: string) => void) => void;
  /** Mod-Enter: run the current code immediately (skips the debounce). */
  onRunNow?: () => void;
  /** Mod-S: share (intercepts the browser's save dialog). */
  onShare?: () => void;
}

export default function EditorPane({
  initialCode,
  extensions = [],
  lineCount,
  onChange,
  onReplaceRef,
  onRunNow,
  onShare,
}: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  // Keep the latest callbacks without remounting the view (avoids stale
  // closures if prop identities change after mount).
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;
  const onRunNowRef = useRef(onRunNow);
  onRunNowRef.current = onRunNow;
  const onShareRef = useRef(onShare);
  onShareRef.current = onShare;

  // NOTE: `extensions` and `initialCode` are intentionally captured once at
  // mount — the App mounts EditorPane only after the catalog is loaded, so
  // extensions are stable for the lifetime of the view.
  useEffect(() => {
    const view = new EditorView({
      doc: initialCode,
      parent: hostRef.current!,
      extensions: [
        // Playground-level bindings, ahead of basicSetup so they win:
        // Mod-Enter = run now (skip debounce), Mod-S = share link instead of
        // the browser's useless save dialog.
        keymap.of([
          {
            key: "Mod-Enter",
            preventDefault: true,
            run: () => {
              onRunNowRef.current?.();
              return true;
            },
          },
          {
            key: "Mod-s",
            preventDefault: true,
            run: () => {
              onShareRef.current?.();
              return true;
            },
          },
        ]),
        basicSetup,
        // basicSetup's default keymap doesn't bind Tab (that's deliberate
        // upstream, so Tab still moves focus for a11y by default) — add it
        // back explicitly so Tab indents code, matching every code editor's
        // expected behavior here. autocompletion's own Tab-to-accept binding
        // (wired in App.tsx via `extensions`, spread in below) still wins
        // while a completion popup is open — CodeMirror gives it higher
        // precedence internally — so this only fires when no popup is open.
        keymap.of([indentWithTab]),
        python(),
        blueprintTheme,
        EditorView.updateListener.of((update) => {
          if (update.docChanged) onChangeRef.current(update.state.doc.toString());
        }),
        ...extensions,
      ],
    });
    onReplaceRef?.((code) => {
      view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: code } });
    });
    return () => view.destroy();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="editor-pane-wrap" data-testid="editor">
      <div className="editor-topbar">
        <span className="editor-filename">main.py</span>
        <span className="editor-linecount">{lineCount} lines</span>
      </div>
      <div ref={hostRef} className="editor-pane" />
    </div>
  );
}
