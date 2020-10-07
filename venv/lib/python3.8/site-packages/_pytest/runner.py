""" basic collect and runtest protocol implementations """
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bdb
import os
import sys
from time import time

import six

from .reports import CollectErrorRepr
from .reports import CollectReport
from .reports import TestReport
from _pytest._code.code import ExceptionInfo
from _pytest.outcomes import skip
from _pytest.outcomes import Skipped
from _pytest.outcomes import TEST_OUTCOME

#
# pytest plugin hooks


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group.addoption(
        "--durations",
        action="store",
        type=int,
        default=None,
        metavar="N",
        help="show N slowest setup/test durations (N=0 for all).",
    ),


def pytest_terminal_summary(terminalreporter):
    durations = terminalreporter.config.option.durations
    verbose = terminalreporter.config.getvalue("verbose")
    if durations is None:
        return
    tr = terminalreporter
    dlist = []
    for replist in tr.stats.values():
        for rep in replist:
            if hasattr(rep, "duration"):
                dlist.append(rep)
    if not dlist:
        return
    dlist.sort(key=lambda x: x.duration)
    dlist.reverse()
    if not durations:
        tr.write_sep("=", "slowest test durations")
    else:
        tr.write_sep("=", "slowest %s test durations" % durations)
        dlist = dlist[:durations]

    for rep in dlist:
        if verbose < 2 and rep.duration < 0.005:
            tr.write_line("")
            tr.write_line("(0.00 durations hidden.  Use -vv to show these durations.)")
            break
        nodeid = rep.nodeid.replace("::()::", "::")
        tr.write_line("%02.2fs %-8s %s" % (rep.duration, rep.when, nodeid))


def pytest_sessionstart(session):
    session._setupstate = SetupState()


def pytest_sessionfinish(session):
    session._setupstate.teardown_all()


def pytest_runtest_protocol(item, nextitem):
    item.ihook.pytest_runtest_logstart(nodeid=item.nodeid, location=item.location)
    runtestprotocol(item, nextitem=nextitem)
    item.ihook.pytest_runtest_logfinish(nodeid=item.nodeid, location=item.location)
    return True


def runtestprotocol(item, log=True, nextitem=None):
    hasrequest = hasattr(item, "_request")
    if hasrequest and not item._request:
        item._initrequest()
    rep = call_and_report(item, "setup", log)
    reports = [rep]
    if rep.passed:
        if item.config.option.setupshow:
            show_test_item(item)
        if not item.config.option.setuponly:
            reports.append(call_and_report(item, "call", log))
    reports.append(call_and_report(item, "teardown", log, nextitem=nextitem))
    # after all teardown hooks have been called
    # want funcargs and request info to go away
    if hasrequest:
        item._request = False
        item.funcargs = None
    return reports


def show_test_item(item):
    """Show test function, parameters and the fixtures of the test item."""
    tw = item.config.get_terminal_writer()
    tw.line()
    tw.write(" " * 8)
    tw.write(item._nodeid)
    used_fixtures = sorted(item._fixtureinfo.name2fixturedefs.keys())
    if used_fixtures:
        tw.write(" (fixtures used: {})".format(", ".join(used_fixtures)))


def pytest_runtest_setup(item):
    _update_current_test_var(item, "setup")
    item.session._setupstate.prepare(item)


def pytest_runtest_call(item):
    _update_current_test_var(item, "call")
    sys.last_type, sys.last_value, sys.last_traceback = (None, None, None)
    try:
        item.runtest()
    except Exception:
        # Store trace info to allow postmortem debugging
        type, value, tb = sys.exc_info()
        tb = tb.tb_next  # Skip *this* frame
        sys.last_type = type
        sys.last_value = value
        sys.last_traceback = tb
        del type, value, tb  # Get rid of these in this frame
        raise


def pytest_runtest_teardown(item, nextitem):
    _update_current_test_var(item, "teardown")
    item.session._setupstate.teardown_exact(item, nextitem)
    _update_current_test_var(item, None)


def _update_current_test_var(item, when):
    """
    Update PYTEST_CURRENT_TEST to reflect the current item and stage.

    If ``when`` is None, delete PYTEST_CURRENT_TEST from the environment.
    """
    var_name = "PYTEST_CURRENT_TEST"
    if when:
        value = "{} ({})".format(item.nodeid, when)
        # don't allow null bytes on environment variables (see #2644, #2957)
        value = value.replace("\x00", "(null)")
        os.environ[var_name] = value
    else:
        os.environ.pop(var_name)


def pytest_report_teststatus(report):
    if report.when in ("setup", "teardown"):
        if report.failed:
            #      category, shortletter, verbose-word
            return "error", "E", "ERROR"
        elif report.skipped:
            return "skipped", "s", "SKIPPED"
        else:
            return "", "", ""


#
# Implementation


def call_and_report(item, when, log=True, **kwds):
    call = call_runtest_hook(item, when, **kwds)
    hook = item.ihook
    report = hook.pytest_runtest_makereport(item=item, call=call)
    if log:
        hook.pytest_runtest_logreport(report=report)
    if check_interactive_exception(call, report):
        hook.pytest_exception_interact(node=item, call=call, report=report)
    return report


def check_interactive_exception(call, report):
    return call.excinfo and not (
        hasattr(report, "wasxfail")
        or call.excinfo.errisinstance(skip.Exception)
        or call.excinfo.errisinstance(bdb.BdbQuit)
    )


def call_runtest_hook(item, when, **kwds):
    hookname = "pytest_runtest_" + when
    ihook = getattr(item.ihook, hookname)
    return CallInfo(
        lambda: ihook(item=item, **kwds),
        when=when,
        treat_keyboard_interrupt_as_exception=item.config.getvalue("usepdb"),
    )


class CallInfo(object):
    """ Result/Exception info a function invocation. """

    #: None or ExceptionInfo object.
    excinfo = None

    def __init__(self, func, when, treat_keyboard_interrupt_as_exception=False):
        #: context of invocation: one of "setup", "call",
        #: "teardown", "memocollect"
        self.when = when
        self.start = time()
        try:
            self.result = func()
        except KeyboardInterrupt:
            if treat_keyboard_interrupt_as_exception:
                self.excinfo = ExceptionInfo()
            else:
                self.stop = time()
                raise
        except:  # noqa
            self.excinfo = ExceptionInfo()
        self.stop = time()

    def __repr__(self):
        if self.excinfo:
            status = "exception: %s" % str(self.excinfo.value)
        else:
            status = "result: %r" % (self.result,)
        return "<CallInfo when=%r %s>" % (self.when, status)


def pytest_runtest_makereport(item, call):
    when = call.when
    duration = call.stop - call.start
    keywords = {x: 1 for x in item.keywords}
    excinfo = call.excinfo
    sections = []
    if not call.excinfo:
        outcome = "passed"
        longrepr = None
    else:
        if not isinstance(excinfo, ExceptionInfo):
            outcome = "failed"
            longrepr = excinfo
        elif excinfo.errisinstance(skip.Exception):
            outcome = "skipped"
            r = excinfo._getreprcrash()
            longrepr = (str(r.path), r.lineno, r.message)
        else:
            outcome = "failed"
            if call.when == "call":
                longrepr = item.repr_failure(excinfo)
            else:  # exception in setup or teardown
                longrepr = item._repr_failure_py(
                    excinfo, style=item.config.option.tbstyle
                )
    for rwhen, key, content in item._report_sections:
        sections.append(("Captured %s %s" % (key, rwhen), content))
    return TestReport(
        item.nodeid,
        item.location,
        keywords,
        outcome,
        longrepr,
        when,
        sections,
        duration,
        user_properties=item.user_properties,
    )


def pytest_make_collect_report(collector):
    call = CallInfo(lambda: list(collector.collect()), "collect")
    longrepr = None
    if not call.excinfo:
        outcome = "passed"
    else:
        from _pytest import nose

        skip_exceptions = (Skipped,) + nose.get_skip_exceptions()
        if call.excinfo.errisinstance(skip_exceptions):
            outcome = "skipped"
            r = collector._repr_failure_py(call.excinfo, "line").reprcrash
            longrepr = (str(r.path), r.lineno, r.message)
        else:
            outcome = "failed"
            errorinfo = collector.repr_failure(call.excinfo)
            if not hasattr(errorinfo, "toterminal"):
                errorinfo = CollectErrorRepr(errorinfo)
            longrepr = errorinfo
    rep = CollectReport(
        collector.nodeid, outcome, longrepr, getattr(call, "result", None)
    )
    rep.call = call  # see collect_one_node
    return rep


class SetupState(object):
    """ shared state for setting up/tearing down test items or collectors. """

    def __init__(self):
        self.stack = []
        self._finalizers = {}

    def addfinalizer(self, finalizer, colitem):
        """ attach a finalizer to the given colitem.
        if colitem is None, this will add a finalizer that
        is called at the end of teardown_all().
        """
        assert colitem and not isinstance(colitem, tuple)
        assert callable(finalizer)
        # assert colitem in self.stack  # some unit tests don't setup stack :/
        self._finalizers.setdefault(colitem, []).append(finalizer)

    def _pop_and_teardown(self):
        colitem = self.stack.pop()
        self._teardown_with_finalization(colitem)

    def _callfinalizers(self, colitem):
        finalizers = self._finalizers.pop(colitem, None)
        exc = None
        while finalizers:
            fin = finalizers.pop()
            try:
                fin()
            except TEST_OUTCOME:
                # XXX Only first exception will be seen by user,
                #     ideally all should be reported.
                if exc is None:
                    exc = sys.exc_info()
        if exc:
            six.reraise(*exc)

    def _teardown_with_finalization(self, colitem):
        self._callfinalizers(colitem)
        if hasattr(colitem, "teardown"):
            colitem.teardown()
        for colitem in self._finalizers:
            assert (
                colitem is None or colitem in self.stack or isinstance(colitem, tuple)
            )

    def teardown_all(self):
        while self.stack:
            self._pop_and_teardown()
        for key in list(self._finalizers):
            self._teardown_with_finalization(key)
        assert not self._finalizers

    def teardown_exact(self, item, nextitem):
        needed_collectors = nextitem and nextitem.listchain() or []
        self._teardown_towards(needed_collectors)

    def _teardown_towards(self, needed_collectors):
        exc = None
        while self.stack:
            if self.stack == needed_collectors[: len(self.stack)]:
                break
            try:
                self._pop_and_teardown()
            except TEST_OUTCOME:
                # XXX Only first exception will be seen by user,
                #     ideally all should be reported.
                if exc is None:
                    exc = sys.exc_info()
        if exc:
            six.reraise(*exc)

    def prepare(self, colitem):
        """ setup objects along the collector chain to the test-method
            and teardown previously setup objects."""
        needed_collectors = colitem.listchain()
        self._teardown_towards(needed_collectors)

        # check if the last collection node has raised an error
        for col in self.stack:
            if hasattr(col, "_prepare_exc"):
                six.reraise(*col._prepare_exc)
        for col in needed_collectors[len(self.stack) :]:
            self.stack.append(col)
            try:
                col.setup()
            except TEST_OUTCOME:
                col._prepare_exc = sys.exc_info()
                raise


def collect_one_node(collector):
    ihook = collector.ihook
    ihook.pytest_collectstart(collector=collector)
    rep = ihook.pytest_make_collect_report(collector=collector)
    call = rep.__dict__.pop("call", None)
    if call and check_interactive_exception(call, rep):
        ihook.pytest_exception_interact(node=collector, call=call, report=rep)
    return rep
