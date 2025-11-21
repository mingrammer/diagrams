"""Run subprocesses with ``subprocess.run()`` and ``subprocess.Popen()``."""

import errno
import logging
import os
import subprocess
import sys
import typing

from .. import _compat

__all__ = ['run_check', 'ExecutableNotFound', 'CalledProcessError']


log = logging.getLogger(__name__)


BytesOrStrIterator = typing.Union[typing.Iterator[bytes],
                                  typing.Iterator[str]]


@typing.overload
def run_check(cmd: typing.Sequence[typing.Union[os.PathLike, str]], *,
              input_lines: typing.Optional[typing.Iterator[bytes]] = ...,
              encoding: None = ...,
              quiet: bool = ...,
              **kwargs) -> subprocess.CompletedProcess:
    """Accept bytes input_lines with default ``encoding=None```."""


@typing.overload
def run_check(cmd: typing.Sequence[typing.Union[os.PathLike, str]], *,
              input_lines: typing.Optional[typing.Iterator[str]] = ...,
              encoding: str,
              quiet: bool = ...,
              **kwargs) -> subprocess.CompletedProcess:
    """Accept string input_lines when given ``encoding``."""


@typing.overload
def run_check(cmd: typing.Sequence[typing.Union[os.PathLike, str]], *,
              input_lines: typing.Optional[BytesOrStrIterator] = ...,
              encoding: typing.Optional[str] = ...,
              capture_output: bool = ...,
              quiet: bool = ...,
              **kwargs) -> subprocess.CompletedProcess:
    """Accept bytes or string input_lines depending on ``encoding``."""


def run_check(cmd: typing.Sequence[typing.Union[os.PathLike, str]], *,
              input_lines: typing.Optional[BytesOrStrIterator] = None,
              encoding: typing.Optional[str] = None,
              quiet: bool = False,
              **kwargs) -> subprocess.CompletedProcess:
    """Run the command described by ``cmd``
        with ``check=True`` and return its completed process.

    Raises:
        CalledProcessError: if the returncode of the subprocess is non-zero.
    """
    log.debug('run %r', cmd)
    if not kwargs.pop('check', True):  # pragma: no cover
        raise NotImplementedError('check must be True or omited')

    if encoding is not None:
        kwargs['encoding'] = encoding

    kwargs.setdefault('startupinfo', _compat.get_startupinfo())

    try:
        if input_lines is not None:
            assert kwargs.get('input') is None
            assert iter(input_lines) is input_lines
            if kwargs.pop('capture_output'):
                kwargs['stdout'] = kwargs['stderr'] = subprocess.PIPE
            proc = _run_input_lines(cmd, input_lines, kwargs=kwargs)
        else:
            proc = subprocess.run(cmd, **kwargs)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise ExecutableNotFound(cmd) from e
        raise

    if not quiet and proc.stderr:
        _write_stderr(proc.stderr)

    try:
        proc.check_returncode()
    except subprocess.CalledProcessError as e:
        raise CalledProcessError(*e.args)

    return proc


def _run_input_lines(cmd, input_lines, *, kwargs):
    popen = subprocess.Popen(cmd, stdin=subprocess.PIPE, **kwargs)

    stdin_write = popen.stdin.write
    for line in input_lines:
        stdin_write(line)

    stdout, stderr = popen.communicate()
    return subprocess.CompletedProcess(popen.args, popen.returncode,
                                       stdout=stdout, stderr=stderr)


def _write_stderr(stderr) -> None:
    if isinstance(stderr, bytes):
        stderr_encoding = (getattr(sys.stderr, 'encoding', None)
                           or sys.getdefaultencoding())
        stderr = stderr.decode(stderr_encoding)

    sys.stderr.write(stderr)
    sys.stderr.flush()
    return None


class ExecutableNotFound(RuntimeError):
    """:exc:`RuntimeError` raised if the Graphviz executable is not found."""

    _msg = ('failed to execute {!r}, '
            'make sure the Graphviz executables are on your systems\' PATH')

    def __init__(self, args) -> None:
        super().__init__(self._msg.format(*args))


class CalledProcessError(subprocess.CalledProcessError):
    """:exc:`~subprocess.CalledProcessError` raised if a subprocess ``returncode`` is not ``0``."""  # noqa: E501

    def __str__(self) -> 'str':
        return f'{super().__str__()} [stderr: {self.stderr!r}]'
