"""Return the version number from running ``dot -V``."""

import logging
import re
import subprocess
import typing

from . import dot_command
from . import execute

VERSION_PATTERN = re.compile(r'''
                             graphviz[ ]
                             version[ ]
                             (\d+)\.(\d+)
                             (?:\.(\d+)
                               (?:
                                 ~dev\.\d{8}\.\d{4}
                                 |
                                 \.(\d+)
                               )?
                             )?
                             [ ]
                             ''', re.VERBOSE)


log = logging.getLogger(__name__)


def version() -> typing.Tuple[int, ...]:
    """Return the upstream version number tuple from ``stderr`` of ``dot -V``.

    Returns:
        Two, three, or four ``int`` version ``tuple``.

    Raises:
        graphviz.ExecutableNotFound: If the Graphviz executable is not found.
        graphviz.CalledProcessError: If the exit status is non-zero.
        RuntimeError: If the output cannot be parsed into a version number.

    Example:
        >>> doctest_mark_exe()
        >>> import graphviz
        >>> graphviz.version()  # doctest: +ELLIPSIS
        (...)

    Note:
        Ignores the ``~dev.<YYYYmmdd.HHMM>`` portion of development versions.

    See also:
        Upstream release version entry format:
        https://gitlab.com/graphviz/graphviz/-/blob/f94e91ba819cef51a4b9dcb2d76153684d06a913/gen_version.py#L17-20
    """
    cmd = [dot_command.DOT_BINARY, '-V']
    proc = execute.run_check(cmd,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             encoding='ascii')

    ma = VERSION_PATTERN.search(proc.stdout)
    if ma is None:
        raise RuntimeError(f'cannot parse {cmd!r} output: {proc.stdout!r}')

    return tuple(int(d) for d in ma.groups() if d is not None)
