"""Pipe bytes, strings, or string iterators through Graphviz ``dot``."""

import typing

from .. import _tools

from . import dot_command
from . import execute

__all__ = ['pipe', 'pipe_string',
           'pipe_lines', 'pipe_lines_string']


@_tools.deprecate_positional_args(supported_number=3)
def pipe(engine: str, format: str, data: bytes,
         renderer: typing.Optional[str] = None,
         formatter: typing.Optional[str] = None,
         neato_no_op: typing.Union[bool, int, None] = None,
         quiet: bool = False) -> bytes:
    """Return ``data`` (``bytes``) piped through ``engine`` into ``format`` as ``bytes``.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        data: Binary (encoded) DOT source bytes to render.
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        neato_no_op: Neato layout engine no-op flag.
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        Binary (encoded) stdout of the layout command.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are unknown.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz ``dot`` executable
            is not found.
        graphviz.CalledProcessError: If the returncode (exit status)
            of the rendering ``dot`` subprocess is non-zero.

    Example:
        >>> doctest_mark_exe()
        >>> import graphviz
        >>> graphviz.pipe('dot', 'svg', b'graph { hello -- world }')[:14]
        b'<?xml version='

    Note:
        The layout command is started from the current directory.
    """
    cmd = dot_command.command(engine, format,
                              renderer=renderer,
                              formatter=formatter,
                              neato_no_op=neato_no_op)
    kwargs = {'input': data}

    proc = execute.run_check(cmd, capture_output=True, quiet=quiet, **kwargs)
    return proc.stdout


def pipe_string(engine: str, format: str, input_string: str, *,
                encoding: str,
                renderer: typing.Optional[str] = None,
                formatter: typing.Optional[str] = None,
                neato_no_op: typing.Union[bool, int, None] = None,
                quiet: bool = False) -> str:
    """Return ``input_string`` piped through ``engine`` into ``format`` as string.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        input_string: Binary (encoded) DOT source bytes to render.
        encoding: Encoding to en/decode subprocess stdin and stdout (required).
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        neato_no_op: Neato layout engine no-op flag.
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        Decoded stdout of the layout command.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are unknown.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz ``dot`` executable
            is not found.
        graphviz.CalledProcessError: If the returncode (exit status)
            of the rendering ``dot`` subprocess is non-zero.

    Example:
        >>> doctest_mark_exe()
        >>> import graphviz
        >>> graphviz.pipe_string('dot', 'svg', 'graph { spam }',
        ...                      encoding='ascii')[:14]
        '<?xml version='

    Note:
        The layout command is started from the current directory.
    """
    cmd = dot_command.command(engine, format,
                              renderer=renderer,
                              formatter=formatter,
                              neato_no_op=neato_no_op)
    kwargs = {'input': input_string, 'encoding': encoding}

    proc = execute.run_check(cmd, capture_output=True, quiet=quiet, **kwargs)
    return proc.stdout


def pipe_lines(engine: str, format: str, input_lines: typing.Iterator[str], *,
               input_encoding: str,
               renderer: typing.Optional[str] = None,
               formatter: typing.Optional[str] = None,
               neato_no_op: typing.Union[bool, int, None] = None,
               quiet: bool = False) -> bytes:
    r"""Return ``input_lines`` piped through ``engine`` into ``format`` as ``bytes``.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        input_lines: DOT source lines to render (including final newline).
        input_encoding: Encode input_lines for subprocess stdin (required).
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        neato_no_op: Neato layout engine no-op flag.
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        Binary stdout of the layout command.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are unknown.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz ``dot`` executable
            is not found.
        graphviz.CalledProcessError: If the returncode (exit status)
            of the rendering ``dot`` subprocess is non-zero.

    Example:
        >>> doctest_mark_exe()
        >>> import graphviz
        >>> graphviz.pipe_lines('dot', 'svg', iter(['graph { spam }\n']),
        ...                     input_encoding='ascii')[:14]
        b'<?xml version='

    Note:
        The layout command is started from the current directory.
    """
    cmd = dot_command.command(engine, format,
                              renderer=renderer,
                              formatter=formatter,
                              neato_no_op=neato_no_op)
    kwargs = {'input_lines': (line.encode(input_encoding) for line in input_lines)}

    proc = execute.run_check(cmd, capture_output=True, quiet=quiet, **kwargs)
    return proc.stdout


def pipe_lines_string(engine: str, format: str, input_lines: typing.Iterator[str], *,
                      encoding: str,
                      renderer: typing.Optional[str] = None,
                      formatter: typing.Optional[str] = None,
                      neato_no_op: typing.Union[bool, int, None] = None,
                      quiet: bool = False) -> str:
    r"""Return ``input_lines`` piped through ``engine`` into ``format`` as string.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        input_lines: DOT source lines to render (including final newline).
        encoding: Encoding to en/decode subprocess stdin and stdout (required).
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        neato_no_op: Neato layout engine no-op flag.
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        Decoded stdout of the layout command.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are unknown.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz ``dot`` executable
            is not found.
        graphviz.CalledProcessError: If the returncode (exit status)
            of the rendering ``dot`` subprocess is non-zero.

    Example:
        >>> doctest_mark_exe()
        >>> import graphviz
        >>> graphviz.pipe_lines_string('dot', 'svg', iter(['graph { spam }\n']),
        ...                            encoding='ascii')[:14]
        '<?xml version='

    Note:
        The layout command is started from the current directory.
    """
    cmd = dot_command.command(engine, format,
                              renderer=renderer,
                              formatter=formatter,
                              neato_no_op=neato_no_op)
    kwargs = {'input_lines': input_lines, 'encoding': encoding}

    proc = execute.run_check(cmd, capture_output=True, quiet=quiet, **kwargs)
    return proc.stdout
