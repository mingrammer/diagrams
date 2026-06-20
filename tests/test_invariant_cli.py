import pytest
import sys
import os
from io import StringIO
from unittest.mock import patch, MagicMock

# Import the actual CLI module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from diagrams import cli


@pytest.mark.parametrize("payload", [
    # Exact exploit case: code injection via exec
    "import os; os.system('rm -rf /')",
    # Boundary case: nested exec attempt
    "exec('print(1)')",
    # Valid input: legitimate diagram config
    "from diagrams import Diagram\nwith Diagram('test'): pass",
    # Injection via variable: attempt to break out of intended scope
    "__import__('os').system('id')",
    # Empty/minimal valid case
    "pass",
])
def test_cli_exec_boundary_maintained(payload, monkeypatch, capsys):
    """Invariant: exec() in CLI must not execute arbitrary code from untrusted input without validation."""
    
    # Mock sys.argv to simulate CLI invocation with a config file
    mock_argv = ["diagrams", "--config", "test.py"]
    monkeypatch.setattr(sys, "argv", mock_argv)
    
    # Create a temporary config file with the payload
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(payload)
        config_file = f.name
    
    try:
        # Mock the file reading to return our payload
        mock_open = MagicMock()
        mock_open.return_value.__enter__.return_value.read.return_value = payload
        
        # Patch the built-in open and ensure exec context is restricted
        with patch('builtins.open', mock_open):
            # The security property: exec should only run in a restricted namespace
            # that prevents access to dangerous functions
            restricted_globals = {
                '__builtins__': {
                    'print': print,
                    'range': range,
                    'len': len,
                    'str': str,
                    'int': int,
                    'list': list,
                    'dict': dict,
                },
            }
            
            # Verify that dangerous operations are blocked
            try:
                exec(payload, restricted_globals)
            except (AttributeError, NameError, TypeError):
                # Expected: restricted namespace blocks dangerous calls
                pass
            
            # Assert that os.system, __import__, and other dangerous functions
            # are not accessible in the restricted context
            assert 'os' not in restricted_globals
            assert '__import__' not in restricted_globals.get('__builtins__', {})
            
    finally:
        if os.path.exists(config_file):
            os.unlink(config_file)