"""Pipe DOT code objects through Graphviz ``dot``."""

import codecs
import logging
import typing

from . import _tools
from . import backend
from . import exceptions
from . import base
from . import encoding

__all__ = ['Pipe']


log = logging.getLogger(__name__)


class Pipe(encoding.Encoding, base.Base, backend.Pipe):
    """Pipe source lines through the Graphviz layout command."""

    @typing.overload
    def pipe(self,
             format: typing.Optional[str] = ...,
             renderer: typing.Optional[str] = ...,
             formatter: typing.Optional[str] = ...,
             neato_no_op: typing.Union[bool, int, None] = ...,
             quiet: bool = ..., *,
             engine: typing.Optional[str] = ...,
             encoding: None = ...) -> bytes:
        """Return bytes with default ``encoding=None``."""

    @typing.overload
    def pipe(self,
             format: typing.Optional[str] = ...,
             renderer: typing.Optional[str] = ...,
             formatter: typing.Optional[str] = ...,
             neato_no_op: typing.Union[bool, int, None] = ...,
             quiet: bool = ..., *,
             engine: typing.Optional[str] = ...,
             encoding: str) -> str:
        """Return string when given encoding."""

    @typing.overload
    def pipe(self,
             format: typing.Optional[str] = ...,
             renderer: typing.Optional[str] = ...,
             formatter: typing.Optional[str] = ...,
             neato_no_op: typing.Union[bool, int, None] = ...,
             quiet: bool = ..., *,
             engine: typing.Optional[str] = ...,
             encoding: typing.Optional[str]) -> typing.Union[bytes, str]:
        """Return bytes or string depending on encoding argument."""

    def pipe(self,
             format: typing.Optional[str] = None,
             renderer: typing.Optional[str] = None,
             formatter: typing.Optional[str] = None,
             neato_no_op: typing.Union[bool, int, None] = None,
             quiet: bool = False, *,
             engine: typing.Optional[str] = None,
             encoding: typing.Optional[str] = None) -> typing.Union[bytes, str]:
        """Return the source piped through the Graphviz layout command.

        Args:
            format: The output format used for rendering
                (``'pdf'``, ``'png'``, etc.).
            renderer: The output renderer used for rendering
                (``'cairo'``, ``'gd'``, ...).
            formatter: The output formatter used for rendering
                (``'cairo'``, ``'gd'``, ...).
            neato_no_op: Neato layout engine no-op flag.
            quiet (bool): Suppress ``stderr`` output
                from the layout subprocess.
            engine: Layout engine for rendering
                (``'dot'``, ``'neato'``, ...).
            encoding: Encoding for decoding the stdout.

        Returns:
            Bytes or if encoding is given decoded string
                (stdout of the layout command).

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
            >>> source = 'graph { spam }'
            >>> graphviz.Source(source, format='svg').pipe()[:14]
            b'<?xml version='
            >>> graphviz.Source(source, format='svg').pipe(encoding='ascii')[:14]
            '<?xml version='
            >>> graphviz.Source(source, format='svg').pipe(encoding='utf-8')[:14]
            '<?xml version='
        """
        return self._pipe_legacy(format,
                                 renderer=renderer,
                                 formatter=formatter,
                                 neato_no_op=neato_no_op,
                                 quiet=quiet,
                                 engine=engine,
                                 encoding=encoding)

    @_tools.deprecate_positional_args(supported_number=2)
    def _pipe_legacy(self,
                     format: typing.Optional[str] = None,
                     renderer: typing.Optional[str] = None,
                     formatter: typing.Optional[str] = None,
                     neato_no_op: typing.Union[bool, int, None] = None,
                     quiet: bool = False, *,
                     engine: typing.Optional[str] = None,
                     encoding: typing.Optional[str] = None) -> typing.Union[bytes, str]:
        return self._pipe_future(format,
                                 renderer=renderer,
                                 formatter=formatter,
                                 neato_no_op=neato_no_op,
                                 quiet=quiet,
                                 engine=engine,
                                 encoding=encoding)

    def _pipe_future(self, format: typing.Optional[str] = None, *,
                     renderer: typing.Optional[str] = None,
                     formatter: typing.Optional[str] = None,
                     neato_no_op: typing.Union[bool, int, None] = None,
                     quiet: bool = False,
                     engine: typing.Optional[str] = None,
                     encoding: typing.Optional[str] = None) -> typing.Union[bytes, str]:
        args, kwargs = self._get_pipe_parameters(engine=engine,
                                                 format=format,
                                                 renderer=renderer,
                                                 formatter=formatter,
                                                 neato_no_op=neato_no_op,
                                                 quiet=quiet,
                                                 verify=True)

        args.append(iter(self))

        if encoding is not None:
            if codecs.lookup(encoding) is codecs.lookup(self.encoding):
                # common case: both stdin and stdout need the same encoding
                return self._pipe_lines_string(*args, encoding=encoding, **kwargs)
            try:
                raw = self._pipe_lines(*args, input_encoding=self.encoding, **kwargs)
            except exceptions.CalledProcessError as e:
                *args, output, stderr = e.args
                if output is not None:
                    output = output.decode(self.encoding)
                if stderr is not None:
                    stderr = stderr.decode(self.encoding)
                raise e.__class__(*args, output=output, stderr=stderr)
            else:
                return raw.decode(encoding)
        return self._pipe_lines(*args, input_encoding=self.encoding, **kwargs)
