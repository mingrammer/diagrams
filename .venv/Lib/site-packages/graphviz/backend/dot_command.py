"""Check and assemble commands for running Graphviz ``dot``."""

import os
import pathlib
import typing

from .. import exceptions
from .. import parameters

__all__ = ['DOT_BINARY', 'command']

DOT_BINARY = pathlib.Path('dot')


def command(engine: str, format_: str, *,
            renderer: typing.Optional[str] = None,
            formatter: typing.Optional[str] = None,
            neato_no_op: typing.Union[bool, int, None] = None
            ) -> typing.List[typing.Union[os.PathLike, str]]:
    """Return ``subprocess.Popen`` argument list for rendering.

    See also:
        Upstream documentation:
        - https://www.graphviz.org/doc/info/command.html#-K
        - https://www.graphviz.org/doc/info/command.html#-T
        - https://www.graphviz.org/doc/info/command.html#-n
    """
    if formatter is not None and renderer is None:
        raise exceptions.RequiredArgumentError('formatter given without renderer')

    parameters.verify_engine(engine, required=True)
    parameters.verify_format(format_, required=True)
    parameters.verify_renderer(renderer, required=False)
    parameters.verify_formatter(formatter, required=False)

    output_format = [f for f in (format_, renderer, formatter) if f is not None]
    output_format_flag = ':'.join(output_format)

    cmd = [DOT_BINARY, f'-K{engine}', f'-T{output_format_flag}']

    if neato_no_op:
        cmd.append(f'-n{neato_no_op:d}')

    return cmd
