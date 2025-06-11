"""Python 3.8 compatibility and platform compatibility."""

import platform
import sys

if sys.version_info < (3, 9):  # pragma: no cover
    # pytype not supported
    import unittest.mock

    Literal = unittest.mock.MagicMock(name='Literal')
else:  # pragma: no cover
    from typing import Literal

    Literal = Literal  # CAVEAT: use None instead of Literal[None]


def get_startupinfo() -> None:
    """Return None for startupinfo argument of ``subprocess.Popen``."""
    return None


assert get_startupinfo() is None, 'get_startupinfo() defaults to a no-op'


if platform.system() == 'Windows':  # pragma: no cover
    import subprocess

    def get_startupinfo() -> subprocess.STARTUPINFO:  # pytype: disable=module-attr
        """Return subprocess.STARTUPINFO instance hiding the console window."""
        startupinfo = subprocess.STARTUPINFO()  # pytype: disable=module-attr
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # pytype: disable=module-attr
        startupinfo.wShowWindow = subprocess.SW_HIDE  # pytype: disable=module-attr
        return startupinfo
