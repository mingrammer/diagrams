from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import warnings

import attr
import py
import six

import _pytest._code
from _pytest.compat import getfslineno
from _pytest.mark.structures import MarkInfo
from _pytest.mark.structures import NodeKeywords
from _pytest.outcomes import fail

SEP = "/"

tracebackcutdir = py.path.local(_pytest.__file__).dirpath()


def _splitnode(nodeid):
    """Split a nodeid into constituent 'parts'.

    Node IDs are strings, and can be things like:
        ''
        'testing/code'
        'testing/code/test_excinfo.py'
        'testing/code/test_excinfo.py::TestFormattedExcinfo::()'

    Return values are lists e.g.
        []
        ['testing', 'code']
        ['testing', 'code', 'test_excinfo.py']
        ['testing', 'code', 'test_excinfo.py', 'TestFormattedExcinfo', '()']
    """
    if nodeid == "":
        # If there is no root node at all, return an empty list so the caller's logic can remain sane
        return []
    parts = nodeid.split(SEP)
    # Replace single last element 'test_foo.py::Bar::()' with multiple elements 'test_foo.py', 'Bar', '()'
    parts[-1:] = parts[-1].split("::")
    return parts


def ischildnode(baseid, nodeid):
    """Return True if the nodeid is a child node of the baseid.

    E.g. 'foo/bar::Baz::()' is a child of 'foo', 'foo/bar' and 'foo/bar::Baz', but not of 'foo/blorp'
    """
    base_parts = _splitnode(baseid)
    node_parts = _splitnode(nodeid)
    if len(node_parts) < len(base_parts):
        return False
    return node_parts[: len(base_parts)] == base_parts


@attr.s
class _CompatProperty(object):
    name = attr.ib()

    def __get__(self, obj, owner):
        if obj is None:
            return self

        from _pytest.deprecated import COMPAT_PROPERTY

        warnings.warn(
            COMPAT_PROPERTY.format(name=self.name, owner=owner.__name__), stacklevel=2
        )
        return getattr(__import__("pytest"), self.name)


class Node(object):
    """ base class for Collector and Item the test collection tree.
    Collector subclasses have children, Items are terminal nodes."""

    def __init__(
        self, name, parent=None, config=None, session=None, fspath=None, nodeid=None
    ):
        #: a unique name within the scope of the parent node
        self.name = name

        #: the parent collector node.
        self.parent = parent

        #: the pytest config object
        self.config = config or parent.config

        #: the session this node is part of
        self.session = session or parent.session

        #: filesystem path where this node was collected from (can be None)
        self.fspath = fspath or getattr(parent, "fspath", None)

        #: keywords/markers collected from all scopes
        self.keywords = NodeKeywords(self)

        #: the marker objects belonging to this node
        self.own_markers = []

        #: allow adding of extra keywords to use for matching
        self.extra_keyword_matches = set()

        # used for storing artificial fixturedefs for direct parametrization
        self._name2pseudofixturedef = {}

        if nodeid is not None:
            self._nodeid = nodeid
        else:
            assert parent is not None
            self._nodeid = self.parent.nodeid + "::" + self.name

    @property
    def ihook(self):
        """ fspath sensitive hook proxy used to call pytest hooks"""
        return self.session.gethookproxy(self.fspath)

    Module = _CompatProperty("Module")
    Class = _CompatProperty("Class")
    Instance = _CompatProperty("Instance")
    Function = _CompatProperty("Function")
    File = _CompatProperty("File")
    Item = _CompatProperty("Item")

    def _getcustomclass(self, name):
        maybe_compatprop = getattr(type(self), name)
        if isinstance(maybe_compatprop, _CompatProperty):
            return getattr(__import__("pytest"), name)
        else:
            from _pytest.deprecated import CUSTOM_CLASS

            cls = getattr(self, name)
            self.warn(CUSTOM_CLASS.format(name=name, type_name=type(self).__name__))
        return cls

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, getattr(self, "name", None))

    def warn(self, _code_or_warning=None, message=None, code=None):
        """Issue a warning for this item.

        Warnings will be displayed after the test session, unless explicitly suppressed.

        This can be called in two forms:

        **Warning instance**

        This was introduced in pytest 3.8 and uses the standard warning mechanism to issue warnings.

        .. code-block:: python

            node.warn(PytestWarning("some message"))

        The warning instance must be a subclass of :class:`pytest.PytestWarning`.

        **code/message (deprecated)**

        This form was used in pytest prior to 3.8 and is considered deprecated. Using this form will emit another
        warning about the deprecation:

        .. code-block:: python

            node.warn("CI", "some message")

        :param Union[Warning,str] _code_or_warning:
            warning instance or warning code (legacy). This parameter receives an underscore for backward
            compatibility with the legacy code/message form, and will be replaced for something
            more usual when the legacy form is removed.

        :param Union[str,None] message: message to display when called in the legacy form.
        :param str code: code for the warning, in legacy form when using keyword arguments.
        :return:
        """
        if message is None:
            if _code_or_warning is None:
                raise ValueError("code_or_warning must be given")
            self._std_warn(_code_or_warning)
        else:
            if _code_or_warning and code:
                raise ValueError(
                    "code_or_warning and code cannot both be passed to this function"
                )
            code = _code_or_warning or code
            self._legacy_warn(code, message)

    def _legacy_warn(self, code, message):
        """
        .. deprecated:: 3.8

            Use :meth:`Node.std_warn <_pytest.nodes.Node.std_warn>` instead.

        Generate a warning with the given code and message for this item.
        """
        from _pytest.deprecated import NODE_WARN

        self._std_warn(NODE_WARN)

        assert isinstance(code, str)
        fslocation = get_fslocation_from_item(self)
        self.ihook.pytest_logwarning.call_historic(
            kwargs=dict(
                code=code, message=message, nodeid=self.nodeid, fslocation=fslocation
            )
        )

    def _std_warn(self, warning):
        """Issue a warning for this item.

        Warnings will be displayed after the test session, unless explicitly suppressed

        :param Warning warning: the warning instance to issue. Must be a subclass of PytestWarning.

        :raise ValueError: if ``warning`` instance is not a subclass of PytestWarning.
        """
        from _pytest.warning_types import PytestWarning

        if not isinstance(warning, PytestWarning):
            raise ValueError(
                "warning must be an instance of PytestWarning or subclass, got {!r}".format(
                    warning
                )
            )
        path, lineno = get_fslocation_from_item(self)
        warnings.warn_explicit(
            warning,
            category=None,
            filename=str(path),
            lineno=lineno + 1 if lineno is not None else None,
        )

    # methods for ordering nodes
    @property
    def nodeid(self):
        """ a ::-separated string denoting its collection tree address. """
        return self._nodeid

    def __hash__(self):
        return hash(self.nodeid)

    def setup(self):
        pass

    def teardown(self):
        pass

    def listchain(self):
        """ return list of all parent collectors up to self,
            starting from root of collection tree. """
        chain = []
        item = self
        while item is not None:
            chain.append(item)
            item = item.parent
        chain.reverse()
        return chain

    def add_marker(self, marker, append=True):
        """dynamically add a marker object to the node.

        :type marker: ``str`` or ``pytest.mark.*``  object
        :param marker:
            ``append=True`` whether to append the marker,
            if ``False`` insert at position ``0``.
        """
        from _pytest.mark import MarkDecorator, MARK_GEN

        if isinstance(marker, six.string_types):
            marker = getattr(MARK_GEN, marker)
        elif not isinstance(marker, MarkDecorator):
            raise ValueError("is not a string or pytest.mark.* Marker")
        self.keywords[marker.name] = marker
        if append:
            self.own_markers.append(marker.mark)
        else:
            self.own_markers.insert(0, marker.mark)

    def iter_markers(self, name=None):
        """
        :param name: if given, filter the results by the name attribute

        iterate over all markers of the node
        """
        return (x[1] for x in self.iter_markers_with_node(name=name))

    def iter_markers_with_node(self, name=None):
        """
        :param name: if given, filter the results by the name attribute

        iterate over all markers of the node
        returns sequence of tuples (node, mark)
        """
        for node in reversed(self.listchain()):
            for mark in node.own_markers:
                if name is None or getattr(mark, "name", None) == name:
                    yield node, mark

    def get_closest_marker(self, name, default=None):
        """return the first marker matching the name, from closest (for example function) to farther level (for example
        module level).

        :param default: fallback return value of no marker was found
        :param name: name to filter by
        """
        return next(self.iter_markers(name=name), default)

    def get_marker(self, name):
        """ get a marker object from this node or None if
        the node doesn't have a marker with that name.

        .. deprecated:: 3.6
            This function has been deprecated in favor of
            :meth:`Node.get_closest_marker <_pytest.nodes.Node.get_closest_marker>` and
            :meth:`Node.iter_markers <_pytest.nodes.Node.iter_markers>`, see :ref:`update marker code`
            for more details.
        """
        markers = list(self.iter_markers(name=name))
        if markers:
            return MarkInfo(markers)

    def listextrakeywords(self):
        """ Return a set of all extra keywords in self and any parents."""
        extra_keywords = set()
        for item in self.listchain():
            extra_keywords.update(item.extra_keyword_matches)
        return extra_keywords

    def listnames(self):
        return [x.name for x in self.listchain()]

    def addfinalizer(self, fin):
        """ register a function to be called when this node is finalized.

        This method can only be called when this node is active
        in a setup chain, for example during self.setup().
        """
        self.session._setupstate.addfinalizer(fin, self)

    def getparent(self, cls):
        """ get the next parent node (including ourself)
        which is an instance of the given class"""
        current = self
        while current and not isinstance(current, cls):
            current = current.parent
        return current

    def _prunetraceback(self, excinfo):
        pass

    def _repr_failure_py(self, excinfo, style=None):
        if excinfo.errisinstance(fail.Exception):
            if not excinfo.value.pytrace:
                return six.text_type(excinfo.value)
        fm = self.session._fixturemanager
        if excinfo.errisinstance(fm.FixtureLookupError):
            return excinfo.value.formatrepr()
        tbfilter = True
        if self.config.option.fulltrace:
            style = "long"
        else:
            tb = _pytest._code.Traceback([excinfo.traceback[-1]])
            self._prunetraceback(excinfo)
            if len(excinfo.traceback) == 0:
                excinfo.traceback = tb
            tbfilter = False  # prunetraceback already does it
            if style == "auto":
                style = "long"
        # XXX should excinfo.getrepr record all data and toterminal() process it?
        if style is None:
            if self.config.option.tbstyle == "short":
                style = "short"
            else:
                style = "long"

        if self.config.option.verbose > 1:
            truncate_locals = False
        else:
            truncate_locals = True

        try:
            os.getcwd()
            abspath = False
        except OSError:
            abspath = True

        return excinfo.getrepr(
            funcargs=True,
            abspath=abspath,
            showlocals=self.config.option.showlocals,
            style=style,
            tbfilter=tbfilter,
            truncate_locals=truncate_locals,
        )

    repr_failure = _repr_failure_py


def get_fslocation_from_item(item):
    """Tries to extract the actual location from an item, depending on available attributes:

    * "fslocation": a pair (path, lineno)
    * "obj": a Python object that the item wraps.
    * "fspath": just a path

    :rtype: a tuple of (str|LocalPath, int) with filename and line number.
    """
    result = getattr(item, "location", None)
    if result is not None:
        return result[:2]
    obj = getattr(item, "obj", None)
    if obj is not None:
        return getfslineno(obj)
    return getattr(item, "fspath", "unknown location"), -1


class Collector(Node):
    """ Collector instances create children through collect()
        and thus iteratively build a tree.
    """

    class CollectError(Exception):
        """ an error during collection, contains a custom message. """

    def collect(self):
        """ returns a list of children (items and collectors)
            for this collection node.
        """
        raise NotImplementedError("abstract")

    def repr_failure(self, excinfo):
        """ represent a collection failure. """
        if excinfo.errisinstance(self.CollectError):
            exc = excinfo.value
            return str(exc.args[0])
        return self._repr_failure_py(excinfo, style="short")

    def _prunetraceback(self, excinfo):
        if hasattr(self, "fspath"):
            traceback = excinfo.traceback
            ntraceback = traceback.cut(path=self.fspath)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(excludepath=tracebackcutdir)
            excinfo.traceback = ntraceback.filter()


def _check_initialpaths_for_relpath(session, fspath):
    for initial_path in session._initialpaths:
        if fspath.common(initial_path) == initial_path:
            return fspath.relto(initial_path)


class FSCollector(Collector):
    def __init__(self, fspath, parent=None, config=None, session=None, nodeid=None):
        fspath = py.path.local(fspath)  # xxx only for test_resultlog.py?
        name = fspath.basename
        if parent is not None:
            rel = fspath.relto(parent.fspath)
            if rel:
                name = rel
            name = name.replace(os.sep, SEP)
        self.fspath = fspath

        session = session or parent.session

        if nodeid is None:
            nodeid = self.fspath.relto(session.config.rootdir)

            if not nodeid:
                nodeid = _check_initialpaths_for_relpath(session, fspath)
            if nodeid and os.sep != SEP:
                nodeid = nodeid.replace(os.sep, SEP)

        super(FSCollector, self).__init__(
            name, parent, config, session, nodeid=nodeid, fspath=fspath
        )


class File(FSCollector):
    """ base class for collecting tests from a file. """


class Item(Node):
    """ a basic test invocation item. Note that for a single function
    there might be multiple test invocation items.
    """

    nextitem = None

    def __init__(self, name, parent=None, config=None, session=None, nodeid=None):
        super(Item, self).__init__(name, parent, config, session, nodeid=nodeid)
        self._report_sections = []

        #: user properties is a list of tuples (name, value) that holds user
        #: defined properties for this test.
        self.user_properties = []

    def add_report_section(self, when, key, content):
        """
        Adds a new report section, similar to what's done internally to add stdout and
        stderr captured output::

            item.add_report_section("call", "stdout", "report section contents")

        :param str when:
            One of the possible capture states, ``"setup"``, ``"call"``, ``"teardown"``.
        :param str key:
            Name of the section, can be customized at will. Pytest uses ``"stdout"`` and
            ``"stderr"`` internally.

        :param str content:
            The full contents as a string.
        """
        if content:
            self._report_sections.append((when, key, content))

    def reportinfo(self):
        return self.fspath, None, ""

    @property
    def location(self):
        try:
            return self._location
        except AttributeError:
            location = self.reportinfo()
            # bestrelpath is a quite slow function
            cache = self.config.__dict__.setdefault("_bestrelpathcache", {})
            try:
                fspath = cache[location[0]]
            except KeyError:
                fspath = self.session.fspath.bestrelpath(location[0])
                cache[location[0]] = fspath
            location = (fspath, location[1], str(location[2]))
            self._location = location
            return location
