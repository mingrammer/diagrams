"""
merged implementation of the cache provider

the name cache was not chosen to ensure pluggy automatically
ignores the external pytest-cache
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from collections import OrderedDict

import attr
import py
import six

import pytest
from .compat import _PY2 as PY2
from .pathlib import Path
from .pathlib import resolve_from_str
from .pathlib import rmtree

README_CONTENT = u"""\
# pytest cache directory #

This directory contains data from the pytest's cache plugin,
which provides the `--lf` and `--ff` options, as well as the `cache` fixture.

**Do not** commit this to version control.

See [the docs](https://docs.pytest.org/en/latest/cache.html) for more information.
"""


@attr.s
class Cache(object):
    _cachedir = attr.ib(repr=False)
    _config = attr.ib(repr=False)

    @classmethod
    def for_config(cls, config):
        cachedir = cls.cache_dir_from_config(config)
        if config.getoption("cacheclear") and cachedir.exists():
            rmtree(cachedir, force=True)
            cachedir.mkdir()
        return cls(cachedir, config)

    @staticmethod
    def cache_dir_from_config(config):
        return resolve_from_str(config.getini("cache_dir"), config.rootdir)

    def warn(self, fmt, **args):
        from _pytest.warnings import _issue_config_warning
        from _pytest.warning_types import PytestWarning

        _issue_config_warning(
            PytestWarning(fmt.format(**args) if args else fmt), self._config
        )

    def makedir(self, name):
        """ return a directory path object with the given name.  If the
        directory does not yet exist, it will be created.  You can use it
        to manage files likes e. g. store/retrieve database
        dumps across test sessions.

        :param name: must be a string not containing a ``/`` separator.
             Make sure the name contains your plugin or application
             identifiers to prevent clashes with other cache users.
        """
        name = Path(name)
        if len(name.parts) > 1:
            raise ValueError("name is not allowed to contain path separators")
        res = self._cachedir.joinpath("d", name)
        res.mkdir(exist_ok=True, parents=True)
        return py.path.local(res)

    def _getvaluepath(self, key):
        return self._cachedir.joinpath("v", Path(key))

    def get(self, key, default):
        """ return cached value for the given key.  If no value
        was yet cached or the value cannot be read, the specified
        default is returned.

        :param key: must be a ``/`` separated value. Usually the first
             name is the name of your plugin or your application.
        :param default: must be provided in case of a cache-miss or
             invalid cache values.

        """
        path = self._getvaluepath(key)
        try:
            with path.open("r") as f:
                return json.load(f)
        except (ValueError, IOError, OSError):
            return default

    def set(self, key, value):
        """ save value for the given key.

        :param key: must be a ``/`` separated value. Usually the first
             name is the name of your plugin or your application.
        :param value: must be of any combination of basic
               python types, including nested types
               like e. g. lists of dictionaries.
        """
        path = self._getvaluepath(key)
        try:
            path.parent.mkdir(exist_ok=True, parents=True)
        except (IOError, OSError):
            self.warn("could not create cache path {path}", path=path)
            return
        try:
            f = path.open("wb" if PY2 else "w")
        except (IOError, OSError):
            self.warn("cache could not write path {path}", path=path)
        else:
            with f:
                json.dump(value, f, indent=2, sort_keys=True)
                self._ensure_supporting_files()

    def _ensure_supporting_files(self):
        """Create supporting files in the cache dir that are not really part of the cache."""
        if self._cachedir.is_dir():
            readme_path = self._cachedir / "README.md"
            if not readme_path.is_file():
                readme_path.write_text(README_CONTENT)

            msg = u"# created by pytest automatically, do not change\n*"
            self._cachedir.joinpath(".gitignore").write_text(msg, encoding="UTF-8")


class LFPlugin(object):
    """ Plugin which implements the --lf (run last-failing) option """

    def __init__(self, config):
        self.config = config
        active_keys = "lf", "failedfirst"
        self.active = any(config.getoption(key) for key in active_keys)
        self.lastfailed = config.cache.get("cache/lastfailed", {})
        self._previously_failed_count = None
        self._no_failures_behavior = self.config.getoption("last_failed_no_failures")

    def pytest_report_collectionfinish(self):
        if self.active and self.config.getoption("verbose") >= 0:
            if not self._previously_failed_count:
                return None
            noun = "failure" if self._previously_failed_count == 1 else "failures"
            suffix = " first" if self.config.getoption("failedfirst") else ""
            mode = "rerun previous {count} {noun}{suffix}".format(
                count=self._previously_failed_count, suffix=suffix, noun=noun
            )
            return "run-last-failure: %s" % mode

    def pytest_runtest_logreport(self, report):
        if (report.when == "call" and report.passed) or report.skipped:
            self.lastfailed.pop(report.nodeid, None)
        elif report.failed:
            self.lastfailed[report.nodeid] = True

    def pytest_collectreport(self, report):
        passed = report.outcome in ("passed", "skipped")
        if passed:
            if report.nodeid in self.lastfailed:
                self.lastfailed.pop(report.nodeid)
                self.lastfailed.update((item.nodeid, True) for item in report.result)
        else:
            self.lastfailed[report.nodeid] = True

    def pytest_collection_modifyitems(self, session, config, items):
        if self.active:
            if self.lastfailed:
                previously_failed = []
                previously_passed = []
                for item in items:
                    if item.nodeid in self.lastfailed:
                        previously_failed.append(item)
                    else:
                        previously_passed.append(item)
                self._previously_failed_count = len(previously_failed)
                if not previously_failed:
                    # running a subset of all tests with recorded failures outside
                    # of the set of tests currently executing
                    return
                if self.config.getoption("lf"):
                    items[:] = previously_failed
                    config.hook.pytest_deselected(items=previously_passed)
                else:
                    items[:] = previously_failed + previously_passed
            elif self._no_failures_behavior == "none":
                config.hook.pytest_deselected(items=items)
                items[:] = []

    def pytest_sessionfinish(self, session):
        config = self.config
        if config.getoption("cacheshow") or hasattr(config, "slaveinput"):
            return

        saved_lastfailed = config.cache.get("cache/lastfailed", {})
        if saved_lastfailed != self.lastfailed:
            config.cache.set("cache/lastfailed", self.lastfailed)


class NFPlugin(object):
    """ Plugin which implements the --nf (run new-first) option """

    def __init__(self, config):
        self.config = config
        self.active = config.option.newfirst
        self.cached_nodeids = config.cache.get("cache/nodeids", [])

    def pytest_collection_modifyitems(self, session, config, items):
        if self.active:
            new_items = OrderedDict()
            other_items = OrderedDict()
            for item in items:
                if item.nodeid not in self.cached_nodeids:
                    new_items[item.nodeid] = item
                else:
                    other_items[item.nodeid] = item

            items[:] = self._get_increasing_order(
                six.itervalues(new_items)
            ) + self._get_increasing_order(six.itervalues(other_items))
        self.cached_nodeids = [x.nodeid for x in items if isinstance(x, pytest.Item)]

    def _get_increasing_order(self, items):
        return sorted(items, key=lambda item: item.fspath.mtime(), reverse=True)

    def pytest_sessionfinish(self, session):
        config = self.config
        if config.getoption("cacheshow") or hasattr(config, "slaveinput"):
            return

        config.cache.set("cache/nodeids", self.cached_nodeids)


def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption(
        "--lf",
        "--last-failed",
        action="store_true",
        dest="lf",
        help="rerun only the tests that failed "
        "at the last run (or all if none failed)",
    )
    group.addoption(
        "--ff",
        "--failed-first",
        action="store_true",
        dest="failedfirst",
        help="run all tests but run the last failures first.  "
        "This may re-order tests and thus lead to "
        "repeated fixture setup/teardown",
    )
    group.addoption(
        "--nf",
        "--new-first",
        action="store_true",
        dest="newfirst",
        help="run tests from new files first, then the rest of the tests "
        "sorted by file mtime",
    )
    group.addoption(
        "--cache-show",
        action="store_true",
        dest="cacheshow",
        help="show cache contents, don't perform collection or tests",
    )
    group.addoption(
        "--cache-clear",
        action="store_true",
        dest="cacheclear",
        help="remove all cache contents at start of test run.",
    )
    parser.addini("cache_dir", default=".pytest_cache", help="cache directory path.")
    group.addoption(
        "--lfnf",
        "--last-failed-no-failures",
        action="store",
        dest="last_failed_no_failures",
        choices=("all", "none"),
        default="all",
        help="change the behavior when no test failed in the last run or no "
        "information about the last failures was found in the cache",
    )


def pytest_cmdline_main(config):
    if config.option.cacheshow:
        from _pytest.main import wrap_session

        return wrap_session(config, cacheshow)


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    config.cache = Cache.for_config(config)
    config.pluginmanager.register(LFPlugin(config), "lfplugin")
    config.pluginmanager.register(NFPlugin(config), "nfplugin")


@pytest.fixture
def cache(request):
    """
    Return a cache object that can persist state between testing sessions.

    cache.get(key, default)
    cache.set(key, value)

    Keys must be a ``/`` separated value, where the first part is usually the
    name of your plugin or application to avoid clashes with other cache users.

    Values can be any object handled by the json stdlib module.
    """
    return request.config.cache


def pytest_report_header(config):
    """Display cachedir with --cache-show and if non-default."""
    if config.option.verbose or config.getini("cache_dir") != ".pytest_cache":
        cachedir = config.cache._cachedir
        # TODO: evaluate generating upward relative paths
        # starting with .., ../.. if sensible

        try:
            displaypath = cachedir.relative_to(config.rootdir)
        except ValueError:
            displaypath = cachedir
        return "cachedir: {}".format(displaypath)


def cacheshow(config, session):
    from pprint import pformat

    tw = py.io.TerminalWriter()
    tw.line("cachedir: " + str(config.cache._cachedir))
    if not config.cache._cachedir.is_dir():
        tw.line("cache is empty")
        return 0
    dummy = object()
    basedir = config.cache._cachedir
    vdir = basedir / "v"
    tw.sep("-", "cache values")
    for valpath in sorted(x for x in vdir.rglob("*") if x.is_file()):
        key = valpath.relative_to(vdir)
        val = config.cache.get(key, dummy)
        if val is dummy:
            tw.line("%s contains unreadable content, will be ignored" % key)
        else:
            tw.line("%s contains:" % key)
            for line in pformat(val).splitlines():
                tw.line("  " + line)

    ddir = basedir / "d"
    if ddir.is_dir():
        contents = sorted(ddir.rglob("*"))
        tw.sep("-", "cache directories")
        for p in contents:
            # if p.check(dir=1):
            #    print("%s/" % p.relto(basedir))
            if p.is_file():
                key = p.relative_to(basedir)
                tw.line("{} is a file of length {:d}".format(key, p.stat().st_size))
    return 0
