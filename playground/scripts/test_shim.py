import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SHIM = REPO_ROOT / "playground" / "src" / "worker" / "shim.py"
sys.path.insert(0, str(REPO_ROOT))


# Fixture to restore json module after each test
@pytest.fixture(autouse=True)
def restore_json_module():
    import json.encoder as je

    original_dumps = json.dumps
    original_encode_basestring_ascii = je.encode_basestring_ascii
    original_encode_basestring = je.encode_basestring
    original_c_encode_basestring_ascii = je.c_encode_basestring_ascii
    original_c_make_encoder = je.c_make_encoder
    yield
    json.dumps = original_dumps
    je.encode_basestring_ascii = original_encode_basestring_ascii
    je.encode_basestring = original_encode_basestring
    je.c_encode_basestring_ascii = original_c_encode_basestring_ascii
    je.c_make_encoder = original_c_make_encoder


namespace = {}
exec(compile(SHIM.read_text(), str(SHIM), "exec"), namespace)
run_user_code = namespace["run_user_code"]

SAMPLE = """
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.network import ELB

with Diagram("Web Service", show=False):
    ELB("lb") >> EC2("web")
"""


def test_captures_dot_source():
    result = json.loads(run_user_code(SAMPLE))
    assert result["error"] is None
    assert len(result["dots"]) == 1
    assert result["dots"][0]["name"] == "Web Service"
    assert "elastic-load-balancing.png" in result["dots"][0]["source"]
    assert "digraph" in result["dots"][0]["source"]


def test_no_output_files_written(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    json.loads(run_user_code(SAMPLE))
    assert list(tmp_path.iterdir()) == []


def test_captures_multiple_diagrams():
    code = SAMPLE + '\nwith Diagram("Second", show=False):\n    EC2("solo")\n'
    result = json.loads(run_user_code(code))
    assert [d["name"] for d in result["dots"]] == ["Web Service", "Second"]


def test_explicit_render_call_not_duplicated():
    code = """
from diagrams import Diagram
from diagrams.aws.compute import EC2
with Diagram("D", show=False) as d:
    EC2("a")
    d.render()
"""
    result = json.loads(run_user_code(code))
    assert len(result["dots"]) == 1


def test_error_returns_clean_traceback():
    result = json.loads(run_user_code("from diagrams import Diagram\n1/0\n"))
    assert result["dots"] == []
    assert "ZeroDivisionError" in result["error"]
    assert "line 2" in result["error"]
    assert "shim.py" not in result["error"]


def test_stdout_captured():
    result = json.loads(run_user_code('print("hello")'))
    assert result["stdout"] == "hello\n"


def test_exception_inside_diagram_block_not_captured():
    code = """
from diagrams import Diagram
from diagrams.aws.compute import EC2
try:
    with Diagram("Broken", show=False):
        EC2("a")
        raise RuntimeError("boom")
except RuntimeError:
    pass
with Diagram("After", show=False):
    EC2("b")
"""
    result = json.loads(run_user_code(code))
    assert [d["name"] for d in result["dots"]] == ["After"]
    assert result["error"] is None


def test_json_sabotage_still_returns_json():
    code = "import json\njson.dumps = None\nprint('ok')"
    result = json.loads(run_user_code(code))
    assert result["error"] is None
    assert result["stdout"] == "ok\n"


def test_json_encoder_sabotage_still_returns_json():
    code = """
import json.encoder as je
def evil(*a, **k):
    raise RuntimeError("pwned")
je.encode_basestring_ascii = evil
je.encode_basestring = evil
je.c_encode_basestring_ascii = None
je.c_make_encoder = None
"""
    result = json.loads(run_user_code(code))
    assert result["dots"] == []
    assert "Internal error serializing result" in result["error"]
    assert "pwned" in result["error"]
