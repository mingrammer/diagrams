import inspect
import warnings
from collections import namedtuple
from functools import reduce
from operator import attrgetter

import attr
from six.moves import map

from ..compat import getfslineno
from ..compat import MappingMixin
from ..compat import NOTSET
from ..deprecated import MARK_INFO_ATTRIBUTE
from ..deprecated import MARK_PARAMETERSET_UNPACKING
from _pytest.outcomes import fail


EMPTY_PARAMETERSET_OPTION = "empty_parameter_set_mark"


def alias(name, warning=None):
    getter = attrgetter(name)

    def warned(self):
        warnings.warn(warning, stacklevel=2)
        return getter(self)

    return property(getter if warning is None else warned, doc="alias for " + name)


def istestfunc(func):
    return (
        hasattr(func, "__call__")
        and getattr(func, "__name__", "<lambda>") != "<lambda>"
    )


def get_empty_parameterset_mark(config, argnames, func):
    from ..nodes import Collector

    requested_mark = config.getini(EMPTY_PARAMETERSET_OPTION)
    if requested_mark in ("", None, "skip"):
        mark = MARK_GEN.skip
    elif requested_mark == "xfail":
        mark = MARK_GEN.xfail(run=False)
    elif requested_mark == "fail_at_collect":
        f_name = func.__name__
        _, lineno = getfslineno(func)
        raise Collector.CollectError(
            "Empty parameter set in '%s' at line %d" % (f_name, lineno)
        )
    else:
        raise LookupError(requested_mark)
    fs, lineno = getfslineno(func)
    reason = "got empty parameter set %r, function %s at %s:%d" % (
        argnames,
        func.__name__,
        fs,
        lineno,
    )
    return mark(reason=reason)


class ParameterSet(namedtuple("ParameterSet", "values, marks, id")):
    @classmethod
    def param(cls, *values, **kw):
        marks = kw.pop("marks", ())
        if isinstance(marks, MarkDecorator):
            marks = (marks,)
        else:
            assert isinstance(marks, (tuple, list, set))

        def param_extract_id(id=None):
            return id

        id_ = param_extract_id(**kw)
        return cls(values, marks, id_)

    @classmethod
    def extract_from(cls, parameterset, belonging_definition, legacy_force_tuple=False):
        """
        :param parameterset:
            a legacy style parameterset that may or may not be a tuple,
            and may or may not be wrapped into a mess of mark objects

        :param legacy_force_tuple:
            enforce tuple wrapping so single argument tuple values
            don't get decomposed and break tests

        :param belonging_definition: the item that we will be extracting the parameters from.
        """

        if isinstance(parameterset, cls):
            return parameterset
        if not isinstance(parameterset, MarkDecorator) and legacy_force_tuple:
            return cls.param(parameterset)

        newmarks = []
        argval = parameterset
        while isinstance(argval, MarkDecorator):
            newmarks.append(
                MarkDecorator(Mark(argval.markname, argval.args[:-1], argval.kwargs))
            )
            argval = argval.args[-1]
        assert not isinstance(argval, ParameterSet)
        if legacy_force_tuple:
            argval = (argval,)

        if newmarks and belonging_definition is not None:
            belonging_definition.warn(MARK_PARAMETERSET_UNPACKING)

        return cls(argval, marks=newmarks, id=None)

    @classmethod
    def _for_parametrize(cls, argnames, argvalues, func, config, function_definition):
        if not isinstance(argnames, (tuple, list)):
            argnames = [x.strip() for x in argnames.split(",") if x.strip()]
            force_tuple = len(argnames) == 1
        else:
            force_tuple = False
        parameters = [
            ParameterSet.extract_from(
                x,
                legacy_force_tuple=force_tuple,
                belonging_definition=function_definition,
            )
            for x in argvalues
        ]
        del argvalues

        if parameters:
            # check all parameter sets have the correct number of values
            for param in parameters:
                if len(param.values) != len(argnames):
                    raise ValueError(
                        'In "parametrize" the number of values ({}) must be '
                        "equal to the number of names ({})".format(
                            param.values, argnames
                        )
                    )
        else:
            # empty parameter set (likely computed at runtime): create a single
            # parameter set with NOSET values, with the "empty parameter set" mark applied to it
            mark = get_empty_parameterset_mark(config, argnames, func)
            parameters.append(
                ParameterSet(values=(NOTSET,) * len(argnames), marks=[mark], id=None)
            )
        return argnames, parameters


@attr.s(frozen=True)
class Mark(object):
    #: name of the mark
    name = attr.ib(type=str)
    #: positional arguments of the mark decorator
    args = attr.ib()  # type: List[object]
    #: keyword arguments of the mark decorator
    kwargs = attr.ib()  # type: Dict[str, object]

    def combined_with(self, other):
        """
        :param other: the mark to combine with
        :type other: Mark
        :rtype: Mark

        combines by appending aargs and merging the mappings
        """
        assert self.name == other.name
        return Mark(
            self.name, self.args + other.args, dict(self.kwargs, **other.kwargs)
        )


@attr.s
class MarkDecorator(object):
    """ A decorator for test functions and test classes.  When applied
    it will create :class:`MarkInfo` objects which may be
    :ref:`retrieved by hooks as item keywords <excontrolskip>`.
    MarkDecorator instances are often created like this::

        mark1 = pytest.mark.NAME              # simple MarkDecorator
        mark2 = pytest.mark.NAME(name1=value) # parametrized MarkDecorator

    and can then be applied as decorators to test functions::

        @mark2
        def test_function():
            pass

    When a MarkDecorator instance is called it does the following:
      1. If called with a single class as its only positional argument and no
         additional keyword arguments, it attaches itself to the class so it
         gets applied automatically to all test cases found in that class.
      2. If called with a single function as its only positional argument and
         no additional keyword arguments, it attaches a MarkInfo object to the
         function, containing all the arguments already stored internally in
         the MarkDecorator.
      3. When called in any other case, it performs a 'fake construction' call,
         i.e. it returns a new MarkDecorator instance with the original
         MarkDecorator's content updated with the arguments passed to this
         call.

    Note: The rules above prevent MarkDecorator objects from storing only a
    single function or class reference as their positional argument with no
    additional keyword or positional arguments.

    """

    mark = attr.ib(validator=attr.validators.instance_of(Mark))

    name = alias("mark.name")
    args = alias("mark.args")
    kwargs = alias("mark.kwargs")

    @property
    def markname(self):
        return self.name  # for backward-compat (2.4.1 had this attr)

    def __eq__(self, other):
        return self.mark == other.mark if isinstance(other, MarkDecorator) else False

    def __repr__(self):
        return "<MarkDecorator %r>" % (self.mark,)

    def with_args(self, *args, **kwargs):
        """ return a MarkDecorator with extra arguments added

        unlike call this can be used even if the sole argument is a callable/class

        :return: MarkDecorator
        """

        mark = Mark(self.name, args, kwargs)
        return self.__class__(self.mark.combined_with(mark))

    def __call__(self, *args, **kwargs):
        """ if passed a single callable argument: decorate it with mark info.
            otherwise add *args/**kwargs in-place to mark information. """
        if args and not kwargs:
            func = args[0]
            is_class = inspect.isclass(func)
            if len(args) == 1 and (istestfunc(func) or is_class):
                if is_class:
                    store_mark(func, self.mark)
                else:
                    store_legacy_markinfo(func, self.mark)
                    store_mark(func, self.mark)
                return func
        return self.with_args(*args, **kwargs)


def get_unpacked_marks(obj):
    """
    obtain the unpacked marks that are stored on an object
    """
    mark_list = getattr(obj, "pytestmark", [])
    if not isinstance(mark_list, list):
        mark_list = [mark_list]
    return normalize_mark_list(mark_list)


def normalize_mark_list(mark_list):
    """
    normalizes marker decorating helpers to mark objects

    :type mark_list: List[Union[Mark, Markdecorator]]
    :rtype: List[Mark]
    """
    return [getattr(mark, "mark", mark) for mark in mark_list]  # unpack MarkDecorator


def store_mark(obj, mark):
    """store a Mark on an object
    this is used to implement the Mark declarations/decorators correctly
    """
    assert isinstance(mark, Mark), mark
    # always reassign name to avoid updating pytestmark
    # in a reference that was only borrowed
    obj.pytestmark = get_unpacked_marks(obj) + [mark]


def store_legacy_markinfo(func, mark):
    """create the legacy MarkInfo objects and put them onto the function
    """
    if not isinstance(mark, Mark):
        raise TypeError("got {mark!r} instead of a Mark".format(mark=mark))
    holder = getattr(func, mark.name, None)
    if holder is None:
        holder = MarkInfo.for_mark(mark)
        setattr(func, mark.name, holder)
    elif isinstance(holder, MarkInfo):
        holder.add_mark(mark)


def transfer_markers(funcobj, cls, mod):
    """
    this function transfers class level markers and module level markers
    into function level markinfo objects

    this is the main reason why marks are so broken
    the resolution will involve phasing out function level MarkInfo objects

    """
    for obj in (cls, mod):
        for mark in get_unpacked_marks(obj):
            if not _marked(funcobj, mark):
                store_legacy_markinfo(funcobj, mark)


def _marked(func, mark):
    """ Returns True if :func: is already marked with :mark:, False otherwise.
    This can happen if marker is applied to class and the test file is
    invoked more than once.
    """
    try:
        func_mark = getattr(func, getattr(mark, "combined", mark).name)
    except AttributeError:
        return False
    return any(mark == info.combined for info in func_mark)


@attr.s(repr=False)
class MarkInfo(object):
    """ Marking object created by :class:`MarkDecorator` instances. """

    _marks = attr.ib(converter=list)

    @_marks.validator
    def validate_marks(self, attribute, value):
        for item in value:
            if not isinstance(item, Mark):
                raise ValueError(
                    "MarkInfo expects Mark instances, got {!r} ({!r})".format(
                        item, type(item)
                    )
                )

    combined = attr.ib(
        repr=False,
        default=attr.Factory(
            lambda self: reduce(Mark.combined_with, self._marks), takes_self=True
        ),
    )

    name = alias("combined.name", warning=MARK_INFO_ATTRIBUTE)
    args = alias("combined.args", warning=MARK_INFO_ATTRIBUTE)
    kwargs = alias("combined.kwargs", warning=MARK_INFO_ATTRIBUTE)

    @classmethod
    def for_mark(cls, mark):
        return cls([mark])

    def __repr__(self):
        return "<MarkInfo {!r}>".format(self.combined)

    def add_mark(self, mark):
        """ add a MarkInfo with the given args and kwargs. """
        self._marks.append(mark)
        self.combined = self.combined.combined_with(mark)

    def __iter__(self):
        """ yield MarkInfo objects each relating to a marking-call. """
        return map(MarkInfo.for_mark, self._marks)


class MarkGenerator(object):
    """ Factory for :class:`MarkDecorator` objects - exposed as
    a ``pytest.mark`` singleton instance.  Example::

         import pytest
         @pytest.mark.slowtest
         def test_function():
            pass

    will set a 'slowtest' :class:`MarkInfo` object
    on the ``test_function`` object. """

    _config = None

    def __getattr__(self, name):
        if name[0] == "_":
            raise AttributeError("Marker name must NOT start with underscore")
        if self._config is not None:
            self._check(name)
        return MarkDecorator(Mark(name, (), {}))

    def _check(self, name):
        try:
            if name in self._markers:
                return
        except AttributeError:
            pass
        self._markers = values = set()
        for line in self._config.getini("markers"):
            marker = line.split(":", 1)[0]
            marker = marker.rstrip()
            x = marker.split("(", 1)[0]
            values.add(x)
        if name not in self._markers:
            fail("{!r} not a registered marker".format(name), pytrace=False)


MARK_GEN = MarkGenerator()


class NodeKeywords(MappingMixin):
    def __init__(self, node):
        self.node = node
        self.parent = node.parent
        self._markers = {node.name: True}

    def __getitem__(self, key):
        try:
            return self._markers[key]
        except KeyError:
            if self.parent is None:
                raise
            return self.parent.keywords[key]

    def __setitem__(self, key, value):
        self._markers[key] = value

    def __delitem__(self, key):
        raise ValueError("cannot delete key in keywords dict")

    def __iter__(self):
        seen = self._seen()
        return iter(seen)

    def _seen(self):
        seen = set(self._markers)
        if self.parent is not None:
            seen.update(self.parent.keywords)
        return seen

    def __len__(self):
        return len(self._seen())

    def __repr__(self):
        return "<NodeKeywords for node %s>" % (self.node,)


@attr.s(cmp=False, hash=False)
class NodeMarkers(object):
    """
    internal structure for storing marks belonging to a node

    ..warning::

        unstable api

    """

    own_markers = attr.ib(default=attr.Factory(list))

    def update(self, add_markers):
        """update the own markers
        """
        self.own_markers.extend(add_markers)

    def find(self, name):
        """
        find markers in own nodes or parent nodes
        needs a better place
        """
        for mark in self.own_markers:
            if mark.name == name:
                yield mark

    def __iter__(self):
        return iter(self.own_markers)
