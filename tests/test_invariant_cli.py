import pytest
import tempfile
import os
import subprocess
import sys


@pytest.mark.parametrize("payload,should_be_blocked", [
    # Exact exploit case: arbitrary code execution via exec
    ("import os; os.system('echo PWNED > /tmp/pwned_test_marker')", True),
    # Boundary case: file read attempt
    ("print(open('/etc/passwd').read())", True),
    # Another dangerous case: subprocess spawn
    ("import subprocess; subprocess.run(['id'])", True),
    # Valid diagram code (should work if sandboxed properly)
    ("x = 1 + 1", False),
])
def test_cli_exec_security_boundary(payload, should_be_blocked):
    """Invariant: CLI should not execute arbitrary Python code without sandboxing"""
    marker_file = "/tmp/pwned_test_marker"
    if os.path.exists(marker_file):
        os.remove(marker_file)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(payload)
        temp_path = f.name
    
    try:
        # Run the CLI with the malicious file
        result = subprocess.run(
            [sys.executable, '-m', 'diagrams.cli', temp_path],
            capture_output=True,
            timeout=5,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # If payload was dangerous, check if it executed
        if should_be_blocked and "os.system" in payload:
            # The marker file should NOT exist if exec was sandboxed
            assert not os.path.exists(marker_file), \
                "Arbitrary code execution succeeded - security boundary violated"
    finally:
        os.unlink(temp_path)
        if os.path.exists(marker_file):
            os.remove(marker_file)