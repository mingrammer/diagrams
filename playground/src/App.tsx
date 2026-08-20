import { autocompletion } from "@codemirror/autocomplete";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import DragHandle from "./components/DragHandle";
import EditorPane from "./components/EditorPane";
import ErrorPanel from "./components/ErrorPanel";
import ExamplesGallery from "./components/ExamplesGallery";
import ExportBar from "./components/ExportBar";
import NodeSearch from "./components/NodeSearch";
import PreviewPane from "./components/PreviewPane";
import Toolbar from "./components/Toolbar";
import { diagramsCompletions } from "./completions/imports";
import { signatureTooltip } from "./completions/signature";
import { DEFAULT_CODE, EXAMPLES } from "./examples";
import { renderDot } from "./renderer/render";
import { decodeShare, encodeShare } from "./share/codec";
import type { Catalog } from "./types";
import { debounce } from "./utils/debounce";
import { clampRatio, clampSidebarWidth, DEFAULT_RATIO, DEFAULT_SIDEBAR_WIDTH } from "./utils/layout";
import { renameDiagramInCode } from "./utils/rename";
import { initTheme } from "./utils/theme";
import { PyClient, SupersededError, TimeoutError } from "./worker/client";

const SPLIT_STORAGE_KEY = "dgp-split";
const SIDEBAR_STORAGE_KEY = "dgp-sidebar";

function loadStoredRatio(): number {
  const stored = Number(localStorage.getItem(SPLIT_STORAGE_KEY));
  return clampRatio(Number.isFinite(stored) && stored !== 0 ? stored : DEFAULT_RATIO);
}

function loadStoredSidebarWidth(): number {
  const stored = Number(localStorage.getItem(SIDEBAR_STORAGE_KEY));
  return clampSidebarWidth(Number.isFinite(stored) && stored !== 0 ? stored : DEFAULT_SIDEBAR_WIDTH);
}

const STATUS_BY_STAGE: Record<string, string> = {
  pyodide: "Loading Python runtime… (first visit only)",
  packages: "Installing diagrams package…",
  ready: "Ready",
};

export default function App() {
  const clientRef = useRef<PyClient>();
  const replaceCodeRef = useRef<(code: string) => void>();
  const codeRef = useRef(decodeShare(window.location.hash) ?? DEFAULT_CODE);

  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [status, setStatus] = useState("Starting…");
  const [ready, setReady] = useState(false);
  const [svgs, setSvgs] = useState<{ name: string; svg: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [rendering, setRendering] = useState(false);
  const [shared, setShared] = useState(false);
  const [splitRatio, setSplitRatio] = useState(loadStoredRatio);
  const [sidebarWidth, setSidebarWidth] = useState(loadStoredSidebarWidth);
  const [lineCount, setLineCount] = useState(() => codeRef.current.split("\n").length);
  // A share-link boot loads its code straight into the editor, so no example
  // pill should read as "active" until the user explicitly picks one.
  const [activeExample, setActiveExample] = useState<string | null>(() =>
    decodeShare(window.location.hash) !== null ? null : EXAMPLES[0].title
  );
  const [renderMs, setRenderMs] = useState<number | null>(null);
  const splitContainerRef = useRef<HTMLDivElement>(null);
  const mainRef = useRef<HTMLElement>(null);

  useEffect(() => {
    initTheme();
  }, []);

  const handleSplitChange = useCallback((ratio: number) => {
    const clamped = clampRatio(ratio);
    setSplitRatio(clamped);
    localStorage.setItem(SPLIT_STORAGE_KEY, String(clamped));
  }, []);

  const handleSidebarChange = useCallback((width: number) => {
    const clamped = clampSidebarWidth(width);
    setSidebarWidth(clamped);
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(clamped));
  }, []);

  const execute = useCallback(async (code: string) => {
    codeRef.current = code;
    const client = clientRef.current;
    if (!client) return;
    setRendering(true);
    const startedAt = performance.now();
    try {
      const result = await client.run(code);
      if (result.error) {
        setError(result.error); // keep the last successful preview on screen
      } else {
        const rendered = await Promise.all(
          result.dots.map(async (d) => ({ name: d.name, svg: await renderDot(d.source) }))
        );
        setSvgs(rendered);
        setError(null);
        setRenderMs(Math.round(performance.now() - startedAt));
      }
    } catch (err) {
      if (err instanceof SupersededError) return;
      if (err instanceof TimeoutError) {
        setError("Execution timed out after 10s. The Python runtime was restarted (infinite loop?).");
      } else {
        setError(String(err));
      }
    } finally {
      setRendering(false);
    }
  }, []);

  const debouncedExecute = useMemo(() => debounce(execute, 500), [execute]);

  // codeRef must track EVERY keystroke immediately — handleShare/insertImport
  // read it synchronously; only the execution is debounced.
  const handleEditorChange = useCallback(
    (code: string) => {
      codeRef.current = code;
      setLineCount(code.split("\n").length);
      debouncedExecute(code);
    },
    [debouncedExecute]
  );

  useEffect(() => {
    fetch("catalog.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(setCatalog)
      .catch((err) => {
        setCatalog(null);
        setCatalogError(
          `Node catalog failed to load (${err instanceof Error ? err.message : String(err)}) — autocomplete and node search are disabled.`
        );
      });

    const client = new PyClient();
    clientRef.current = client;
    client
      .init((stage) => {
        if (clientRef.current === client) setStatus(STATUS_BY_STAGE[stage] ?? stage);
      })
      .then(() => {
        if (clientRef.current !== client) return;
        setReady(true);
        void execute(codeRef.current);
      })
      .catch((err) => {
        if (String(err).includes("disposed")) return; // our own cleanup
        if (clientRef.current === client) setStatus(`Failed to start: ${err}`);
      });
    return () => client.dispose();
  }, [execute]);

  const editorExtensions = useMemo(() => {
    if (!catalog) return [];
    return [
      autocompletion({ override: [diagramsCompletions(catalog)] }),
      signatureTooltip(catalog.signatures),
    ];
  }, [catalog]);

  function handleShare() {
    const hash = `#code=${encodeShare(codeRef.current)}`;
    window.history.replaceState(null, "", hash);
    navigator.clipboard
      .writeText(window.location.href)
      .then(() => {
        setShared(true);
        setTimeout(() => setShared(false), 2000);
      })
      .catch(() => setShared(false));
  }

  function loadCode(code: string) {
    replaceCodeRef.current?.(code);
    void execute(code);
  }

  function insertImport(importStmt: string) {
    loadCode(`${importStmt}\n${codeRef.current}`);
  }

  function handleSelectExample(example: { title: string; code: string }) {
    setActiveExample(example.title);
    loadCode(example.code);
  }

  function handleRenameDiagram(index: number, name: string) {
    const next = renameDiagramInCode(codeRef.current, index, name);
    if (next) loadCode(next);
  }

  return (
    <div className="app">
      <Toolbar status={ready ? (rendering ? "Rendering…" : "Ready") : status} onShare={handleShare} shared={shared} />
      <ExamplesGallery activeExample={activeExample} onSelect={handleSelectExample} />
      <main className="main" ref={mainRef}>
        <NodeSearch catalog={catalog} onInsert={insertImport} width={sidebarWidth} />
        <DragHandle
          containerRef={mainRef}
          onChange={handleSidebarChange}
          ariaLabel="Resize node list sidebar"
          valueFromPointer={(clientX, rect) => clampSidebarWidth(clientX - rect.left)}
          resetValue={DEFAULT_SIDEBAR_WIDTH}
        />
        <div className="split-container" ref={splitContainerRef}>
          <div className="editor-column" style={{ flexBasis: `${splitRatio}%` }}>
            <EditorPane
              key={catalog ? "with-catalog" : "bare"}
              initialCode={codeRef.current}
              extensions={editorExtensions}
              lineCount={lineCount}
              onChange={handleEditorChange}
              onReplaceRef={(fn) => (replaceCodeRef.current = fn)}
              onRunNow={() => void execute(codeRef.current)}
              onShare={handleShare}
            />
            <ErrorPanel error={catalogError} testId="catalog-error-panel" />
            <ErrorPanel error={error} />
          </div>
          <DragHandle
            containerRef={splitContainerRef}
            onChange={handleSplitChange}
            ariaLabel="Resize editor and preview panes"
            valueFromPointer={(clientX, rect) =>
              rect.width === 0 ? DEFAULT_RATIO : clampRatio(((clientX - rect.left) / rect.width) * 100)
            }
            resetValue={DEFAULT_RATIO}
          />
          <PreviewPane svgs={svgs} loading={rendering} renderMs={renderMs} onRenameDiagram={handleRenameDiagram}>
            <ExportBar svgs={svgs} />
          </PreviewPane>
        </div>
      </main>
    </div>
  );
}
