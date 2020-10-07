# -*- coding: utf-8 -*-
# Copyright (c) 2012-2015 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2013-2014 Google, Inc.
# Copyright (c) 2014-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Eevee (Alex Munroe) <amunroe@yelp.com>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2015 Dmitry Pribysh <dmand@yandex.ru>
# Copyright (c) 2015 David Shea <dshea@redhat.com>
# Copyright (c) 2015 Philip Lorenz <philip@bithub.de>
# Copyright (c) 2016 Jakub Wilk <jwilk@jwilk.net>
# Copyright (c) 2016 Mateusz Bysiek <mb@mbdev.pl>
# Copyright (c) 2017 Hugo <hugovk@users.noreply.github.com>
# Copyright (c) 2017 Łukasz Rogalski <rogalski.91@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

"""Astroid hooks for the Python standard library."""

import functools
import keyword
from textwrap import dedent

from astroid import MANAGER, UseInferenceDefault, inference_tip, InferenceError
from astroid import arguments
from astroid import exceptions
from astroid import nodes
from astroid.builder import AstroidBuilder, extract_node
from astroid import util


TYPING_NAMEDTUPLE_BASENAMES = {"NamedTuple", "typing.NamedTuple"}
ENUM_BASE_NAMES = {
    "Enum",
    "IntEnum",
    "enum.Enum",
    "enum.IntEnum",
    "IntFlag",
    "enum.IntFlag",
}


def _infer_first(node, context):
    if node is util.Uninferable:
        raise UseInferenceDefault
    try:
        value = next(node.infer(context=context))
        if value is util.Uninferable:
            raise UseInferenceDefault()
        else:
            return value
    except StopIteration:
        raise InferenceError()


def _find_func_form_arguments(node, context):
    def _extract_namedtuple_arg_or_keyword(position, key_name=None):

        if len(args) > position:
            return _infer_first(args[position], context)
        if key_name and key_name in found_keywords:
            return _infer_first(found_keywords[key_name], context)

    args = node.args
    keywords = node.keywords
    found_keywords = (
        {keyword.arg: keyword.value for keyword in keywords} if keywords else {}
    )

    name = _extract_namedtuple_arg_or_keyword(position=0, key_name="typename")
    names = _extract_namedtuple_arg_or_keyword(position=1, key_name="field_names")
    if name and names:
        return name.value, names

    raise UseInferenceDefault()


def infer_func_form(node, base_type, context=None, enum=False):
    """Specific inference function for namedtuple or Python 3 enum. """
    # node is a Call node, class name as first argument and generated class
    # attributes as second argument

    # namedtuple or enums list of attributes can be a list of strings or a
    # whitespace-separate string
    try:
        name, names = _find_func_form_arguments(node, context)
        try:
            attributes = names.value.replace(",", " ").split()
        except AttributeError:
            if not enum:
                attributes = [
                    _infer_first(const, context).value for const in names.elts
                ]
            else:
                # Enums supports either iterator of (name, value) pairs
                # or mappings.
                if hasattr(names, "items") and isinstance(names.items, list):
                    attributes = [
                        _infer_first(const[0], context).value
                        for const in names.items
                        if isinstance(const[0], nodes.Const)
                    ]
                elif hasattr(names, "elts"):
                    # Enums can support either ["a", "b", "c"]
                    # or [("a", 1), ("b", 2), ...], but they can't
                    # be mixed.
                    if all(isinstance(const, nodes.Tuple) for const in names.elts):
                        attributes = [
                            _infer_first(const.elts[0], context).value
                            for const in names.elts
                            if isinstance(const, nodes.Tuple)
                        ]
                    else:
                        attributes = [
                            _infer_first(const, context).value for const in names.elts
                        ]
                else:
                    raise AttributeError
                if not attributes:
                    raise AttributeError
    except (AttributeError, exceptions.InferenceError):
        raise UseInferenceDefault()

    # If we can't infer the name of the class, don't crash, up to this point
    # we know it is a namedtuple anyway.
    name = name or "Uninferable"
    # we want to return a Class node instance with proper attributes set
    class_node = nodes.ClassDef(name, "docstring")
    class_node.parent = node.parent
    # set base class=tuple
    class_node.bases.append(base_type)
    # XXX add __init__(*attributes) method
    for attr in attributes:
        fake_node = nodes.EmptyNode()
        fake_node.parent = class_node
        fake_node.attrname = attr
        class_node.instance_attrs[attr] = [fake_node]
    return class_node, name, attributes


def _has_namedtuple_base(node):
    """Predicate for class inference tip

    :type node: ClassDef
    :rtype: bool
    """
    return set(node.basenames) & TYPING_NAMEDTUPLE_BASENAMES


def _looks_like(node, name):
    func = node.func
    if isinstance(func, nodes.Attribute):
        return func.attrname == name
    if isinstance(func, nodes.Name):
        return func.name == name
    return False


_looks_like_namedtuple = functools.partial(_looks_like, name="namedtuple")
_looks_like_enum = functools.partial(_looks_like, name="Enum")
_looks_like_typing_namedtuple = functools.partial(_looks_like, name="NamedTuple")


def infer_named_tuple(node, context=None):
    """Specific inference function for namedtuple Call node"""
    tuple_base_name = nodes.Name(name="tuple", parent=node.root())
    class_node, name, attributes = infer_func_form(
        node, tuple_base_name, context=context
    )
    call_site = arguments.CallSite.from_call(node)
    func = next(extract_node("import collections; collections.namedtuple").infer())
    try:
        rename = next(call_site.infer_argument(func, "rename", context)).bool_value()
    except InferenceError:
        rename = False

    if rename:
        attributes = _get_renamed_namedtuple_attributes(attributes)

    replace_args = ", ".join("{arg}=None".format(arg=arg) for arg in attributes)
    field_def = (
        "    {name} = property(lambda self: self[{index:d}], "
        "doc='Alias for field number {index:d}')"
    )
    field_defs = "\n".join(
        field_def.format(name=name, index=index)
        for index, name in enumerate(attributes)
    )
    fake = AstroidBuilder(MANAGER).string_build(
        """
class %(name)s(tuple):
    __slots__ = ()
    _fields = %(fields)r
    def _asdict(self):
        return self.__dict__
    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        return new(cls, iterable)
    def _replace(self, %(replace_args)s):
        return self
    def __getnewargs__(self):
        return tuple(self)
%(field_defs)s
    """
        % {
            "name": name,
            "fields": attributes,
            "field_defs": field_defs,
            "replace_args": replace_args,
        }
    )
    class_node.locals["_asdict"] = fake.body[0].locals["_asdict"]
    class_node.locals["_make"] = fake.body[0].locals["_make"]
    class_node.locals["_replace"] = fake.body[0].locals["_replace"]
    class_node.locals["_fields"] = fake.body[0].locals["_fields"]
    for attr in attributes:
        class_node.locals[attr] = fake.body[0].locals[attr]
    # we use UseInferenceDefault, we can't be a generator so return an iterator
    return iter([class_node])


def _get_renamed_namedtuple_attributes(field_names):
    names = list(field_names)
    seen = set()
    for i, name in enumerate(field_names):
        if (
            not all(c.isalnum() or c == "_" for c in name)
            or keyword.iskeyword(name)
            or not name
            or name[0].isdigit()
            or name.startswith("_")
            or name in seen
        ):
            names[i] = "_%d" % i
        seen.add(name)
    return tuple(names)


def infer_enum(node, context=None):
    """ Specific inference function for enum Call node. """
    enum_meta = extract_node(
        """
    class EnumMeta(object):
        'docstring'
        def __call__(self, node):
            class EnumAttribute(object):
                name = ''
                value = 0
            return EnumAttribute()
        def __iter__(self):
            class EnumAttribute(object):
                name = ''
                value = 0
            return [EnumAttribute()]
        def __reversed__(self):
            class EnumAttribute(object):
                name = ''
                value = 0
            return (EnumAttribute, )
        def __next__(self):
            return next(iter(self))
        def __getitem__(self, attr):
            class Value(object):
                @property
                def name(self):
                    return ''
                @property
                def value(self):
                    return attr

            return Value()
        __members__ = ['']
    """
    )
    class_node = infer_func_form(node, enum_meta, context=context, enum=True)[0]
    return iter([class_node.instantiate_class()])


INT_FLAG_ADDITION_METHODS = """
    def __or__(self, other):
        return {name}(self.value | other.value)
    def __and__(self, other):
        return {name}(self.value & other.value)
    def __xor__(self, other):
        return {name}(self.value ^ other.value)
    def __add__(self, other):
        return {name}(self.value + other.value)
    def __div__(self, other):
        return {name}(self.value / other.value)
    def __invert__(self):
        return {name}(~self.value)
    def __mul__(self, other):
        return {name}(self.value * other.value)
"""


def infer_enum_class(node):
    """ Specific inference for enums. """
    for basename in node.basenames:
        # TODO: doesn't handle subclasses yet. This implementation
        # is a hack to support enums.
        if basename not in ENUM_BASE_NAMES:
            continue
        if node.root().name == "enum":
            # Skip if the class is directly from enum module.
            break
        for local, values in node.locals.items():
            if any(not isinstance(value, nodes.AssignName) for value in values):
                continue

            targets = []
            stmt = values[0].statement()
            if isinstance(stmt, nodes.Assign):
                if isinstance(stmt.targets[0], nodes.Tuple):
                    targets = stmt.targets[0].itered()
                else:
                    targets = stmt.targets
            elif isinstance(stmt, nodes.AnnAssign):
                targets = [stmt.target]

            inferred_return_value = None
            if isinstance(stmt, nodes.Assign):
                if isinstance(stmt.value, nodes.Const):
                    if isinstance(stmt.value.value, str):
                        inferred_return_value = repr(stmt.value.value)
                    else:
                        inferred_return_value = stmt.value.value
                else:
                    inferred_return_value = stmt.value.as_string()

            new_targets = []
            for target in targets:
                # Replace all the assignments with our mocked class.
                classdef = dedent(
                    """
                class {name}({types}):
                    @property
                    def value(self):
                        return {return_value}
                    @property
                    def name(self):
                        return "{name}"
                """.format(
                        name=target.name,
                        types=", ".join(node.basenames),
                        return_value=inferred_return_value,
                    )
                )
                if "IntFlag" in basename:
                    # Alright, we need to add some additional methods.
                    # Unfortunately we still can't infer the resulting objects as
                    # Enum members, but once we'll be able to do that, the following
                    # should result in some nice symbolic execution
                    classdef += INT_FLAG_ADDITION_METHODS.format(name=target.name)

                fake = AstroidBuilder(MANAGER).string_build(classdef)[target.name]
                fake.parent = target.parent
                for method in node.mymethods():
                    fake.locals[method.name] = [method]
                new_targets.append(fake.instantiate_class())
            node.locals[local] = new_targets
        break
    return node


def infer_typing_namedtuple_class(class_node, context=None):
    """Infer a subclass of typing.NamedTuple"""
    # Check if it has the corresponding bases
    annassigns_fields = [
        annassign.target.name
        for annassign in class_node.body
        if isinstance(annassign, nodes.AnnAssign)
    ]
    code = dedent(
        """
    from collections import namedtuple
    namedtuple({typename!r}, {fields!r})
    """
    ).format(typename=class_node.name, fields=",".join(annassigns_fields))
    node = extract_node(code)
    generated_class_node = next(infer_named_tuple(node, context))
    for method in class_node.mymethods():
        generated_class_node.locals[method.name] = [method]

    for assign in class_node.body:
        if not isinstance(assign, nodes.Assign):
            continue

        for target in assign.targets:
            attr = target.name
            generated_class_node.locals[attr] = class_node.locals[attr]

    return iter((generated_class_node,))


def infer_typing_namedtuple(node, context=None):
    """Infer a typing.NamedTuple(...) call."""
    # This is essentially a namedtuple with different arguments
    # so we extract the args and infer a named tuple.
    try:
        func = next(node.func.infer())
    except InferenceError:
        raise UseInferenceDefault

    if func.qname() != "typing.NamedTuple":
        raise UseInferenceDefault

    if len(node.args) != 2:
        raise UseInferenceDefault

    if not isinstance(node.args[1], (nodes.List, nodes.Tuple)):
        raise UseInferenceDefault

    names = []
    for elt in node.args[1].elts:
        if not isinstance(elt, (nodes.List, nodes.Tuple)):
            raise UseInferenceDefault
        if len(elt.elts) != 2:
            raise UseInferenceDefault
        names.append(elt.elts[0].as_string())

    typename = node.args[0].as_string()
    if names:
        field_names = "({},)".format(",".join(names))
    else:
        field_names = "''"
    node = extract_node(
        "namedtuple({typename}, {fields})".format(typename=typename, fields=field_names)
    )
    return infer_named_tuple(node, context)


MANAGER.register_transform(
    nodes.Call, inference_tip(infer_named_tuple), _looks_like_namedtuple
)
MANAGER.register_transform(nodes.Call, inference_tip(infer_enum), _looks_like_enum)
MANAGER.register_transform(
    nodes.ClassDef,
    infer_enum_class,
    predicate=lambda cls: any(
        basename for basename in cls.basenames if basename in ENUM_BASE_NAMES
    ),
)
MANAGER.register_transform(
    nodes.ClassDef, inference_tip(infer_typing_namedtuple_class), _has_namedtuple_base
)
MANAGER.register_transform(
    nodes.Call, inference_tip(infer_typing_namedtuple), _looks_like_typing_namedtuple
)
