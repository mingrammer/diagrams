from __future__ import absolute_import, division, print_function

import copy
import linecache
import sys
import threading
import uuid
import warnings

from operator import itemgetter

from . import _config
from ._compat import (
    PY2,
    isclass,
    iteritems,
    metadata_proxy,
    ordered_dict,
    set_closure_cell,
)
from .exceptions import (
    DefaultAlreadySetError,
    FrozenInstanceError,
    NotAnAttrsClassError,
    PythonTooOldError,
    UnannotatedAttributeError,
)


# This is used at least twice, so cache it here.
_obj_setattr = object.__setattr__
_init_converter_pat = "__attr_converter_{}"
_init_factory_pat = "__attr_factory_{}"
_tuple_property_pat = (
    "    {attr_name} = _attrs_property(_attrs_itemgetter({index}))"
)
_classvar_prefixes = ("typing.ClassVar", "t.ClassVar", "ClassVar")
# we don't use a double-underscore prefix because that triggers
# name mangling when trying to create a slot for the field
# (when slots=True)
_hash_cache_field = "_attrs_cached_hash"

_empty_metadata_singleton = metadata_proxy({})

# Unique object for unequivocal getattr() defaults.
_sentinel = object()


class _Nothing(object):
    """
    Sentinel class to indicate the lack of a value when ``None`` is ambiguous.

    ``_Nothing`` is a singleton. There is only ever one of it.
    """

    _singleton = None

    def __new__(cls):
        if _Nothing._singleton is None:
            _Nothing._singleton = super(_Nothing, cls).__new__(cls)
        return _Nothing._singleton

    def __repr__(self):
        return "NOTHING"


NOTHING = _Nothing()
"""
Sentinel to indicate the lack of a value when ``None`` is ambiguous.
"""


def attrib(
    default=NOTHING,
    validator=None,
    repr=True,
    cmp=None,
    hash=None,
    init=True,
    metadata=None,
    type=None,
    converter=None,
    factory=None,
    kw_only=False,
    eq=None,
    order=None,
):
    """
    Create a new attribute on a class.

    ..  warning::

        Does *not* do anything unless the class is also decorated with
        `attr.s`!

    :param default: A value that is used if an ``attrs``-generated ``__init__``
        is used and no value is passed while instantiating or the attribute is
        excluded using ``init=False``.

        If the value is an instance of `Factory`, its callable will be
        used to construct a new value (useful for mutable data types like lists
        or dicts).

        If a default is not set (or set manually to ``attr.NOTHING``), a value
        *must* be supplied when instantiating; otherwise a `TypeError`
        will be raised.

        The default can also be set using decorator notation as shown below.

    :type default: Any value

    :param callable factory: Syntactic sugar for
        ``default=attr.Factory(callable)``.

    :param validator: `callable` that is called by ``attrs``-generated
        ``__init__`` methods after the instance has been initialized.  They
        receive the initialized instance, the `Attribute`, and the
        passed value.

        The return value is *not* inspected so the validator has to throw an
        exception itself.

        If a ``list`` is passed, its items are treated as validators and must
        all pass.

        Validators can be globally disabled and re-enabled using
        `get_run_validators`.

        The validator can also be set using decorator notation as shown below.

    :type validator: ``callable`` or a ``list`` of ``callable``\\ s.

    :param repr: Include this attribute in the generated ``__repr__``
        method. If ``True``, include the attribute; if ``False``, omit it. By
        default, the built-in ``repr()`` function is used. To override how the
        attribute value is formatted, pass a ``callable`` that takes a single
        value and returns a string. Note that the resulting string is used
        as-is, i.e. it will be used directly *instead* of calling ``repr()``
        (the default).
    :type repr: a ``bool`` or a ``callable`` to use a custom function.
    :param bool eq: If ``True`` (default), include this attribute in the
        generated ``__eq__`` and ``__ne__`` methods that check two instances
        for equality.
    :param bool order: If ``True`` (default), include this attributes in the
        generated ``__lt__``, ``__le__``, ``__gt__`` and ``__ge__`` methods.
    :param bool cmp: Setting to ``True`` is equivalent to setting ``eq=True,
        order=True``. Deprecated in favor of *eq* and *order*.
    :param hash: Include this attribute in the generated ``__hash__``
        method.  If ``None`` (default), mirror *eq*'s value.  This is the
        correct behavior according the Python spec.  Setting this value to
        anything else than ``None`` is *discouraged*.
    :type hash: ``bool`` or ``None``
    :param bool init: Include this attribute in the generated ``__init__``
        method.  It is possible to set this to ``False`` and set a default
        value.  In that case this attributed is unconditionally initialized
        with the specified default value or factory.
    :param callable converter: `callable` that is called by
        ``attrs``-generated ``__init__`` methods to converter attribute's value
        to the desired format.  It is given the passed-in value, and the
        returned value will be used as the new value of the attribute.  The
        value is converted before being passed to the validator, if any.
    :param metadata: An arbitrary mapping, to be used by third-party
        components.  See `extending_metadata`.
    :param type: The type of the attribute.  In Python 3.6 or greater, the
        preferred method to specify the type is using a variable annotation
        (see `PEP 526 <https://www.python.org/dev/peps/pep-0526/>`_).
        This argument is provided for backward compatibility.
        Regardless of the approach used, the type will be stored on
        ``Attribute.type``.

        Please note that ``attrs`` doesn't do anything with this metadata by
        itself. You can use it as part of your own code or for
        `static type checking <types>`.
    :param kw_only: Make this attribute keyword-only (Python 3+)
        in the generated ``__init__`` (if ``init`` is ``False``, this
        parameter is ignored).

    .. versionadded:: 15.2.0 *convert*
    .. versionadded:: 16.3.0 *metadata*
    .. versionchanged:: 17.1.0 *validator* can be a ``list`` now.
    .. versionchanged:: 17.1.0
       *hash* is ``None`` and therefore mirrors *eq* by default.
    .. versionadded:: 17.3.0 *type*
    .. deprecated:: 17.4.0 *convert*
    .. versionadded:: 17.4.0 *converter* as a replacement for the deprecated
       *convert* to achieve consistency with other noun-based arguments.
    .. versionadded:: 18.1.0
       ``factory=f`` is syntactic sugar for ``default=attr.Factory(f)``.
    .. versionadded:: 18.2.0 *kw_only*
    .. versionchanged:: 19.2.0 *convert* keyword argument removed
    .. versionchanged:: 19.2.0 *repr* also accepts a custom callable.
    .. deprecated:: 19.2.0 *cmp* Removal on or after 2021-06-01.
    .. versionadded:: 19.2.0 *eq* and *order*
    """
    eq, order = _determine_eq_order(cmp, eq, order)

    if hash is not None and hash is not True and hash is not False:
        raise TypeError(
            "Invalid value for hash.  Must be True, False, or None."
        )

    if factory is not None:
        if default is not NOTHING:
            raise ValueError(
                "The `default` and `factory` arguments are mutually "
                "exclusive."
            )
        if not callable(factory):
            raise ValueError("The `factory` argument must be a callable.")
        default = Factory(factory)

    if metadata is None:
        metadata = {}

    return _CountingAttr(
        default=default,
        validator=validator,
        repr=repr,
        cmp=None,
        hash=hash,
        init=init,
        converter=converter,
        metadata=metadata,
        type=type,
        kw_only=kw_only,
        eq=eq,
        order=order,
    )


def _make_attr_tuple_class(cls_name, attr_names):
    """
    Create a tuple subclass to hold `Attribute`s for an `attrs` class.

    The subclass is a bare tuple with properties for names.

    class MyClassAttributes(tuple):
        __slots__ = ()
        x = property(itemgetter(0))
    """
    attr_class_name = "{}Attributes".format(cls_name)
    attr_class_template = [
        "class {}(tuple):".format(attr_class_name),
        "    __slots__ = ()",
    ]
    if attr_names:
        for i, attr_name in enumerate(attr_names):
            attr_class_template.append(
                _tuple_property_pat.format(index=i, attr_name=attr_name)
            )
    else:
        attr_class_template.append("    pass")
    globs = {"_attrs_itemgetter": itemgetter, "_attrs_property": property}
    eval(compile("\n".join(attr_class_template), "", "exec"), globs)

    return globs[attr_class_name]


# Tuple class for extracted attributes from a class definition.
# `base_attrs` is a subset of `attrs`.
_Attributes = _make_attr_tuple_class(
    "_Attributes",
    [
        # all attributes to build dunder methods for
        "attrs",
        # attributes that have been inherited
        "base_attrs",
        # map inherited attributes to their originating classes
        "base_attrs_map",
    ],
)


def _is_class_var(annot):
    """
    Check whether *annot* is a typing.ClassVar.

    The string comparison hack is used to avoid evaluating all string
    annotations which would put attrs-based classes at a performance
    disadvantage compared to plain old classes.
    """
    return str(annot).startswith(_classvar_prefixes)


def _get_annotations(cls):
    """
    Get annotations for *cls*.
    """
    anns = getattr(cls, "__annotations__", None)
    if anns is None:
        return {}

    # Verify that the annotations aren't merely inherited.
    for base_cls in cls.__mro__[1:]:
        if anns is getattr(base_cls, "__annotations__", None):
            return {}

    return anns


def _counter_getter(e):
    """
    Key function for sorting to avoid re-creating a lambda for every class.
    """
    return e[1].counter


def _transform_attrs(cls, these, auto_attribs, kw_only):
    """
    Transform all `_CountingAttr`s on a class into `Attribute`s.

    If *these* is passed, use that and don't look for them on the class.

    Return an `_Attributes`.
    """
    cd = cls.__dict__
    anns = _get_annotations(cls)

    if these is not None:
        ca_list = [(name, ca) for name, ca in iteritems(these)]

        if not isinstance(these, ordered_dict):
            ca_list.sort(key=_counter_getter)
    elif auto_attribs is True:
        ca_names = {
            name
            for name, attr in cd.items()
            if isinstance(attr, _CountingAttr)
        }
        ca_list = []
        annot_names = set()
        for attr_name, type in anns.items():
            if _is_class_var(type):
                continue
            annot_names.add(attr_name)
            a = cd.get(attr_name, NOTHING)
            if not isinstance(a, _CountingAttr):
                if a is NOTHING:
                    a = attrib()
                else:
                    a = attrib(default=a)
            ca_list.append((attr_name, a))

        unannotated = ca_names - annot_names
        if len(unannotated) > 0:
            raise UnannotatedAttributeError(
                "The following `attr.ib`s lack a type annotation: "
                + ", ".join(
                    sorted(unannotated, key=lambda n: cd.get(n).counter)
                )
                + "."
            )
    else:
        ca_list = sorted(
            (
                (name, attr)
                for name, attr in cd.items()
                if isinstance(attr, _CountingAttr)
            ),
            key=lambda e: e[1].counter,
        )

    own_attrs = [
        Attribute.from_counting_attr(
            name=attr_name, ca=ca, type=anns.get(attr_name)
        )
        for attr_name, ca in ca_list
    ]

    base_attrs = []
    base_attr_map = {}  # A dictionary of base attrs to their classes.
    taken_attr_names = {a.name: a for a in own_attrs}

    # Traverse the MRO and collect attributes.
    for base_cls in cls.__mro__[1:-1]:
        sub_attrs = getattr(base_cls, "__attrs_attrs__", None)
        if sub_attrs is not None:
            for a in sub_attrs:
                prev_a = taken_attr_names.get(a.name)
                # Only add an attribute if it hasn't been defined before.  This
                # allows for overwriting attribute definitions by subclassing.
                if prev_a is None:
                    base_attrs.append(a)
                    taken_attr_names[a.name] = a
                    base_attr_map[a.name] = base_cls

    attr_names = [a.name for a in base_attrs + own_attrs]

    AttrsClass = _make_attr_tuple_class(cls.__name__, attr_names)

    if kw_only:
        own_attrs = [a._assoc(kw_only=True) for a in own_attrs]
        base_attrs = [a._assoc(kw_only=True) for a in base_attrs]

    attrs = AttrsClass(base_attrs + own_attrs)

    # Mandatory vs non-mandatory attr order only matters when they are part of
    # the __init__ signature and when they aren't kw_only (which are moved to
    # the end and can be mandatory or non-mandatory in any order, as they will
    # be specified as keyword args anyway). Check the order of those attrs:
    had_default = False
    for a in (a for a in attrs if a.init is not False and a.kw_only is False):
        if had_default is True and a.default is NOTHING:
            raise ValueError(
                "No mandatory attributes allowed after an attribute with a "
                "default value or factory.  Attribute in question: %r" % (a,)
            )

        if had_default is False and a.default is not NOTHING:
            had_default = True

    return _Attributes((attrs, base_attrs, base_attr_map))


def _frozen_setattrs(self, name, value):
    """
    Attached to frozen classes as __setattr__.
    """
    raise FrozenInstanceError()


def _frozen_delattrs(self, name):
    """
    Attached to frozen classes as __delattr__.
    """
    raise FrozenInstanceError()


class _ClassBuilder(object):
    """
    Iteratively build *one* class.
    """

    __slots__ = (
        "_cls",
        "_cls_dict",
        "_attrs",
        "_base_names",
        "_attr_names",
        "_slots",
        "_frozen",
        "_weakref_slot",
        "_cache_hash",
        "_has_post_init",
        "_delete_attribs",
        "_base_attr_map",
        "_is_exc",
    )

    def __init__(
        self,
        cls,
        these,
        slots,
        frozen,
        weakref_slot,
        auto_attribs,
        kw_only,
        cache_hash,
        is_exc,
    ):
        attrs, base_attrs, base_map = _transform_attrs(
            cls, these, auto_attribs, kw_only
        )

        self._cls = cls
        self._cls_dict = dict(cls.__dict__) if slots else {}
        self._attrs = attrs
        self._base_names = set(a.name for a in base_attrs)
        self._base_attr_map = base_map
        self._attr_names = tuple(a.name for a in attrs)
        self._slots = slots
        self._frozen = frozen or _has_frozen_base_class(cls)
        self._weakref_slot = weakref_slot
        self._cache_hash = cache_hash
        self._has_post_init = bool(getattr(cls, "__attrs_post_init__", False))
        self._delete_attribs = not bool(these)
        self._is_exc = is_exc

        self._cls_dict["__attrs_attrs__"] = self._attrs

        if frozen:
            self._cls_dict["__setattr__"] = _frozen_setattrs
            self._cls_dict["__delattr__"] = _frozen_delattrs

    def __repr__(self):
        return "<_ClassBuilder(cls={cls})>".format(cls=self._cls.__name__)

    def build_class(self):
        """
        Finalize class based on the accumulated configuration.

        Builder cannot be used after calling this method.
        """
        if self._slots is True:
            return self._create_slots_class()
        else:
            return self._patch_original_class()

    def _patch_original_class(self):
        """
        Apply accumulated methods and return the class.
        """
        cls = self._cls
        base_names = self._base_names

        # Clean class of attribute definitions (`attr.ib()`s).
        if self._delete_attribs:
            for name in self._attr_names:
                if (
                    name not in base_names
                    and getattr(cls, name, _sentinel) is not _sentinel
                ):
                    try:
                        delattr(cls, name)
                    except AttributeError:
                        # This can happen if a base class defines a class
                        # variable and we want to set an attribute with the
                        # same name by using only a type annotation.
                        pass

        # Attach our dunder methods.
        for name, value in self._cls_dict.items():
            setattr(cls, name, value)

        # Attach __setstate__. This is necessary to clear the hash code
        # cache on deserialization. See issue
        # https://github.com/python-attrs/attrs/issues/482 .
        # Note that this code only handles setstate for dict classes.
        # For slotted classes, see similar code in _create_slots_class .
        if self._cache_hash:
            existing_set_state_method = getattr(cls, "__setstate__", None)
            if existing_set_state_method:
                raise NotImplementedError(
                    "Currently you cannot use hash caching if "
                    "you specify your own __setstate__ method."
                    "See https://github.com/python-attrs/attrs/issues/494 ."
                )

            def cache_hash_set_state(chss_self, _):
                # clear hash code cache
                setattr(chss_self, _hash_cache_field, None)

            setattr(cls, "__setstate__", cache_hash_set_state)

        return cls

    def _create_slots_class(self):
        """
        Build and return a new class with a `__slots__` attribute.
        """
        base_names = self._base_names
        cd = {
            k: v
            for k, v in iteritems(self._cls_dict)
            if k not in tuple(self._attr_names) + ("__dict__", "__weakref__")
        }

        weakref_inherited = False

        # Traverse the MRO to check for an existing __weakref__.
        for base_cls in self._cls.__mro__[1:-1]:
            if "__weakref__" in getattr(base_cls, "__dict__", ()):
                weakref_inherited = True
                break

        names = self._attr_names
        if (
            self._weakref_slot
            and "__weakref__" not in getattr(self._cls, "__slots__", ())
            and "__weakref__" not in names
            and not weakref_inherited
        ):
            names += ("__weakref__",)

        # We only add the names of attributes that aren't inherited.
        # Settings __slots__ to inherited attributes wastes memory.
        slot_names = [name for name in names if name not in base_names]
        if self._cache_hash:
            slot_names.append(_hash_cache_field)
        cd["__slots__"] = tuple(slot_names)

        qualname = getattr(self._cls, "__qualname__", None)
        if qualname is not None:
            cd["__qualname__"] = qualname

        # __weakref__ is not writable.
        state_attr_names = tuple(
            an for an in self._attr_names if an != "__weakref__"
        )

        def slots_getstate(self):
            """
            Automatically created by attrs.
            """
            return tuple(getattr(self, name) for name in state_attr_names)

        hash_caching_enabled = self._cache_hash

        def slots_setstate(self, state):
            """
            Automatically created by attrs.
            """
            __bound_setattr = _obj_setattr.__get__(self, Attribute)
            for name, value in zip(state_attr_names, state):
                __bound_setattr(name, value)
            # Clearing the hash code cache on deserialization is needed
            # because hash codes can change from run to run. See issue
            # https://github.com/python-attrs/attrs/issues/482 .
            # Note that this code only handles setstate for slotted classes.
            # For dict classes, see similar code in _patch_original_class .
            if hash_caching_enabled:
                __bound_setattr(_hash_cache_field, None)

        # slots and frozen require __getstate__/__setstate__ to work
        cd["__getstate__"] = slots_getstate
        cd["__setstate__"] = slots_setstate

        # Create new class based on old class and our methods.
        cls = type(self._cls)(self._cls.__name__, self._cls.__bases__, cd)

        # The following is a fix for
        # https://github.com/python-attrs/attrs/issues/102.  On Python 3,
        # if a method mentions `__class__` or uses the no-arg super(), the
        # compiler will bake a reference to the class in the method itself
        # as `method.__closure__`.  Since we replace the class with a
        # clone, we rewrite these references so it keeps working.
        for item in cls.__dict__.values():
            if isinstance(item, (classmethod, staticmethod)):
                # Class- and staticmethods hide their functions inside.
                # These might need to be rewritten as well.
                closure_cells = getattr(item.__func__, "__closure__", None)
            else:
                closure_cells = getattr(item, "__closure__", None)

            if not closure_cells:  # Catch None or the empty list.
                continue
            for cell in closure_cells:
                if cell.cell_contents is self._cls:
                    set_closure_cell(cell, cls)

        return cls

    def add_repr(self, ns):
        self._cls_dict["__repr__"] = self._add_method_dunders(
            _make_repr(self._attrs, ns=ns)
        )
        return self

    def add_str(self):
        repr = self._cls_dict.get("__repr__")
        if repr is None:
            raise ValueError(
                "__str__ can only be generated if a __repr__ exists."
            )

        def __str__(self):
            return self.__repr__()

        self._cls_dict["__str__"] = self._add_method_dunders(__str__)
        return self

    def make_unhashable(self):
        self._cls_dict["__hash__"] = None
        return self

    def add_hash(self):
        self._cls_dict["__hash__"] = self._add_method_dunders(
            _make_hash(
                self._cls,
                self._attrs,
                frozen=self._frozen,
                cache_hash=self._cache_hash,
            )
        )

        return self

    def add_init(self):
        self._cls_dict["__init__"] = self._add_method_dunders(
            _make_init(
                self._cls,
                self._attrs,
                self._has_post_init,
                self._frozen,
                self._slots,
                self._cache_hash,
                self._base_attr_map,
                self._is_exc,
            )
        )

        return self

    def add_eq(self):
        cd = self._cls_dict

        cd["__eq__"], cd["__ne__"] = (
            self._add_method_dunders(meth)
            for meth in _make_eq(self._cls, self._attrs)
        )

        return self

    def add_order(self):
        cd = self._cls_dict

        cd["__lt__"], cd["__le__"], cd["__gt__"], cd["__ge__"] = (
            self._add_method_dunders(meth)
            for meth in _make_order(self._cls, self._attrs)
        )

        return self

    def _add_method_dunders(self, method):
        """
        Add __module__ and __qualname__ to a *method* if possible.
        """
        try:
            method.__module__ = self._cls.__module__
        except AttributeError:
            pass

        try:
            method.__qualname__ = ".".join(
                (self._cls.__qualname__, method.__name__)
            )
        except AttributeError:
            pass

        return method


_CMP_DEPRECATION = (
    "The usage of `cmp` is deprecated and will be removed on or after "
    "2021-06-01.  Please use `eq` and `order` instead."
)


def _determine_eq_order(cmp, eq, order):
    """
    Validate the combination of *cmp*, *eq*, and *order*. Derive the effective
    values of eq and order.
    """
    if cmp is not None and any((eq is not None, order is not None)):
        raise ValueError("Don't mix `cmp` with `eq' and `order`.")

    # cmp takes precedence due to bw-compatibility.
    if cmp is not None:
        warnings.warn(_CMP_DEPRECATION, DeprecationWarning, stacklevel=3)

        return cmp, cmp

    # If left None, equality is on and ordering mirrors equality.
    if eq is None:
        eq = True

    if order is None:
        order = eq

    if eq is False and order is True:
        raise ValueError("`order` can only be True if `eq` is True too.")

    return eq, order


def attrs(
    maybe_cls=None,
    these=None,
    repr_ns=None,
    repr=True,
    cmp=None,
    hash=None,
    init=True,
    slots=False,
    frozen=False,
    weakref_slot=True,
    str=False,
    auto_attribs=False,
    kw_only=False,
    cache_hash=False,
    auto_exc=False,
    eq=None,
    order=None,
):
    r"""
    A class decorator that adds `dunder
    <https://wiki.python.org/moin/DunderAlias>`_\ -methods according to the
    specified attributes using `attr.ib` or the *these* argument.

    :param these: A dictionary of name to `attr.ib` mappings.  This is
        useful to avoid the definition of your attributes within the class body
        because you can't (e.g. if you want to add ``__repr__`` methods to
        Django models) or don't want to.

        If *these* is not ``None``, ``attrs`` will *not* search the class body
        for attributes and will *not* remove any attributes from it.

        If *these* is an ordered dict (`dict` on Python 3.6+,
        `collections.OrderedDict` otherwise), the order is deduced from
        the order of the attributes inside *these*.  Otherwise the order
        of the definition of the attributes is used.

    :type these: `dict` of `str` to `attr.ib`

    :param str repr_ns: When using nested classes, there's no way in Python 2
        to automatically detect that.  Therefore it's possible to set the
        namespace explicitly for a more meaningful ``repr`` output.
    :param bool repr: Create a ``__repr__`` method with a human readable
        representation of ``attrs`` attributes..
    :param bool str: Create a ``__str__`` method that is identical to
        ``__repr__``.  This is usually not necessary except for
        `Exception`\ s.
    :param bool eq: If ``True`` or ``None`` (default), add ``__eq__`` and
        ``__ne__`` methods that check two instances for equality.

        They compare the instances as if they were tuples of their ``attrs``
        attributes, but only iff the types of both classes are *identical*!
    :type eq: `bool` or `None`
    :param bool order: If ``True``, add ``__lt__``, ``__le__``, ``__gt__``,
        and ``__ge__`` methods that behave like *eq* above and allow instances
        to be ordered. If ``None`` (default) mirror value of *eq*.
    :type order: `bool` or `None`
    :param cmp: Setting to ``True`` is equivalent to setting ``eq=True,
        order=True``. Deprecated in favor of *eq* and *order*, has precedence
        over them for backward-compatibility though. Must not be mixed with
        *eq* or *order*.
    :type cmp: `bool` or `None`
    :param hash: If ``None`` (default), the ``__hash__`` method is generated
        according how *eq* and *frozen* are set.

        1. If *both* are True, ``attrs`` will generate a ``__hash__`` for you.
        2. If *eq* is True and *frozen* is False, ``__hash__`` will be set to
           None, marking it unhashable (which it is).
        3. If *eq* is False, ``__hash__`` will be left untouched meaning the
           ``__hash__`` method of the base class will be used (if base class is
           ``object``, this means it will fall back to id-based hashing.).

        Although not recommended, you can decide for yourself and force
        ``attrs`` to create one (e.g. if the class is immutable even though you
        didn't freeze it programmatically) by passing ``True`` or not.  Both of
        these cases are rather special and should be used carefully.

        See our documentation on `hashing`, Python's documentation on
        `object.__hash__`, and the `GitHub issue that led to the default \
        behavior <https://github.com/python-attrs/attrs/issues/136>`_ for more
        details.
    :type hash: ``bool`` or ``None``
    :param bool init: Create a ``__init__`` method that initializes the
        ``attrs`` attributes.  Leading underscores are stripped for the
        argument name.  If a ``__attrs_post_init__`` method exists on the
        class, it will be called after the class is fully initialized.
    :param bool slots: Create a `slotted class <slotted classes>` that's more
        memory-efficient.
    :param bool frozen: Make instances immutable after initialization.  If
        someone attempts to modify a frozen instance,
        `attr.exceptions.FrozenInstanceError` is raised.

        Please note:

            1. This is achieved by installing a custom ``__setattr__`` method
               on your class, so you can't implement your own.

            2. True immutability is impossible in Python.

            3. This *does* have a minor a runtime performance `impact
               <how-frozen>` when initializing new instances.  In other words:
               ``__init__`` is slightly slower with ``frozen=True``.

            4. If a class is frozen, you cannot modify ``self`` in
               ``__attrs_post_init__`` or a self-written ``__init__``. You can
               circumvent that limitation by using
               ``object.__setattr__(self, "attribute_name", value)``.

    :param bool weakref_slot: Make instances weak-referenceable.  This has no
        effect unless ``slots`` is also enabled.
    :param bool auto_attribs: If True, collect `PEP 526`_-annotated attributes
        (Python 3.6 and later only) from the class body.

        In this case, you **must** annotate every field.  If ``attrs``
        encounters a field that is set to an `attr.ib` but lacks a type
        annotation, an `attr.exceptions.UnannotatedAttributeError` is
        raised.  Use ``field_name: typing.Any = attr.ib(...)`` if you don't
        want to set a type.

        If you assign a value to those attributes (e.g. ``x: int = 42``), that
        value becomes the default value like if it were passed using
        ``attr.ib(default=42)``.  Passing an instance of `Factory` also
        works as expected.

        Attributes annotated as `typing.ClassVar`, and attributes that are
        neither annotated nor set to an `attr.ib` are **ignored**.

        .. _`PEP 526`: https://www.python.org/dev/peps/pep-0526/
    :param bool kw_only: Make all attributes keyword-only (Python 3+)
        in the generated ``__init__`` (if ``init`` is ``False``, this
        parameter is ignored).
    :param bool cache_hash: Ensure that the object's hash code is computed
        only once and stored on the object.  If this is set to ``True``,
        hashing must be either explicitly or implicitly enabled for this
        class.  If the hash code is cached, avoid any reassignments of
        fields involved in hash code computation or mutations of the objects
        those fields point to after object creation.  If such changes occur,
        the behavior of the object's hash code is undefined.
    :param bool auto_exc: If the class subclasses `BaseException`
        (which implicitly includes any subclass of any exception), the
        following happens to behave like a well-behaved Python exceptions
        class:

        - the values for *eq*, *order*, and *hash* are ignored and the
          instances compare and hash by the instance's ids (N.B. ``attrs`` will
          *not* remove existing implementations of ``__hash__`` or the equality
          methods. It just won't add own ones.),
        - all attributes that are either passed into ``__init__`` or have a
          default value are additionally available as a tuple in the ``args``
          attribute,
        - the value of *str* is ignored leaving ``__str__`` to base classes.

    .. versionadded:: 16.0.0 *slots*
    .. versionadded:: 16.1.0 *frozen*
    .. versionadded:: 16.3.0 *str*
    .. versionadded:: 16.3.0 Support for ``__attrs_post_init__``.
    .. versionchanged:: 17.1.0
       *hash* supports ``None`` as value which is also the default now.
    .. versionadded:: 17.3.0 *auto_attribs*
    .. versionchanged:: 18.1.0
       If *these* is passed, no attributes are deleted from the class body.
    .. versionchanged:: 18.1.0 If *these* is ordered, the order is retained.
    .. versionadded:: 18.2.0 *weakref_slot*
    .. deprecated:: 18.2.0
       ``__lt__``, ``__le__``, ``__gt__``, and ``__ge__`` now raise a
       `DeprecationWarning` if the classes compared are subclasses of
       each other. ``__eq`` and ``__ne__`` never tried to compared subclasses
       to each other.
    .. versionchanged:: 19.2.0
       ``__lt__``, ``__le__``, ``__gt__``, and ``__ge__`` now do not consider
       subclasses comparable anymore.
    .. versionadded:: 18.2.0 *kw_only*
    .. versionadded:: 18.2.0 *cache_hash*
    .. versionadded:: 19.1.0 *auto_exc*
    .. deprecated:: 19.2.0 *cmp* Removal on or after 2021-06-01.
    .. versionadded:: 19.2.0 *eq* and *order*
    """
    eq, order = _determine_eq_order(cmp, eq, order)

    def wrap(cls):

        if getattr(cls, "__class__", None) is None:
            raise TypeError("attrs only works with new-style classes.")

        is_exc = auto_exc is True and issubclass(cls, BaseException)

        builder = _ClassBuilder(
            cls,
            these,
            slots,
            frozen,
            weakref_slot,
            auto_attribs,
            kw_only,
            cache_hash,
            is_exc,
        )

        if repr is True:
            builder.add_repr(repr_ns)
        if str is True:
            builder.add_str()
        if eq is True and not is_exc:
            builder.add_eq()
        if order is True and not is_exc:
            builder.add_order()

        if hash is not True and hash is not False and hash is not None:
            # Can't use `hash in` because 1 == True for example.
            raise TypeError(
                "Invalid value for hash.  Must be True, False, or None."
            )
        elif hash is False or (hash is None and eq is False) or is_exc:
            # Don't do anything. Should fall back to __object__'s __hash__
            # which is by id.
            if cache_hash:
                raise TypeError(
                    "Invalid value for cache_hash.  To use hash caching,"
                    " hashing must be either explicitly or implicitly "
                    "enabled."
                )
        elif hash is True or (hash is None and eq is True and frozen is True):
            # Build a __hash__ if told so, or if it's safe.
            builder.add_hash()
        else:
            # Raise TypeError on attempts to hash.
            if cache_hash:
                raise TypeError(
                    "Invalid value for cache_hash.  To use hash caching,"
                    " hashing must be either explicitly or implicitly "
                    "enabled."
                )
            builder.make_unhashable()

        if init is True:
            builder.add_init()
        else:
            if cache_hash:
                raise TypeError(
                    "Invalid value for cache_hash.  To use hash caching,"
                    " init must be True."
                )

        return builder.build_class()

    # maybe_cls's type depends on the usage of the decorator.  It's a class
    # if it's used as `@attrs` but ``None`` if used as `@attrs()`.
    if maybe_cls is None:
        return wrap
    else:
        return wrap(maybe_cls)


_attrs = attrs
"""
Internal alias so we can use it in functions that take an argument called
*attrs*.
"""


if PY2:

    def _has_frozen_base_class(cls):
        """
        Check whether *cls* has a frozen ancestor by looking at its
        __setattr__.
        """
        return (
            getattr(cls.__setattr__, "__module__", None)
            == _frozen_setattrs.__module__
            and cls.__setattr__.__name__ == _frozen_setattrs.__name__
        )


else:

    def _has_frozen_base_class(cls):
        """
        Check whether *cls* has a frozen ancestor by looking at its
        __setattr__.
        """
        return cls.__setattr__ == _frozen_setattrs


def _attrs_to_tuple(obj, attrs):
    """
    Create a tuple of all values of *obj*'s *attrs*.
    """
    return tuple(getattr(obj, a.name) for a in attrs)


def _generate_unique_filename(cls, func_name):
    """
    Create a "filename" suitable for a function being generated.
    """
    unique_id = uuid.uuid4()
    extra = ""
    count = 1

    while True:
        unique_filename = "<attrs generated {0} {1}.{2}{3}>".format(
            func_name,
            cls.__module__,
            getattr(cls, "__qualname__", cls.__name__),
            extra,
        )
        # To handle concurrency we essentially "reserve" our spot in
        # the linecache with a dummy line.  The caller can then
        # set this value correctly.
        cache_line = (1, None, (str(unique_id),), unique_filename)
        if (
            linecache.cache.setdefault(unique_filename, cache_line)
            == cache_line
        ):
            return unique_filename

        # Looks like this spot is taken. Try again.
        count += 1
        extra = "-{0}".format(count)


def _make_hash(cls, attrs, frozen, cache_hash):
    attrs = tuple(
        a for a in attrs if a.hash is True or (a.hash is None and a.eq is True)
    )

    tab = "        "

    unique_filename = _generate_unique_filename(cls, "hash")
    type_hash = hash(unique_filename)

    method_lines = ["def __hash__(self):"]

    def append_hash_computation_lines(prefix, indent):
        """
        Generate the code for actually computing the hash code.
        Below this will either be returned directly or used to compute
        a value which is then cached, depending on the value of cache_hash
        """
        method_lines.extend(
            [indent + prefix + "hash((", indent + "        %d," % (type_hash,)]
        )

        for a in attrs:
            method_lines.append(indent + "        self.%s," % a.name)

        method_lines.append(indent + "    ))")

    if cache_hash:
        method_lines.append(tab + "if self.%s is None:" % _hash_cache_field)
        if frozen:
            append_hash_computation_lines(
                "object.__setattr__(self, '%s', " % _hash_cache_field, tab * 2
            )
            method_lines.append(tab * 2 + ")")  # close __setattr__
        else:
            append_hash_computation_lines(
                "self.%s = " % _hash_cache_field, tab * 2
            )
        method_lines.append(tab + "return self.%s" % _hash_cache_field)
    else:
        append_hash_computation_lines("return ", tab)

    script = "\n".join(method_lines)
    globs = {}
    locs = {}
    bytecode = compile(script, unique_filename, "exec")
    eval(bytecode, globs, locs)

    # In order of debuggers like PDB being able to step through the code,
    # we add a fake linecache entry.
    linecache.cache[unique_filename] = (
        len(script),
        None,
        script.splitlines(True),
        unique_filename,
    )

    return locs["__hash__"]


def _add_hash(cls, attrs):
    """
    Add a hash method to *cls*.
    """
    cls.__hash__ = _make_hash(cls, attrs, frozen=False, cache_hash=False)
    return cls


def __ne__(self, other):
    """
    Check equality and either forward a NotImplemented or return the result
    negated.
    """
    result = self.__eq__(other)
    if result is NotImplemented:
        return NotImplemented

    return not result


def _make_eq(cls, attrs):
    attrs = [a for a in attrs if a.eq]

    unique_filename = _generate_unique_filename(cls, "eq")
    lines = [
        "def __eq__(self, other):",
        "    if other.__class__ is not self.__class__:",
        "        return NotImplemented",
    ]
    # We can't just do a big self.x = other.x and... clause due to
    # irregularities like nan == nan is false but (nan,) == (nan,) is true.
    if attrs:
        lines.append("    return  (")
        others = ["    ) == ("]
        for a in attrs:
            lines.append("        self.%s," % (a.name,))
            others.append("        other.%s," % (a.name,))

        lines += others + ["    )"]
    else:
        lines.append("    return True")

    script = "\n".join(lines)
    globs = {}
    locs = {}
    bytecode = compile(script, unique_filename, "exec")
    eval(bytecode, globs, locs)

    # In order of debuggers like PDB being able to step through the code,
    # we add a fake linecache entry.
    linecache.cache[unique_filename] = (
        len(script),
        None,
        script.splitlines(True),
        unique_filename,
    )
    return locs["__eq__"], __ne__


def _make_order(cls, attrs):
    attrs = [a for a in attrs if a.order]

    def attrs_to_tuple(obj):
        """
        Save us some typing.
        """
        return _attrs_to_tuple(obj, attrs)

    def __lt__(self, other):
        """
        Automatically created by attrs.
        """
        if other.__class__ is self.__class__:
            return attrs_to_tuple(self) < attrs_to_tuple(other)

        return NotImplemented

    def __le__(self, other):
        """
        Automatically created by attrs.
        """
        if other.__class__ is self.__class__:
            return attrs_to_tuple(self) <= attrs_to_tuple(other)

        return NotImplemented

    def __gt__(self, other):
        """
        Automatically created by attrs.
        """
        if other.__class__ is self.__class__:
            return attrs_to_tuple(self) > attrs_to_tuple(other)

        return NotImplemented

    def __ge__(self, other):
        """
        Automatically created by attrs.
        """
        if other.__class__ is self.__class__:
            return attrs_to_tuple(self) >= attrs_to_tuple(other)

        return NotImplemented

    return __lt__, __le__, __gt__, __ge__


def _add_eq(cls, attrs=None):
    """
    Add equality methods to *cls* with *attrs*.
    """
    if attrs is None:
        attrs = cls.__attrs_attrs__

    cls.__eq__, cls.__ne__ = _make_eq(cls, attrs)

    return cls


_already_repring = threading.local()


def _make_repr(attrs, ns):
    """
    Make a repr method that includes relevant *attrs*, adding *ns* to the full
    name.
    """

    # Figure out which attributes to include, and which function to use to
    # format them. The a.repr value can be either bool or a custom callable.
    attr_names_with_reprs = tuple(
        (a.name, repr if a.repr is True else a.repr)
        for a in attrs
        if a.repr is not False
    )

    def __repr__(self):
        """
        Automatically created by attrs.
        """
        try:
            working_set = _already_repring.working_set
        except AttributeError:
            working_set = set()
            _already_repring.working_set = working_set

        if id(self) in working_set:
            return "..."
        real_cls = self.__class__
        if ns is None:
            qualname = getattr(real_cls, "__qualname__", None)
            if qualname is not None:
                class_name = qualname.rsplit(">.", 1)[-1]
            else:
                class_name = real_cls.__name__
        else:
            class_name = ns + "." + real_cls.__name__

        # Since 'self' remains on the stack (i.e.: strongly referenced) for the
        # duration of this call, it's safe to depend on id(...) stability, and
        # not need to track the instance and therefore worry about properties
        # like weakref- or hash-ability.
        working_set.add(id(self))
        try:
            result = [class_name, "("]
            first = True
            for name, attr_repr in attr_names_with_reprs:
                if first:
                    first = False
                else:
                    result.append(", ")
                result.extend(
                    (name, "=", attr_repr(getattr(self, name, NOTHING)))
                )
            return "".join(result) + ")"
        finally:
            working_set.remove(id(self))

    return __repr__


def _add_repr(cls, ns=None, attrs=None):
    """
    Add a repr method to *cls*.
    """
    if attrs is None:
        attrs = cls.__attrs_attrs__

    cls.__repr__ = _make_repr(attrs, ns)
    return cls


def _make_init(
    cls, attrs, post_init, frozen, slots, cache_hash, base_attr_map, is_exc
):
    attrs = [a for a in attrs if a.init or a.default is not NOTHING]

    unique_filename = _generate_unique_filename(cls, "init")

    script, globs, annotations = _attrs_to_init_script(
        attrs, frozen, slots, post_init, cache_hash, base_attr_map, is_exc
    )
    locs = {}
    bytecode = compile(script, unique_filename, "exec")
    attr_dict = dict((a.name, a) for a in attrs)
    globs.update({"NOTHING": NOTHING, "attr_dict": attr_dict})

    if frozen is True:
        # Save the lookup overhead in __init__ if we need to circumvent
        # immutability.
        globs["_cached_setattr"] = _obj_setattr

    eval(bytecode, globs, locs)

    # In order of debuggers like PDB being able to step through the code,
    # we add a fake linecache entry.
    linecache.cache[unique_filename] = (
        len(script),
        None,
        script.splitlines(True),
        unique_filename,
    )

    __init__ = locs["__init__"]
    __init__.__annotations__ = annotations

    return __init__


def fields(cls):
    """
    Return the tuple of ``attrs`` attributes for a class.

    The tuple also allows accessing the fields by their names (see below for
    examples).

    :param type cls: Class to introspect.

    :raise TypeError: If *cls* is not a class.
    :raise attr.exceptions.NotAnAttrsClassError: If *cls* is not an ``attrs``
        class.

    :rtype: tuple (with name accessors) of `attr.Attribute`

    ..  versionchanged:: 16.2.0 Returned tuple allows accessing the fields
        by name.
    """
    if not isclass(cls):
        raise TypeError("Passed object must be a class.")
    attrs = getattr(cls, "__attrs_attrs__", None)
    if attrs is None:
        raise NotAnAttrsClassError(
            "{cls!r} is not an attrs-decorated class.".format(cls=cls)
        )
    return attrs


def fields_dict(cls):
    """
    Return an ordered dictionary of ``attrs`` attributes for a class, whose
    keys are the attribute names.

    :param type cls: Class to introspect.

    :raise TypeError: If *cls* is not a class.
    :raise attr.exceptions.NotAnAttrsClassError: If *cls* is not an ``attrs``
        class.

    :rtype: an ordered dict where keys are attribute names and values are
        `attr.Attribute`\\ s. This will be a `dict` if it's
        naturally ordered like on Python 3.6+ or an
        :class:`~collections.OrderedDict` otherwise.

    .. versionadded:: 18.1.0
    """
    if not isclass(cls):
        raise TypeError("Passed object must be a class.")
    attrs = getattr(cls, "__attrs_attrs__", None)
    if attrs is None:
        raise NotAnAttrsClassError(
            "{cls!r} is not an attrs-decorated class.".format(cls=cls)
        )
    return ordered_dict(((a.name, a) for a in attrs))


def validate(inst):
    """
    Validate all attributes on *inst* that have a validator.

    Leaves all exceptions through.

    :param inst: Instance of a class with ``attrs`` attributes.
    """
    if _config._run_validators is False:
        return

    for a in fields(inst.__class__):
        v = a.validator
        if v is not None:
            v(inst, a, getattr(inst, a.name))


def _is_slot_cls(cls):
    return "__slots__" in cls.__dict__


def _is_slot_attr(a_name, base_attr_map):
    """
    Check if the attribute name comes from a slot class.
    """
    return a_name in base_attr_map and _is_slot_cls(base_attr_map[a_name])


def _attrs_to_init_script(
    attrs, frozen, slots, post_init, cache_hash, base_attr_map, is_exc
):
    """
    Return a script of an initializer for *attrs* and a dict of globals.

    The globals are expected by the generated script.

    If *frozen* is True, we cannot set the attributes directly so we use
    a cached ``object.__setattr__``.
    """
    lines = []
    any_slot_ancestors = any(
        _is_slot_attr(a.name, base_attr_map) for a in attrs
    )
    if frozen is True:
        if slots is True:
            lines.append(
                # Circumvent the __setattr__ descriptor to save one lookup per
                # assignment.
                # Note _setattr will be used again below if cache_hash is True
                "_setattr = _cached_setattr.__get__(self, self.__class__)"
            )

            def fmt_setter(attr_name, value_var):
                return "_setattr('%(attr_name)s', %(value_var)s)" % {
                    "attr_name": attr_name,
                    "value_var": value_var,
                }

            def fmt_setter_with_converter(attr_name, value_var):
                conv_name = _init_converter_pat.format(attr_name)
                return "_setattr('%(attr_name)s', %(conv)s(%(value_var)s))" % {
                    "attr_name": attr_name,
                    "value_var": value_var,
                    "conv": conv_name,
                }

        else:
            # Dict frozen classes assign directly to __dict__.
            # But only if the attribute doesn't come from an ancestor slot
            # class.
            # Note _inst_dict will be used again below if cache_hash is True
            lines.append("_inst_dict = self.__dict__")
            if any_slot_ancestors:
                lines.append(
                    # Circumvent the __setattr__ descriptor to save one lookup
                    # per assignment.
                    "_setattr = _cached_setattr.__get__(self, self.__class__)"
                )

            def fmt_setter(attr_name, value_var):
                if _is_slot_attr(attr_name, base_attr_map):
                    res = "_setattr('%(attr_name)s', %(value_var)s)" % {
                        "attr_name": attr_name,
                        "value_var": value_var,
                    }
                else:
                    res = "_inst_dict['%(attr_name)s'] = %(value_var)s" % {
                        "attr_name": attr_name,
                        "value_var": value_var,
                    }
                return res

            def fmt_setter_with_converter(attr_name, value_var):
                conv_name = _init_converter_pat.format(attr_name)
                if _is_slot_attr(attr_name, base_attr_map):
                    tmpl = "_setattr('%(attr_name)s', %(c)s(%(value_var)s))"
                else:
                    tmpl = "_inst_dict['%(attr_name)s'] = %(c)s(%(value_var)s)"
                return tmpl % {
                    "attr_name": attr_name,
                    "value_var": value_var,
                    "c": conv_name,
                }

    else:
        # Not frozen.
        def fmt_setter(attr_name, value):
            return "self.%(attr_name)s = %(value)s" % {
                "attr_name": attr_name,
                "value": value,
            }

        def fmt_setter_with_converter(attr_name, value_var):
            conv_name = _init_converter_pat.format(attr_name)
            return "self.%(attr_name)s = %(conv)s(%(value_var)s)" % {
                "attr_name": attr_name,
                "value_var": value_var,
                "conv": conv_name,
            }

    args = []
    kw_only_args = []
    attrs_to_validate = []

    # This is a dictionary of names to validator and converter callables.
    # Injecting this into __init__ globals lets us avoid lookups.
    names_for_globals = {}
    annotations = {"return": None}

    for a in attrs:
        if a.validator:
            attrs_to_validate.append(a)
        attr_name = a.name
        arg_name = a.name.lstrip("_")
        has_factory = isinstance(a.default, Factory)
        if has_factory and a.default.takes_self:
            maybe_self = "self"
        else:
            maybe_self = ""
        if a.init is False:
            if has_factory:
                init_factory_name = _init_factory_pat.format(a.name)
                if a.converter is not None:
                    lines.append(
                        fmt_setter_with_converter(
                            attr_name,
                            init_factory_name + "({0})".format(maybe_self),
                        )
                    )
                    conv_name = _init_converter_pat.format(a.name)
                    names_for_globals[conv_name] = a.converter
                else:
                    lines.append(
                        fmt_setter(
                            attr_name,
                            init_factory_name + "({0})".format(maybe_self),
                        )
                    )
                names_for_globals[init_factory_name] = a.default.factory
            else:
                if a.converter is not None:
                    lines.append(
                        fmt_setter_with_converter(
                            attr_name,
                            "attr_dict['{attr_name}'].default".format(
                                attr_name=attr_name
                            ),
                        )
                    )
                    conv_name = _init_converter_pat.format(a.name)
                    names_for_globals[conv_name] = a.converter
                else:
                    lines.append(
                        fmt_setter(
                            attr_name,
                            "attr_dict['{attr_name}'].default".format(
                                attr_name=attr_name
                            ),
                        )
                    )
        elif a.default is not NOTHING and not has_factory:
            arg = "{arg_name}=attr_dict['{attr_name}'].default".format(
                arg_name=arg_name, attr_name=attr_name
            )
            if a.kw_only:
                kw_only_args.append(arg)
            else:
                args.append(arg)
            if a.converter is not None:
                lines.append(fmt_setter_with_converter(attr_name, arg_name))
                names_for_globals[
                    _init_converter_pat.format(a.name)
                ] = a.converter
            else:
                lines.append(fmt_setter(attr_name, arg_name))
        elif has_factory:
            arg = "{arg_name}=NOTHING".format(arg_name=arg_name)
            if a.kw_only:
                kw_only_args.append(arg)
            else:
                args.append(arg)
            lines.append(
                "if {arg_name} is not NOTHING:".format(arg_name=arg_name)
            )
            init_factory_name = _init_factory_pat.format(a.name)
            if a.converter is not None:
                lines.append(
                    "    " + fmt_setter_with_converter(attr_name, arg_name)
                )
                lines.append("else:")
                lines.append(
                    "    "
                    + fmt_setter_with_converter(
                        attr_name,
                        init_factory_name + "({0})".format(maybe_self),
                    )
                )
                names_for_globals[
                    _init_converter_pat.format(a.name)
                ] = a.converter
            else:
                lines.append("    " + fmt_setter(attr_name, arg_name))
                lines.append("else:")
                lines.append(
                    "    "
                    + fmt_setter(
                        attr_name,
                        init_factory_name + "({0})".format(maybe_self),
                    )
                )
            names_for_globals[init_factory_name] = a.default.factory
        else:
            if a.kw_only:
                kw_only_args.append(arg_name)
            else:
                args.append(arg_name)
            if a.converter is not None:
                lines.append(fmt_setter_with_converter(attr_name, arg_name))
                names_for_globals[
                    _init_converter_pat.format(a.name)
                ] = a.converter
            else:
                lines.append(fmt_setter(attr_name, arg_name))

        if a.init is True and a.converter is None and a.type is not None:
            annotations[arg_name] = a.type

    if attrs_to_validate:  # we can skip this if there are no validators.
        names_for_globals["_config"] = _config
        lines.append("if _config._run_validators is True:")
        for a in attrs_to_validate:
            val_name = "__attr_validator_{}".format(a.name)
            attr_name = "__attr_{}".format(a.name)
            lines.append(
                "    {}(self, {}, self.{})".format(val_name, attr_name, a.name)
            )
            names_for_globals[val_name] = a.validator
            names_for_globals[attr_name] = a
    if post_init:
        lines.append("self.__attrs_post_init__()")

    # because this is set only after __attrs_post_init is called, a crash
    # will result if post-init tries to access the hash code.  This seemed
    # preferable to setting this beforehand, in which case alteration to
    # field values during post-init combined with post-init accessing the
    # hash code would result in silent bugs.
    if cache_hash:
        if frozen:
            if slots:
                # if frozen and slots, then _setattr defined above
                init_hash_cache = "_setattr('%s', %s)"
            else:
                # if frozen and not slots, then _inst_dict defined above
                init_hash_cache = "_inst_dict['%s'] = %s"
        else:
            init_hash_cache = "self.%s = %s"
        lines.append(init_hash_cache % (_hash_cache_field, "None"))

    # For exceptions we rely on BaseException.__init__ for proper
    # initialization.
    if is_exc:
        vals = ",".join("self." + a.name for a in attrs if a.init)

        lines.append("BaseException.__init__(self, %s)" % (vals,))

    args = ", ".join(args)
    if kw_only_args:
        if PY2:
            raise PythonTooOldError(
                "Keyword-only arguments only work on Python 3 and later."
            )

        args += "{leading_comma}*, {kw_only_args}".format(
            leading_comma=", " if args else "",
            kw_only_args=", ".join(kw_only_args),
        )
    return (
        """\
def __init__(self, {args}):
    {lines}
""".format(
            args=args, lines="\n    ".join(lines) if lines else "pass"
        ),
        names_for_globals,
        annotations,
    )


class Attribute(object):
    """
    *Read-only* representation of an attribute.

    :attribute name: The name of the attribute.

    Plus *all* arguments of `attr.ib` (except for ``factory``
    which is only syntactic sugar for ``default=Factory(...)``.

    For the version history of the fields, see `attr.ib`.
    """

    __slots__ = (
        "name",
        "default",
        "validator",
        "repr",
        "eq",
        "order",
        "hash",
        "init",
        "metadata",
        "type",
        "converter",
        "kw_only",
    )

    def __init__(
        self,
        name,
        default,
        validator,
        repr,
        cmp,  # XXX: unused, remove along with other cmp code.
        hash,
        init,
        metadata=None,
        type=None,
        converter=None,
        kw_only=False,
        eq=None,
        order=None,
    ):
        eq, order = _determine_eq_order(cmp, eq, order)

        # Cache this descriptor here to speed things up later.
        bound_setattr = _obj_setattr.__get__(self, Attribute)

        # Despite the big red warning, people *do* instantiate `Attribute`
        # themselves.
        bound_setattr("name", name)
        bound_setattr("default", default)
        bound_setattr("validator", validator)
        bound_setattr("repr", repr)
        bound_setattr("eq", eq)
        bound_setattr("order", order)
        bound_setattr("hash", hash)
        bound_setattr("init", init)
        bound_setattr("converter", converter)
        bound_setattr(
            "metadata",
            (
                metadata_proxy(metadata)
                if metadata
                else _empty_metadata_singleton
            ),
        )
        bound_setattr("type", type)
        bound_setattr("kw_only", kw_only)

    def __setattr__(self, name, value):
        raise FrozenInstanceError()

    @classmethod
    def from_counting_attr(cls, name, ca, type=None):
        # type holds the annotated value. deal with conflicts:
        if type is None:
            type = ca.type
        elif ca.type is not None:
            raise ValueError(
                "Type annotation and type argument cannot both be present"
            )
        inst_dict = {
            k: getattr(ca, k)
            for k in Attribute.__slots__
            if k
            not in (
                "name",
                "validator",
                "default",
                "type",
            )  # exclude methods and deprecated alias
        }
        return cls(
            name=name,
            validator=ca._validator,
            default=ca._default,
            type=type,
            cmp=None,
            **inst_dict
        )

    @property
    def cmp(self):
        """
        Simulate the presence of a cmp attribute and warn.
        """
        warnings.warn(_CMP_DEPRECATION, DeprecationWarning, stacklevel=2)

        return self.eq and self.order

    # Don't use attr.assoc since fields(Attribute) doesn't work
    def _assoc(self, **changes):
        """
        Copy *self* and apply *changes*.
        """
        new = copy.copy(self)

        new._setattrs(changes.items())

        return new

    # Don't use _add_pickle since fields(Attribute) doesn't work
    def __getstate__(self):
        """
        Play nice with pickle.
        """
        return tuple(
            getattr(self, name) if name != "metadata" else dict(self.metadata)
            for name in self.__slots__
        )

    def __setstate__(self, state):
        """
        Play nice with pickle.
        """
        self._setattrs(zip(self.__slots__, state))

    def _setattrs(self, name_values_pairs):
        bound_setattr = _obj_setattr.__get__(self, Attribute)
        for name, value in name_values_pairs:
            if name != "metadata":
                bound_setattr(name, value)
            else:
                bound_setattr(
                    name,
                    metadata_proxy(value)
                    if value
                    else _empty_metadata_singleton,
                )


_a = [
    Attribute(
        name=name,
        default=NOTHING,
        validator=None,
        repr=True,
        cmp=None,
        eq=True,
        order=False,
        hash=(name != "metadata"),
        init=True,
    )
    for name in Attribute.__slots__
]

Attribute = _add_hash(
    _add_eq(_add_repr(Attribute, attrs=_a), attrs=_a),
    attrs=[a for a in _a if a.hash],
)


class _CountingAttr(object):
    """
    Intermediate representation of attributes that uses a counter to preserve
    the order in which the attributes have been defined.

    *Internal* data structure of the attrs library.  Running into is most
    likely the result of a bug like a forgotten `@attr.s` decorator.
    """

    __slots__ = (
        "counter",
        "_default",
        "repr",
        "eq",
        "order",
        "hash",
        "init",
        "metadata",
        "_validator",
        "converter",
        "type",
        "kw_only",
    )
    __attrs_attrs__ = tuple(
        Attribute(
            name=name,
            default=NOTHING,
            validator=None,
            repr=True,
            cmp=None,
            hash=True,
            init=True,
            kw_only=False,
            eq=True,
            order=False,
        )
        for name in (
            "counter",
            "_default",
            "repr",
            "eq",
            "order",
            "hash",
            "init",
        )
    ) + (
        Attribute(
            name="metadata",
            default=None,
            validator=None,
            repr=True,
            cmp=None,
            hash=False,
            init=True,
            kw_only=False,
            eq=True,
            order=False,
        ),
    )
    cls_counter = 0

    def __init__(
        self,
        default,
        validator,
        repr,
        cmp,  # XXX: unused, remove along with cmp
        hash,
        init,
        converter,
        metadata,
        type,
        kw_only,
        eq,
        order,
    ):
        _CountingAttr.cls_counter += 1
        self.counter = _CountingAttr.cls_counter
        self._default = default
        # If validator is a list/tuple, wrap it using helper validator.
        if validator and isinstance(validator, (list, tuple)):
            self._validator = and_(*validator)
        else:
            self._validator = validator
        self.repr = repr
        self.eq = eq
        self.order = order
        self.hash = hash
        self.init = init
        self.converter = converter
        self.metadata = metadata
        self.type = type
        self.kw_only = kw_only

    def validator(self, meth):
        """
        Decorator that adds *meth* to the list of validators.

        Returns *meth* unchanged.

        .. versionadded:: 17.1.0
        """
        if self._validator is None:
            self._validator = meth
        else:
            self._validator = and_(self._validator, meth)
        return meth

    def default(self, meth):
        """
        Decorator that allows to set the default for an attribute.

        Returns *meth* unchanged.

        :raises DefaultAlreadySetError: If default has been set before.

        .. versionadded:: 17.1.0
        """
        if self._default is not NOTHING:
            raise DefaultAlreadySetError()

        self._default = Factory(meth, takes_self=True)

        return meth


_CountingAttr = _add_eq(_add_repr(_CountingAttr))


@attrs(slots=True, init=False, hash=True)
class Factory(object):
    """
    Stores a factory callable.

    If passed as the default value to `attr.ib`, the factory is used to
    generate a new value.

    :param callable factory: A callable that takes either none or exactly one
        mandatory positional argument depending on *takes_self*.
    :param bool takes_self: Pass the partially initialized instance that is
        being initialized as a positional argument.

    .. versionadded:: 17.1.0  *takes_self*
    """

    factory = attrib()
    takes_self = attrib()

    def __init__(self, factory, takes_self=False):
        """
        `Factory` is part of the default machinery so if we want a default
        value here, we have to implement it ourselves.
        """
        self.factory = factory
        self.takes_self = takes_self


def make_class(name, attrs, bases=(object,), **attributes_arguments):
    """
    A quick way to create a new class called *name* with *attrs*.

    :param name: The name for the new class.
    :type name: str

    :param attrs: A list of names or a dictionary of mappings of names to
        attributes.

        If *attrs* is a list or an ordered dict (`dict` on Python 3.6+,
        `collections.OrderedDict` otherwise), the order is deduced from
        the order of the names or attributes inside *attrs*.  Otherwise the
        order of the definition of the attributes is used.
    :type attrs: `list` or `dict`

    :param tuple bases: Classes that the new class will subclass.

    :param attributes_arguments: Passed unmodified to `attr.s`.

    :return: A new class with *attrs*.
    :rtype: type

    .. versionadded:: 17.1.0 *bases*
    .. versionchanged:: 18.1.0 If *attrs* is ordered, the order is retained.
    """
    if isinstance(attrs, dict):
        cls_dict = attrs
    elif isinstance(attrs, (list, tuple)):
        cls_dict = dict((a, attrib()) for a in attrs)
    else:
        raise TypeError("attrs argument must be a dict or a list.")

    post_init = cls_dict.pop("__attrs_post_init__", None)
    type_ = type(
        name,
        bases,
        {} if post_init is None else {"__attrs_post_init__": post_init},
    )
    # For pickling to work, the __module__ variable needs to be set to the
    # frame where the class is created.  Bypass this step in environments where
    # sys._getframe is not defined (Jython for example) or sys._getframe is not
    # defined for arguments greater than 0 (IronPython).
    try:
        type_.__module__ = sys._getframe(1).f_globals.get(
            "__name__", "__main__"
        )
    except (AttributeError, ValueError):
        pass

    # We do it here for proper warnings with meaningful stacklevel.
    cmp = attributes_arguments.pop("cmp", None)
    attributes_arguments["eq"], attributes_arguments[
        "order"
    ] = _determine_eq_order(
        cmp, attributes_arguments.get("eq"), attributes_arguments.get("order")
    )

    return _attrs(these=cls_dict, **attributes_arguments)(type_)


# These are required by within this module so we define them here and merely
# import into .validators.


@attrs(slots=True, hash=True)
class _AndValidator(object):
    """
    Compose many validators to a single one.
    """

    _validators = attrib()

    def __call__(self, inst, attr, value):
        for v in self._validators:
            v(inst, attr, value)


def and_(*validators):
    """
    A validator that composes multiple validators into one.

    When called on a value, it runs all wrapped validators.

    :param validators: Arbitrary number of validators.
    :type validators: callables

    .. versionadded:: 17.1.0
    """
    vals = []
    for validator in validators:
        vals.extend(
            validator._validators
            if isinstance(validator, _AndValidator)
            else [validator]
        )

    return _AndValidator(tuple(vals))
