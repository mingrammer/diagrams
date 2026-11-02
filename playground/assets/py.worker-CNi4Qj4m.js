(function(){"use strict";var s=`"""Runs inside Pyodide. Patches diagrams so that no dot binary or filesystem
writes are needed: Diagram.render only captures DOT source, and
Diagram.__exit__ skips the os.remove of the .gv file."""

import io
import json
import sys
import traceback

_json_dumps = json.dumps  # captured before user code can monkeypatch json


def _install_patches(dots, state):
    import diagrams

    def patched_render(self):
        # Dedup a diagram rendered twice back-to-back (an explicit d.render()
        # immediately followed by __exit__) by comparing object identity to
        # the last-rendered diagram. \`state["last"]\` keeps that object alive,
        # so \`is\` stays reliable — unlike id(self), which CPython can reuse
        # once the previous diagram is garbage-collected, silently
        # overwriting an earlier capture.
        if state["last"] is self:
            dots[-1] = {"name": self.name, "source": self.dot.source}
            return
        state["last"] = self
        dots.append({"name": self.name, "source": self.dot.source})

    def patched_exit(self, exc_type, exc_value, tb):
        if exc_type is None:
            patched_render(self)
        diagrams.setdiagram(None)

    diagrams.Diagram.render = patched_render
    diagrams.Diagram.__exit__ = patched_exit


def _format_user_traceback(exc):
    # Drop the first frame (our exec call below) so the trace starts at
    # the user's <playground> code.
    tb = exc.__traceback__
    if tb is not None:
        tb = tb.tb_next
    return "".join(traceback.format_exception(type(exc), exc, tb))


def run_user_code(code):
    dots = []
    state = {"last": None}
    _install_patches(dots, state)
    stdout = io.StringIO()
    original_stdout, error = sys.stdout, None
    sys.stdout = stdout
    try:
        exec(compile(code, "<playground>", "exec"), {"__name__": "__main__"})
    except BaseException as exc:  # noqa: BLE001 - report everything to the UI
        error = _format_user_traceback(exc)
    finally:
        sys.stdout = original_stdout
    payload = {"dots": dots, "stdout": stdout.getvalue(), "error": error}
    try:
        return _json_dumps(payload)
    except Exception as exc:  # json machinery sabotaged or payload non-serializable
        message = "Internal error serializing result: " + repr(exc)
        escaped = (
            message.replace("\\\\", "\\\\\\\\")
            .replace('"', '\\\\"')
            .replace("\\n", "\\\\n")
            .replace("\\r", "\\\\r")
            .replace("\\t", "\\\\t")
        )
        return '{"dots": [], "stdout": "", "error": "' + escaped + '"}'
`;const o="https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.mjs";let t=null;function n(r){self.postMessage(r)}async function i(r){n({type:"progress",stage:"pyodide"}),t=await(await import(o)).loadPyodide(),n({type:"progress",stage:"packages"}),await t.loadPackage("micropip"),await t.pyimport("micropip").install(["jinja2","graphviz",r]),t.runPython(s),n({type:"ready"})}self.onmessage=async r=>{const e=r.data;try{if(e.type==="init")await i(e.wheelUrl);else if(e.type==="run"){const a=t.globals.get("run_user_code")(e.code);n({type:"result",id:e.id,result:JSON.parse(a)})}}catch(a){n({type:e.type==="init"?"init-error":"run-error",id:e.id,error:String(a)})}}})();
