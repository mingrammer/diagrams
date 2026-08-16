"""Pipe DOT source code through ``unflatten``."""

import pathlib
import typing

from ..encoding import DEFAULT_ENCODING
from .. import _tools
from .. import exceptions

from . import execute

__all__ = ['UNFLATTEN_BINARY', 'unflatten']

UNFLATTEN_BINARY = pathlib.Path('unflatten')


@_tools.deprecate_positional_args(supported_number=1)
def unflatten(source: str,
              stagger: typing.Optional[int] = None,
              fanout: bool = False,
              chain: typing.Optional[int] = None,
              encoding: str = DEFAULT_ENCODING) -> str:
    """Return DOT ``source`` piped through ``unflatten`` preprocessor as string.

    Args:
        source: DOT source to process
            (improve layout aspect ratio).
        stagger: Stagger the minimum length of leaf edges
            between 1 and this small integer.
        fanout: Fanout nodes with indegree = outdegree = 1
            when staggering (requires ``stagger``).
        chain: Form disconnected nodes into chains of up to this many nodes.
        encoding: Encoding to encode unflatten stdin and decode its stdout.

    Returns:
        Decoded stdout of the Graphviz unflatten command.

    Raises:
        graphviz.RequiredArgumentError: If ``fanout`` is given
            but no ``stagger``.
        graphviz.ExecutableNotFound: If the Graphviz 'unflatten' executable
            is not found.
        graphviz.CalledProcessError: If the returncode (exit status)
            of the unflattening 'unflatten' subprocess is non-zero.

    See also:
        Upstream documentation:
        https://www.graphviz.org/pdf/unflatten.1.pdf
    """
    if fanout and stagger is None:
        raise exceptions.RequiredArgumentError('fanout given without stagger')

    cmd = [UNFLATTEN_BINARY]
    if stagger is not None:
        cmd += ['-l', str(stagger)]
    if fanout:
        cmd.append('-f')
    if chain is not None:
        cmd += ['-c', str(chain)]

    proc = execute.run_check(cmd, input=source, encoding=encoding,
                             capture_output=True)
    return proc.stdout
