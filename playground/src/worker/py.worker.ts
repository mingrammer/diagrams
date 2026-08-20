/// <reference lib="webworker" />
import shimSource from "./shim.py?raw";

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.mjs";

// pyodide has no bundled types; the surface we use is tiny.
interface Pyodide {
  loadPackage(name: string): Promise<void>;
  pyimport(name: string): { install(reqs: string[]): Promise<void> };
  runPython(code: string): void;
  globals: { get(name: string): (arg: string) => string };
}

let pyodide: Pyodide | null = null;

function post(msg: unknown) {
  (self as unknown as Worker).postMessage(msg);
}

async function init(wheelUrl: string) {
  post({ type: "progress", stage: "pyodide" });
  const mod = await import(/* @vite-ignore */ PYODIDE_URL);
  pyodide = (await mod.loadPyodide()) as Pyodide;
  post({ type: "progress", stage: "packages" });
  await pyodide.loadPackage("micropip");
  const micropip = pyodide.pyimport("micropip");
  await micropip.install(["jinja2", "graphviz", wheelUrl]);
  pyodide.runPython(shimSource);
  post({ type: "ready" });
}

self.onmessage = async (e: MessageEvent) => {
  const msg = e.data;
  try {
    if (msg.type === "init") {
      await init(msg.wheelUrl);
    } else if (msg.type === "run") {
      const json = pyodide!.globals.get("run_user_code")(msg.code);
      post({ type: "result", id: msg.id, result: JSON.parse(json) });
    }
  } catch (err) {
    post({
      type: msg.type === "init" ? "init-error" : "run-error",
      id: msg.id,
      error: String(err),
    });
  }
};
