# Copyright (c) 2012-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2012 FELD Boris <lothiraldan@gmail.com>
# Copyright (c) 2013-2017 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2013-2014 Google, Inc.
# Copyright (c) 2013 buck@yelp.com <buck@yelp.com>
# Copyright (c) 2014 LCD 47 <lcd047@gmail.com>
# Copyright (c) 2014 Brett Cannon <brett@python.org>
# Copyright (c) 2014 Ricardo Gemignani <ricardo.gemignani@gmail.com>
# Copyright (c) 2014 Arun Persaud <arun@nubati.net>
# Copyright (c) 2015 Pavel Roskin <proski@gnu.org>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2016 Derek Gustafson <degustaf@gmail.com>
# Copyright (c) 2016 Roy Williams <roy.williams.iii@gmail.com>
# Copyright (c) 2016 xmo-odoo <xmo-odoo@users.noreply.github.com>
# Copyright (c) 2017 Bryce Guinta <bryce.paul.guinta@gmail.com>
# Copyright (c) 2018 ssolanki <sushobhitsolanki@gmail.com>
# Copyright (c) 2018 Sushobhit <31987769+sushobhit27@users.noreply.github.com>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""functional/non regression tests for pylint"""
import collections
import contextlib
import functools
import sys
import tempfile
import tokenize
from glob import glob
from io import StringIO
from os import close, getcwd, linesep, remove, sep, write
from os.path import abspath, basename, dirname, join, splitext

import astroid

from pylint import checkers
from pylint.interfaces import IReporter
from pylint.lint import PyLinter
from pylint.reporters import BaseReporter
from pylint.utils import ASTWalker

# Utils

SYS_VERS_STR = "%d%d%d" % sys.version_info[:3]
TITLE_UNDERLINES = ["", "=", "-", "."]
PREFIX = abspath(dirname(__file__))


def _get_tests_info(input_dir, msg_dir, prefix, suffix):
    """get python input examples and output messages

    We use following conventions for input files and messages:
    for different inputs:
        test for python  >= x.y    ->  input   =  <name>_pyxy.py
        test for python  <  x.y    ->  input   =  <name>_py_xy.py
    for one input and different messages:
        message for python >=  x.y ->  message =  <name>_pyxy.txt
        lower versions             ->  message with highest num
    """
    result = []
    for fname in glob(join(input_dir, prefix + "*" + suffix)):
        infile = basename(fname)
        fbase = splitext(infile)[0]
        # filter input files :
        pyrestr = fbase.rsplit("_py", 1)[-1]  # like _26 or 26
        if pyrestr.isdigit():  # '24', '25'...
            if SYS_VERS_STR < pyrestr:
                continue
        if pyrestr.startswith("_") and pyrestr[1:].isdigit():
            # skip test for higher python versions
            if SYS_VERS_STR >= pyrestr[1:]:
                continue
        messages = glob(join(msg_dir, fbase + "*.txt"))
        # the last one will be without ext, i.e. for all or upper versions:
        if messages:
            for outfile in sorted(messages, reverse=True):
                py_rest = outfile.rsplit("_py", 1)[-1][:-4]
                if py_rest.isdigit() and SYS_VERS_STR >= py_rest:
                    break
        else:
            # This will provide an error message indicating the missing filename.
            outfile = join(msg_dir, fbase + ".txt")
        result.append((infile, outfile))
    return result


class TestReporter(BaseReporter):
    """reporter storing plain text messages"""

    __implements__ = IReporter

    def __init__(self):  # pylint: disable=super-init-not-called

        self.message_ids = {}
        self.reset()
        self.path_strip_prefix = getcwd() + sep

    def reset(self):
        self.out = StringIO()
        self.messages = []

    def handle_message(self, msg):
        """manage message of different type and in the context of path """
        obj = msg.obj
        line = msg.line
        msg_id = msg.msg_id
        msg = msg.msg
        self.message_ids[msg_id] = 1
        if obj:
            obj = ":%s" % obj
        sigle = msg_id[0]
        if linesep != "\n":
            # 2to3 writes os.linesep instead of using
            # the previosly used line separators
            msg = msg.replace("\r\n", "\n")
        self.messages.append("%s:%3s%s: %s" % (sigle, line, obj, msg))

    def finalize(self):
        self.messages.sort()
        for msg in self.messages:
            print(msg, file=self.out)
        result = self.out.getvalue()
        self.reset()
        return result

    # pylint: disable=unused-argument
    def on_set_current_module(self, module, filepath):
        pass

    # pylint: enable=unused-argument

    def display_reports(self, layout):
        """ignore layouts"""

    _display = None


class MinimalTestReporter(BaseReporter):
    def handle_message(self, msg):
        self.messages.append(msg)

    def on_set_current_module(self, module, filepath):
        self.messages = []

    _display = None


class Message(
    collections.namedtuple("Message", ["msg_id", "line", "node", "args", "confidence"])
):
    def __new__(cls, msg_id, line=None, node=None, args=None, confidence=None):
        return tuple.__new__(cls, (msg_id, line, node, args, confidence))

    def __eq__(self, other):
        if isinstance(other, Message):
            if self.confidence and other.confidence:
                return super(Message, self).__eq__(other)
            return self[:-1] == other[:-1]
        return NotImplemented  # pragma: no cover

    __hash__ = None


class UnittestLinter:
    """A fake linter class to capture checker messages."""

    # pylint: disable=unused-argument, no-self-use

    def __init__(self):
        self._messages = []
        self.stats = {}

    def release_messages(self):
        try:
            return self._messages
        finally:
            self._messages = []

    def add_message(
        self, msg_id, line=None, node=None, args=None, confidence=None, col_offset=None
    ):
        # Do not test col_offset for now since changing Message breaks everything
        self._messages.append(Message(msg_id, line, node, args, confidence))

    def is_message_enabled(self, *unused_args, **unused_kwargs):
        return True

    def add_stats(self, **kwargs):
        for name, value in kwargs.items():
            self.stats[name] = value
        return self.stats

    @property
    def options_providers(self):
        return linter.options_providers


def set_config(**kwargs):
    """Decorator for setting config values on a checker."""

    def _wrapper(fun):
        @functools.wraps(fun)
        def _forward(self):
            for key, value in kwargs.items():
                setattr(self.checker.config, key, value)
            if isinstance(self, CheckerTestCase):
                # reopen checker in case, it may be interested in configuration change
                self.checker.open()
            fun(self)

        return _forward

    return _wrapper


class CheckerTestCase:
    """A base testcase class for unit testing individual checker classes."""

    CHECKER_CLASS = None
    CONFIG = {}

    def setup_method(self):
        self.linter = UnittestLinter()
        self.checker = self.CHECKER_CLASS(self.linter)  # pylint: disable=not-callable
        for key, value in self.CONFIG.items():
            setattr(self.checker.config, key, value)
        self.checker.open()

    @contextlib.contextmanager
    def assertNoMessages(self):
        """Assert that no messages are added by the given method."""
        with self.assertAddsMessages():
            yield

    @contextlib.contextmanager
    def assertAddsMessages(self, *messages):
        """Assert that exactly the given method adds the given messages.

        The list of messages must exactly match *all* the messages added by the
        method. Additionally, we check to see whether the args in each message can
        actually be substituted into the message string.
        """
        yield
        got = self.linter.release_messages()
        msg = "Expected messages did not match actual.\n" "Expected:\n%s\nGot:\n%s" % (
            "\n".join(repr(m) for m in messages),
            "\n".join(repr(m) for m in got),
        )
        assert list(messages) == got, msg

    def walk(self, node):
        """recursive walk on the given node"""
        walker = ASTWalker(linter)
        walker.add_checker(self.checker)
        walker.walk(node)


# Init
test_reporter = TestReporter()
linter = PyLinter()
linter.set_reporter(test_reporter)
linter.config.persistent = 0
checkers.initialize(linter)


def _tokenize_str(code):
    return list(tokenize.generate_tokens(StringIO(code).readline))


@contextlib.contextmanager
def _create_tempfile(content=None):
    """Create a new temporary file.

    If *content* parameter is given, then it will be written
    in the temporary file, before passing it back.
    This is a context manager and should be used with a *with* statement.
    """
    # Can't use tempfile.NamedTemporaryFile here
    # because on Windows the file must be closed before writing to it,
    # see http://bugs.python.org/issue14243
    file_handle, tmp = tempfile.mkstemp()
    if content:
        # erff
        write(file_handle, bytes(content, "ascii"))
    try:
        yield tmp
    finally:
        close(file_handle)
        remove(tmp)


@contextlib.contextmanager
def _create_file_backed_module(code):
    """Create an astroid module for the given code, backed by a real file."""
    with _create_tempfile() as temp:
        module = astroid.parse(code)
        module.file = temp
        yield module
