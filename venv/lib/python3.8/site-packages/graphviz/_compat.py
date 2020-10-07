# _compat.py - Python 2/3 compatibility

import os
import sys
import operator
import subprocess

PY2 = (sys.version_info.major == 2)


if PY2:
    string_classes = (str, unicode)  # needed individually for sublassing
    text_type = unicode

    iteritems = operator.methodcaller('iteritems')

    def makedirs(name, mode=0o777, exist_ok=False):
        try:
            os.makedirs(name, mode)
        except OSError:
            if not exist_ok or not os.path.isdir(name):
                raise

    def stderr_write_bytes(data, flush=False):
        """Write data str to sys.stderr (flush if requested)."""
        sys.stderr.write(data)
        if flush:
            sys.stderr.flush()

    def Popen_stderr_devnull(*args, **kwargs):  # noqa: N802
        with open(os.devnull, 'w') as f:
            return subprocess.Popen(*args, stderr=f, **kwargs)

    class CalledProcessError(subprocess.CalledProcessError):

        def __init__(self, returncode, cmd, output=None, stderr=None):
            super(CalledProcessError, self).__init__(returncode, cmd, output)
            self.stderr = stderr

        @property  # pragma: no cover
        def stdout(self):
            return self.output

        @stdout.setter  # pragma: no cover
        def stdout(self, value):
            self.output = value


else:
    string_classes = (str,)
    text_type = str

    def iteritems(d):
        return iter(d.items())

    def makedirs(name, mode=0o777, exist_ok=False):  # allow os.makedirs mocking
        return os.makedirs(name, mode, exist_ok=exist_ok)

    def stderr_write_bytes(data, flush=False):
        """Encode data str and write to sys.stderr (flush if requested)."""
        encoding = sys.stderr.encoding or sys.getdefaultencoding()
        sys.stderr.write(data.decode(encoding))
        if flush:
            sys.stderr.flush()

    def Popen_stderr_devnull(*args, **kwargs):  # noqa: N802
        return subprocess.Popen(*args, stderr=subprocess.DEVNULL, **kwargs)

    CalledProcessError = subprocess.CalledProcessError
