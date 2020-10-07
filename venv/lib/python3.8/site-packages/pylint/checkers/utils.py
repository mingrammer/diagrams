# -*- coding: utf-8 -*-
# Copyright (c) 2006-2007, 2009-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2009 Mads Kiilerich <mads@kiilerich.com>
# Copyright (c) 2010 Daniel Harding <dharding@gmail.com>
# Copyright (c) 2012-2014 Google, Inc.
# Copyright (c) 2012 FELD Boris <lothiraldan@gmail.com>
# Copyright (c) 2013-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Brett Cannon <brett@python.org>
# Copyright (c) 2014 Ricardo Gemignani <ricardo.gemignani@gmail.com>
# Copyright (c) 2014 Arun Persaud <arun@nubati.net>
# Copyright (c) 2015 Dmitry Pribysh <dmand@yandex.ru>
# Copyright (c) 2015 Florian Bruhin <me@the-compiler.org>
# Copyright (c) 2015 Radu Ciorba <radu@devrandom.ro>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2016, 2018 Ashley Whetter <ashley@awhetter.co.uk>
# Copyright (c) 2016-2017 Łukasz Rogalski <rogalski.91@gmail.com>
# Copyright (c) 2016-2017 Moises Lopez <moylop260@vauxoo.com>
# Copyright (c) 2016 Brian C. Lane <bcl@redhat.com>
# Copyright (c) 2017-2018 hippo91 <guillaume.peillex@gmail.com>
# Copyright (c) 2017 ttenhoeve-aa <ttenhoeve@appannie.com>
# Copyright (c) 2018 Bryce Guinta <bryce.guinta@protonmail.com>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>
# Copyright (c) 2018 Ville Skyttä <ville.skytta@upcloud.com>
# Copyright (c) 2018 Brian Shaginaw <brian.shaginaw@warbyparker.com>
# Copyright (c) 2018 Caio Carrara <ccarrara@redhat.com>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""some functions that may be useful for various checkers
"""
import builtins
import itertools
import numbers
import re
import string
from functools import lru_cache, partial
from typing import Callable, Dict, Iterable, List, Match, Optional, Set, Tuple, Union

import astroid
from astroid import bases as _bases
from astroid import helpers, scoped_nodes
from astroid.exceptions import _NonDeducibleTypeHierarchy

import _string  # pylint: disable=wrong-import-position, wrong-import-order

BUILTINS_NAME = builtins.__name__
COMP_NODE_TYPES = (
    astroid.ListComp,
    astroid.SetComp,
    astroid.DictComp,
    astroid.GeneratorExp,
)
EXCEPTIONS_MODULE = "builtins"
ABC_METHODS = {
    "abc.abstractproperty",
    "abc.abstractmethod",
    "abc.abstractclassmethod",
    "abc.abstractstaticmethod",
}
TYPING_PROTOCOLS = frozenset({"typing.Protocol", "typing_extensions.Protocol"})
ITER_METHOD = "__iter__"
AITER_METHOD = "__aiter__"
NEXT_METHOD = "__next__"
GETITEM_METHOD = "__getitem__"
CLASS_GETITEM_METHOD = "__class_getitem__"
SETITEM_METHOD = "__setitem__"
DELITEM_METHOD = "__delitem__"
CONTAINS_METHOD = "__contains__"
KEYS_METHOD = "keys"

# Dictionary which maps the number of expected parameters a
# special method can have to a set of special methods.
# The following keys are used to denote the parameters restrictions:
#
# * None: variable number of parameters
# * number: exactly that number of parameters
# * tuple: this are the odd ones. Basically it means that the function
#          can work with any number of arguments from that tuple,
#          although it's best to implement it in order to accept
#          all of them.
_SPECIAL_METHODS_PARAMS = {
    None: ("__new__", "__init__", "__call__"),
    0: (
        "__del__",
        "__repr__",
        "__str__",
        "__bytes__",
        "__hash__",
        "__bool__",
        "__dir__",
        "__len__",
        "__length_hint__",
        "__iter__",
        "__reversed__",
        "__neg__",
        "__pos__",
        "__abs__",
        "__invert__",
        "__complex__",
        "__int__",
        "__float__",
        "__neg__",
        "__pos__",
        "__abs__",
        "__complex__",
        "__int__",
        "__float__",
        "__index__",
        "__enter__",
        "__aenter__",
        "__getnewargs_ex__",
        "__getnewargs__",
        "__getstate__",
        "__reduce__",
        "__copy__",
        "__unicode__",
        "__nonzero__",
        "__await__",
        "__aiter__",
        "__anext__",
        "__fspath__",
    ),
    1: (
        "__format__",
        "__lt__",
        "__le__",
        "__eq__",
        "__ne__",
        "__gt__",
        "__ge__",
        "__getattr__",
        "__getattribute__",
        "__delattr__",
        "__delete__",
        "__instancecheck__",
        "__subclasscheck__",
        "__getitem__",
        "__missing__",
        "__delitem__",
        "__contains__",
        "__add__",
        "__sub__",
        "__mul__",
        "__truediv__",
        "__floordiv__",
        "__rfloordiv__",
        "__mod__",
        "__divmod__",
        "__lshift__",
        "__rshift__",
        "__and__",
        "__xor__",
        "__or__",
        "__radd__",
        "__rsub__",
        "__rmul__",
        "__rtruediv__",
        "__rmod__",
        "__rdivmod__",
        "__rpow__",
        "__rlshift__",
        "__rrshift__",
        "__rand__",
        "__rxor__",
        "__ror__",
        "__iadd__",
        "__isub__",
        "__imul__",
        "__itruediv__",
        "__ifloordiv__",
        "__imod__",
        "__ilshift__",
        "__irshift__",
        "__iand__",
        "__ixor__",
        "__ior__",
        "__ipow__",
        "__setstate__",
        "__reduce_ex__",
        "__deepcopy__",
        "__cmp__",
        "__matmul__",
        "__rmatmul__",
        "__div__",
    ),
    2: ("__setattr__", "__get__", "__set__", "__setitem__", "__set_name__"),
    3: ("__exit__", "__aexit__"),
    (0, 1): ("__round__",),
}

SPECIAL_METHODS_PARAMS = {
    name: params
    for params, methods in _SPECIAL_METHODS_PARAMS.items()
    for name in methods  # type: ignore
}
PYMETHODS = set(SPECIAL_METHODS_PARAMS)


class NoSuchArgumentError(Exception):
    pass


def is_inside_except(node):
    """Returns true if node is inside the name of an except handler."""
    current = node
    while current and not isinstance(current.parent, astroid.ExceptHandler):
        current = current.parent

    return current and current is current.parent.name


def is_inside_lambda(node: astroid.node_classes.NodeNG) -> bool:
    """Return true if given node is inside lambda"""
    parent = node.parent
    while parent is not None:
        if isinstance(parent, astroid.Lambda):
            return True
        parent = parent.parent
    return False


def get_all_elements(
    node: astroid.node_classes.NodeNG
) -> Iterable[astroid.node_classes.NodeNG]:
    """Recursively returns all atoms in nested lists and tuples."""
    if isinstance(node, (astroid.Tuple, astroid.List)):
        for child in node.elts:
            yield from get_all_elements(child)
    else:
        yield node


def clobber_in_except(
    node: astroid.node_classes.NodeNG
) -> Tuple[bool, Optional[Tuple[str, str]]]:
    """Checks if an assignment node in an except handler clobbers an existing
    variable.

    Returns (True, args for W0623) if assignment clobbers an existing variable,
    (False, None) otherwise.
    """
    if isinstance(node, astroid.AssignAttr):
        return True, (node.attrname, "object %r" % (node.expr.as_string(),))
    if isinstance(node, astroid.AssignName):
        name = node.name
        if is_builtin(name):
            return True, (name, "builtins")

        stmts = node.lookup(name)[1]
        if stmts and not isinstance(
            stmts[0].assign_type(),
            (astroid.Assign, astroid.AugAssign, astroid.ExceptHandler),
        ):
            return True, (name, "outer scope (line %s)" % stmts[0].fromlineno)
    return False, None


def is_super(node: astroid.node_classes.NodeNG) -> bool:
    """return True if the node is referencing the "super" builtin function
    """
    if getattr(node, "name", None) == "super" and node.root().name == BUILTINS_NAME:
        return True
    return False


def is_error(node: astroid.node_classes.NodeNG) -> bool:
    """return true if the function does nothing but raising an exception"""
    raises = False
    returns = False
    for child_node in node.nodes_of_class((astroid.Raise, astroid.Return)):
        if isinstance(child_node, astroid.Raise):
            raises = True
        if isinstance(child_node, astroid.Return):
            returns = True
    return raises and not returns


builtins = builtins.__dict__.copy()  # type: ignore
SPECIAL_BUILTINS = ("__builtins__",)  # '__path__', '__file__')


def is_builtin_object(node: astroid.node_classes.NodeNG) -> bool:
    """Returns True if the given node is an object from the __builtin__ module."""
    return node and node.root().name == BUILTINS_NAME


def is_builtin(name: str) -> bool:
    """return true if <name> could be considered as a builtin defined by python
    """
    return name in builtins or name in SPECIAL_BUILTINS  # type: ignore


def is_defined_in_scope(
    var_node: astroid.node_classes.NodeNG,
    varname: str,
    scope: astroid.node_classes.NodeNG,
) -> bool:
    if isinstance(scope, astroid.If):
        for node in scope.body:
            if (
                isinstance(node, astroid.Assign)
                and any(
                    isinstance(target, astroid.AssignName) and target.name == varname
                    for target in node.targets
                )
            ) or (isinstance(node, astroid.Nonlocal) and varname in node.names):
                return True
    elif isinstance(scope, (COMP_NODE_TYPES, astroid.For)):
        for ass_node in scope.nodes_of_class(astroid.AssignName):
            if ass_node.name == varname:
                return True
    elif isinstance(scope, astroid.With):
        for expr, ids in scope.items:
            if expr.parent_of(var_node):
                break
            if ids and isinstance(ids, astroid.AssignName) and ids.name == varname:
                return True
    elif isinstance(scope, (astroid.Lambda, astroid.FunctionDef)):
        if scope.args.is_argument(varname):
            # If the name is found inside a default value
            # of a function, then let the search continue
            # in the parent's tree.
            if scope.args.parent_of(var_node):
                try:
                    scope.args.default_value(varname)
                    scope = scope.parent
                    is_defined_in_scope(var_node, varname, scope)
                except astroid.NoDefault:
                    pass
            return True
        if getattr(scope, "name", None) == varname:
            return True
    elif isinstance(scope, astroid.ExceptHandler):
        if isinstance(scope.name, astroid.AssignName):
            ass_node = scope.name
            if ass_node.name == varname:
                return True
    return False


def is_defined_before(var_node: astroid.node_classes.NodeNG) -> bool:
    """return True if the variable node is defined by a parent node (list,
    set, dict, or generator comprehension, lambda) or in a previous sibling
    node on the same line (statement_defining ; statement_using)
    """
    varname = var_node.name
    _node = var_node.parent
    while _node:
        if is_defined_in_scope(var_node, varname, _node):
            return True
        _node = _node.parent
    # possibly multiple statements on the same line using semi colon separator
    stmt = var_node.statement()
    _node = stmt.previous_sibling()
    lineno = stmt.fromlineno
    while _node and _node.fromlineno == lineno:
        for assign_node in _node.nodes_of_class(astroid.AssignName):
            if assign_node.name == varname:
                return True
        for imp_node in _node.nodes_of_class((astroid.ImportFrom, astroid.Import)):
            if varname in [name[1] or name[0] for name in imp_node.names]:
                return True
        _node = _node.previous_sibling()
    return False


def is_default_argument(node: astroid.node_classes.NodeNG) -> bool:
    """return true if the given Name node is used in function or lambda
    default argument's value
    """
    parent = node.scope()
    if isinstance(parent, (astroid.FunctionDef, astroid.Lambda)):
        for default_node in parent.args.defaults:
            for default_name_node in default_node.nodes_of_class(astroid.Name):
                if default_name_node is node:
                    return True
    return False


def is_func_decorator(node: astroid.node_classes.NodeNG) -> bool:
    """return true if the name is used in function decorator"""
    parent = node.parent
    while parent is not None:
        if isinstance(parent, astroid.Decorators):
            return True
        if parent.is_statement or isinstance(
            parent,
            (astroid.Lambda, scoped_nodes.ComprehensionScope, scoped_nodes.ListComp),
        ):
            break
        parent = parent.parent
    return False


def is_ancestor_name(
    frame: astroid.node_classes.NodeNG, node: astroid.node_classes.NodeNG
) -> bool:
    """return True if `frame` is an astroid.Class node with `node` in the
    subtree of its bases attribute
    """
    try:
        bases = frame.bases
    except AttributeError:
        return False
    for base in bases:
        if node in base.nodes_of_class(astroid.Name):
            return True
    return False


def assign_parent(node: astroid.node_classes.NodeNG) -> astroid.node_classes.NodeNG:
    """return the higher parent which is not an AssignName, Tuple or List node
    """
    while node and isinstance(node, (astroid.AssignName, astroid.Tuple, astroid.List)):
        node = node.parent
    return node


def overrides_a_method(class_node: astroid.node_classes.NodeNG, name: str) -> bool:
    """return True if <name> is a method overridden from an ancestor"""
    for ancestor in class_node.ancestors():
        if name in ancestor and isinstance(ancestor[name], astroid.FunctionDef):
            return True
    return False


def check_messages(*messages: str) -> Callable:
    """decorator to store messages that are handled by a checker method"""

    def store_messages(func):
        func.checks_msgs = messages
        return func

    return store_messages


class IncompleteFormatString(Exception):
    """A format string ended in the middle of a format specifier."""


class UnsupportedFormatCharacter(Exception):
    """A format character in a format string is not one of the supported
    format characters."""

    def __init__(self, index):
        Exception.__init__(self, index)
        self.index = index


def parse_format_string(
    format_string: str
) -> Tuple[Set[str], int, Dict[str, str], List[str]]:
    """Parses a format string, returning a tuple of (keys, num_args), where keys
    is the set of mapping keys in the format string, and num_args is the number
    of arguments required by the format string.  Raises
    IncompleteFormatString or UnsupportedFormatCharacter if a
    parse error occurs."""
    keys = set()
    key_types = dict()
    pos_types = []
    num_args = 0

    def next_char(i):
        i += 1
        if i == len(format_string):
            raise IncompleteFormatString
        return (i, format_string[i])

    i = 0
    while i < len(format_string):
        char = format_string[i]
        if char == "%":
            i, char = next_char(i)
            # Parse the mapping key (optional).
            key = None
            if char == "(":
                depth = 1
                i, char = next_char(i)
                key_start = i
                while depth != 0:
                    if char == "(":
                        depth += 1
                    elif char == ")":
                        depth -= 1
                    i, char = next_char(i)
                key_end = i - 1
                key = format_string[key_start:key_end]

            # Parse the conversion flags (optional).
            while char in "#0- +":
                i, char = next_char(i)
            # Parse the minimum field width (optional).
            if char == "*":
                num_args += 1
                i, char = next_char(i)
            else:
                while char in string.digits:
                    i, char = next_char(i)
            # Parse the precision (optional).
            if char == ".":
                i, char = next_char(i)
                if char == "*":
                    num_args += 1
                    i, char = next_char(i)
                else:
                    while char in string.digits:
                        i, char = next_char(i)
            # Parse the length modifier (optional).
            if char in "hlL":
                i, char = next_char(i)
            # Parse the conversion type (mandatory).
            flags = "diouxXeEfFgGcrs%a"
            if char not in flags:
                raise UnsupportedFormatCharacter(i)
            if key:
                keys.add(key)
                key_types[key] = char
            elif char != "%":
                num_args += 1
                pos_types.append(char)
        i += 1
    return keys, num_args, key_types, pos_types


def split_format_field_names(format_string) -> Tuple[str, Iterable[Tuple[bool, str]]]:
    try:
        return _string.formatter_field_name_split(format_string)
    except ValueError:
        raise IncompleteFormatString()


def collect_string_fields(format_string) -> Iterable[Optional[str]]:
    """ Given a format string, return an iterator
    of all the valid format fields. It handles nested fields
    as well.
    """
    formatter = string.Formatter()
    try:
        parseiterator = formatter.parse(format_string)
        for result in parseiterator:
            if all(item is None for item in result[1:]):
                # not a replacement format
                continue
            name = result[1]
            nested = result[2]
            yield name
            if nested:
                for field in collect_string_fields(nested):
                    yield field
    except ValueError as exc:
        # Probably the format string is invalid.
        if exc.args[0].startswith("cannot switch from manual"):
            # On Jython, parsing a string with both manual
            # and automatic positions will fail with a ValueError,
            # while on CPython it will simply return the fields,
            # the validation being done in the interpreter (?).
            # We're just returning two mixed fields in order
            # to trigger the format-combined-specification check.
            yield ""
            yield "1"
            return
        raise IncompleteFormatString(format_string)


def parse_format_method_string(
    format_string: str
) -> Tuple[List[Tuple[str, List[Tuple[bool, str]]]], int, int]:
    """
    Parses a PEP 3101 format string, returning a tuple of
    (keyword_arguments, implicit_pos_args_cnt, explicit_pos_args),
    where keyword_arguments is the set of mapping keys in the format string, implicit_pos_args_cnt
    is the number of arguments required by the format string and
    explicit_pos_args is the number of arguments passed with the position.
    """
    keyword_arguments = []
    implicit_pos_args_cnt = 0
    explicit_pos_args = set()
    for name in collect_string_fields(format_string):
        if name and str(name).isdigit():
            explicit_pos_args.add(str(name))
        elif name:
            keyname, fielditerator = split_format_field_names(name)
            if isinstance(keyname, numbers.Number):
                # In Python 2 it will return long which will lead
                # to different output between 2 and 3
                explicit_pos_args.add(str(keyname))
                keyname = int(keyname)
            try:
                keyword_arguments.append((keyname, list(fielditerator)))
            except ValueError:
                raise IncompleteFormatString()
        else:
            implicit_pos_args_cnt += 1
    return keyword_arguments, implicit_pos_args_cnt, len(explicit_pos_args)


def is_attr_protected(attrname: str) -> bool:
    """return True if attribute name is protected (start with _ and some other
    details), False otherwise.
    """
    return (
        attrname[0] == "_"
        and attrname != "_"
        and not (attrname.startswith("__") and attrname.endswith("__"))
    )


def node_frame_class(node: astroid.node_classes.NodeNG) -> Optional[astroid.ClassDef]:
    """Return the class that is wrapping the given node

    The function returns a class for a method node (or a staticmethod or a
    classmethod), otherwise it returns `None`.
    """
    klass = node.frame()

    while klass is not None and not isinstance(klass, astroid.ClassDef):
        if klass.parent is None:
            klass = None
        else:
            klass = klass.parent.frame()

    return klass


def is_attr_private(attrname: str) -> Optional[Match[str]]:
    """Check that attribute name is private (at least two leading underscores,
    at most one trailing underscore)
    """
    regex = re.compile("^_{2,}.*[^_]+_?$")
    return regex.match(attrname)


def get_argument_from_call(
    call_node: astroid.Call, position: int = None, keyword: str = None
) -> astroid.Name:
    """Returns the specified argument from a function call.

    :param astroid.Call call_node: Node representing a function call to check.
    :param int position: position of the argument.
    :param str keyword: the keyword of the argument.

    :returns: The node representing the argument, None if the argument is not found.
    :rtype: astroid.Name
    :raises ValueError: if both position and keyword are None.
    :raises NoSuchArgumentError: if no argument at the provided position or with
    the provided keyword.
    """
    if position is None and keyword is None:
        raise ValueError("Must specify at least one of: position or keyword.")
    if position is not None:
        try:
            return call_node.args[position]
        except IndexError:
            pass
    if keyword and call_node.keywords:
        for arg in call_node.keywords:
            if arg.arg == keyword:
                return arg.value

    raise NoSuchArgumentError


def inherit_from_std_ex(node: astroid.node_classes.NodeNG) -> bool:
    """
    Return true if the given class node is subclass of
    exceptions.Exception.
    """
    ancestors = node.ancestors() if hasattr(node, "ancestors") else []
    for ancestor in itertools.chain([node], ancestors):
        if (
            ancestor.name in ("Exception", "BaseException")
            and ancestor.root().name == EXCEPTIONS_MODULE
        ):
            return True
    return False


def error_of_type(handler: astroid.ExceptHandler, error_type) -> bool:
    """
    Check if the given exception handler catches
    the given error_type.

    The *handler* parameter is a node, representing an ExceptHandler node.
    The *error_type* can be an exception, such as AttributeError,
    the name of an exception, or it can be a tuple of errors.
    The function will return True if the handler catches any of the
    given errors.
    """

    def stringify_error(error):
        if not isinstance(error, str):
            return error.__name__
        return error

    if not isinstance(error_type, tuple):
        error_type = (error_type,)  # type: ignore
    expected_errors = {stringify_error(error) for error in error_type}  # type: ignore
    if not handler.type:
        return True
    return handler.catch(expected_errors)


def decorated_with_property(node: astroid.FunctionDef) -> bool:
    """Detect if the given function node is decorated with a property. """
    if not node.decorators:
        return False
    for decorator in node.decorators.nodes:
        try:
            if _is_property_decorator(decorator):
                return True
        except astroid.InferenceError:
            pass
    return False


def _is_property_kind(node, *kinds):
    if not isinstance(node, (astroid.UnboundMethod, astroid.FunctionDef)):
        return False
    if node.decorators:
        for decorator in node.decorators.nodes:
            if isinstance(decorator, astroid.Attribute) and decorator.attrname in kinds:
                return True
    return False


def is_property_setter(node: astroid.FunctionDef) -> bool:
    """Check if the given node is a property setter"""
    return _is_property_kind(node, "setter")


def is_property_setter_or_deleter(node: astroid.FunctionDef) -> bool:
    """Check if the given node is either a property setter or a deleter"""
    return _is_property_kind(node, "setter", "deleter")


def _is_property_decorator(decorator: astroid.Name) -> bool:
    for inferred in decorator.infer():
        if isinstance(inferred, astroid.ClassDef):
            if inferred.root().name == BUILTINS_NAME and inferred.name == "property":
                return True
            for ancestor in inferred.ancestors():
                if (
                    ancestor.name == "property"
                    and ancestor.root().name == BUILTINS_NAME
                ):
                    return True
    return False


def decorated_with(
    func: Union[astroid.FunctionDef, astroid.BoundMethod, astroid.UnboundMethod],
    qnames: Iterable[str],
) -> bool:
    """Determine if the `func` node has a decorator with the qualified name `qname`."""
    decorators = func.decorators.nodes if func.decorators else []
    for decorator_node in decorators:
        if isinstance(decorator_node, astroid.Call):
            # We only want to infer the function name
            decorator_node = decorator_node.func
        try:
            if any(
                i is not None and i.qname() in qnames or i.name in qnames
                for i in decorator_node.infer()
            ):
                return True
        except astroid.InferenceError:
            continue
    return False


@lru_cache(maxsize=1024)
def unimplemented_abstract_methods(
    node: astroid.node_classes.NodeNG, is_abstract_cb: astroid.FunctionDef = None
) -> Dict[str, astroid.node_classes.NodeNG]:
    """
    Get the unimplemented abstract methods for the given *node*.

    A method can be considered abstract if the callback *is_abstract_cb*
    returns a ``True`` value. The check defaults to verifying that
    a method is decorated with abstract methods.
    The function will work only for new-style classes. For old-style
    classes, it will simply return an empty dictionary.
    For the rest of them, it will return a dictionary of abstract method
    names and their inferred objects.
    """
    if is_abstract_cb is None:
        is_abstract_cb = partial(decorated_with, qnames=ABC_METHODS)
    visited = {}  # type: Dict[str, astroid.node_classes.NodeNG]
    try:
        mro = reversed(node.mro())
    except NotImplementedError:
        # Old style class, it will not have a mro.
        return {}
    except astroid.ResolveError:
        # Probably inconsistent hierarchy, don'try
        # to figure this out here.
        return {}
    for ancestor in mro:
        for obj in ancestor.values():
            inferred = obj
            if isinstance(obj, astroid.AssignName):
                inferred = safe_infer(obj)
                if not inferred:
                    # Might be an abstract function,
                    # but since we don't have enough information
                    # in order to take this decision, we're taking
                    # the *safe* decision instead.
                    if obj.name in visited:
                        del visited[obj.name]
                    continue
                if not isinstance(inferred, astroid.FunctionDef):
                    if obj.name in visited:
                        del visited[obj.name]
            if isinstance(inferred, astroid.FunctionDef):
                # It's critical to use the original name,
                # since after inferring, an object can be something
                # else than expected, as in the case of the
                # following assignment.
                #
                # class A:
                #     def keys(self): pass
                #     __iter__ = keys
                abstract = is_abstract_cb(inferred)
                if abstract:
                    visited[obj.name] = inferred
                elif not abstract and obj.name in visited:
                    del visited[obj.name]
    return visited


def find_try_except_wrapper_node(
    node: astroid.node_classes.NodeNG
) -> Union[astroid.ExceptHandler, astroid.TryExcept]:
    """Return the ExceptHandler or the TryExcept node in which the node is."""
    current = node
    ignores = (astroid.ExceptHandler, astroid.TryExcept)
    while current and not isinstance(current.parent, ignores):
        current = current.parent

    if current and isinstance(current.parent, ignores):
        return current.parent
    return None


def is_from_fallback_block(node: astroid.node_classes.NodeNG) -> bool:
    """Check if the given node is from a fallback import block."""
    context = find_try_except_wrapper_node(node)
    if not context:
        return False

    if isinstance(context, astroid.ExceptHandler):
        other_body = context.parent.body
        handlers = context.parent.handlers
    else:
        other_body = itertools.chain.from_iterable(
            handler.body for handler in context.handlers
        )
        handlers = context.handlers

    has_fallback_imports = any(
        isinstance(import_node, (astroid.ImportFrom, astroid.Import))
        for import_node in other_body
    )
    ignores_import_error = _except_handlers_ignores_exception(handlers, ImportError)
    return ignores_import_error or has_fallback_imports


def _except_handlers_ignores_exception(
    handlers: astroid.ExceptHandler, exception
) -> bool:
    func = partial(error_of_type, error_type=(exception,))
    return any(map(func, handlers))


def get_exception_handlers(
    node: astroid.node_classes.NodeNG, exception=Exception
) -> Optional[List[astroid.ExceptHandler]]:
    """Return the collections of handlers handling the exception in arguments.

    Args:
        node (astroid.NodeNG): A node that is potentially wrapped in a try except.
        exception (builtin.Exception or str): exception or name of the exception.

    Returns:
        list: the collection of handlers that are handling the exception or None.

    """
    context = find_try_except_wrapper_node(node)
    if isinstance(context, astroid.TryExcept):
        return [
            handler for handler in context.handlers if error_of_type(handler, exception)
        ]
    return []


def is_node_inside_try_except(node: astroid.Raise) -> bool:
    """Check if the node is directly under a Try/Except statement.
    (but not under an ExceptHandler!)

    Args:
        node (astroid.Raise): the node raising the exception.

    Returns:
        bool: True if the node is inside a try/except statement, False otherwise.
    """
    context = find_try_except_wrapper_node(node)
    return isinstance(context, astroid.TryExcept)


def node_ignores_exception(
    node: astroid.node_classes.NodeNG, exception=Exception
) -> bool:
    """Check if the node is in a TryExcept which handles the given exception.

    If the exception is not given, the function is going to look for bare
    excepts.
    """
    managing_handlers = get_exception_handlers(node, exception)
    if not managing_handlers:
        return False
    return any(managing_handlers)


def class_is_abstract(node: astroid.ClassDef) -> bool:
    """return true if the given class node should be considered as an abstract
    class
    """
    for method in node.methods():
        if method.parent.frame() is node:
            if method.is_abstract(pass_is_abstract=False):
                return True
    return False


def _supports_protocol_method(value: astroid.node_classes.NodeNG, attr: str) -> bool:
    try:
        attributes = value.getattr(attr)
    except astroid.NotFoundError:
        return False

    first = attributes[0]
    if isinstance(first, astroid.AssignName):
        if isinstance(first.parent.value, astroid.Const):
            return False
    return True


def is_comprehension(node: astroid.node_classes.NodeNG) -> bool:
    comprehensions = (
        astroid.ListComp,
        astroid.SetComp,
        astroid.DictComp,
        astroid.GeneratorExp,
    )
    return isinstance(node, comprehensions)


def _supports_mapping_protocol(value: astroid.node_classes.NodeNG) -> bool:
    return _supports_protocol_method(
        value, GETITEM_METHOD
    ) and _supports_protocol_method(value, KEYS_METHOD)


def _supports_membership_test_protocol(value: astroid.node_classes.NodeNG) -> bool:
    return _supports_protocol_method(value, CONTAINS_METHOD)


def _supports_iteration_protocol(value: astroid.node_classes.NodeNG) -> bool:
    return _supports_protocol_method(value, ITER_METHOD) or _supports_protocol_method(
        value, GETITEM_METHOD
    )


def _supports_async_iteration_protocol(value: astroid.node_classes.NodeNG) -> bool:
    return _supports_protocol_method(value, AITER_METHOD)


def _supports_getitem_protocol(value: astroid.node_classes.NodeNG) -> bool:
    return _supports_protocol_method(value, GETITEM_METHOD)


def _supports_setitem_protocol(value: astroid.node_classes.NodeNG) -> bool:
    return _supports_protocol_method(value, SETITEM_METHOD)


def _supports_delitem_protocol(value: astroid.node_classes.NodeNG) -> bool:
    return _supports_protocol_method(value, DELITEM_METHOD)


def _is_abstract_class_name(name: str) -> bool:
    lname = name.lower()
    is_mixin = lname.endswith("mixin")
    is_abstract = lname.startswith("abstract")
    is_base = lname.startswith("base") or lname.endswith("base")
    return is_mixin or is_abstract or is_base


def is_inside_abstract_class(node: astroid.node_classes.NodeNG) -> bool:
    while node is not None:
        if isinstance(node, astroid.ClassDef):
            if class_is_abstract(node):
                return True
            name = getattr(node, "name", None)
            if name is not None and _is_abstract_class_name(name):
                return True
        node = node.parent
    return False


def _supports_protocol(
    value: astroid.node_classes.NodeNG, protocol_callback: astroid.FunctionDef
) -> bool:
    if isinstance(value, astroid.ClassDef):
        if not has_known_bases(value):
            return True
        # classobj can only be iterable if it has an iterable metaclass
        meta = value.metaclass()
        if meta is not None:
            if protocol_callback(meta):
                return True
    if isinstance(value, astroid.BaseInstance):
        if not has_known_bases(value):
            return True
        if value.has_dynamic_getattr():
            return True
        if protocol_callback(value):
            return True

    if (
        isinstance(value, _bases.Proxy)
        and isinstance(value._proxied, astroid.BaseInstance)
        and has_known_bases(value._proxied)
    ):
        value = value._proxied
        return protocol_callback(value)

    return False


def is_iterable(value: astroid.node_classes.NodeNG, check_async: bool = False) -> bool:
    if check_async:
        protocol_check = _supports_async_iteration_protocol
    else:
        protocol_check = _supports_iteration_protocol
    return _supports_protocol(value, protocol_check)


def is_mapping(value: astroid.node_classes.NodeNG) -> bool:
    return _supports_protocol(value, _supports_mapping_protocol)


def supports_membership_test(value: astroid.node_classes.NodeNG) -> bool:
    supported = _supports_protocol(value, _supports_membership_test_protocol)
    return supported or is_iterable(value)


def supports_getitem(value: astroid.node_classes.NodeNG) -> bool:
    if isinstance(value, astroid.ClassDef):
        if _supports_protocol_method(value, CLASS_GETITEM_METHOD):
            return True
    return _supports_protocol(value, _supports_getitem_protocol)


def supports_setitem(value: astroid.node_classes.NodeNG) -> bool:
    return _supports_protocol(value, _supports_setitem_protocol)


def supports_delitem(value: astroid.node_classes.NodeNG) -> bool:
    return _supports_protocol(value, _supports_delitem_protocol)


@lru_cache(maxsize=1024)
def safe_infer(
    node: astroid.node_classes.NodeNG, context=None
) -> Optional[astroid.node_classes.NodeNG]:
    """Return the inferred value for the given node.

    Return None if inference failed or if there is some ambiguity (more than
    one node has been inferred).
    """
    try:
        inferit = node.infer(context=context)
        value = next(inferit)
    except astroid.InferenceError:
        return None
    try:
        next(inferit)
        return None  # None if there is ambiguity on the inferred node
    except astroid.InferenceError:
        return None  # there is some kind of ambiguity
    except StopIteration:
        return value


def has_known_bases(klass: astroid.ClassDef, context=None) -> bool:
    """Return true if all base classes of a class could be inferred."""
    try:
        return klass._all_bases_known
    except AttributeError:
        pass
    for base in klass.bases:
        result = safe_infer(base, context=context)
        if (
            not isinstance(result, astroid.ClassDef)
            or result is klass
            or not has_known_bases(result, context=context)
        ):
            klass._all_bases_known = False
            return False
    klass._all_bases_known = True
    return True


def is_none(node: astroid.node_classes.NodeNG) -> bool:
    return (
        node is None
        or (isinstance(node, astroid.Const) and node.value is None)
        or (isinstance(node, astroid.Name) and node.name == "None")
    )


def node_type(node: astroid.node_classes.NodeNG) -> Optional[type]:
    """Return the inferred type for `node`

    If there is more than one possible type, or if inferred type is Uninferable or None,
    return None
    """
    # check there is only one possible type for the assign node. Else we
    # don't handle it for now
    types = set()
    try:
        for var_type in node.infer():
            if var_type == astroid.Uninferable or is_none(var_type):
                continue
            types.add(var_type)
            if len(types) > 1:
                return None
    except astroid.InferenceError:
        return None
    return types.pop() if types else None


def is_registered_in_singledispatch_function(node: astroid.FunctionDef) -> bool:
    """Check if the given function node is a singledispatch function."""

    singledispatch_qnames = (
        "functools.singledispatch",
        "singledispatch.singledispatch",
    )

    if not isinstance(node, astroid.FunctionDef):
        return False

    decorators = node.decorators.nodes if node.decorators else []
    for decorator in decorators:
        # func.register are function calls
        if not isinstance(decorator, astroid.Call):
            continue

        func = decorator.func
        if not isinstance(func, astroid.Attribute) or func.attrname != "register":
            continue

        try:
            func_def = next(func.expr.infer())
        except astroid.InferenceError:
            continue

        if isinstance(func_def, astroid.FunctionDef):
            # pylint: disable=redundant-keyword-arg; some flow inference goes wrong here
            return decorated_with(func_def, singledispatch_qnames)

    return False


def get_node_last_lineno(node: astroid.node_classes.NodeNG) -> int:
    """
    Get the last lineno of the given node. For a simple statement this will just be node.lineno,
    but for a node that has child statements (e.g. a method) this will be the lineno of the last
    child statement recursively.
    """
    # 'finalbody' is always the last clause in a try statement, if present
    if getattr(node, "finalbody", False):
        return get_node_last_lineno(node.finalbody[-1])
    # For if, while, and for statements 'orelse' is always the last clause.
    # For try statements 'orelse' is the last in the absence of a 'finalbody'
    if getattr(node, "orelse", False):
        return get_node_last_lineno(node.orelse[-1])
    # try statements have the 'handlers' last if there is no 'orelse' or 'finalbody'
    if getattr(node, "handlers", False):
        return get_node_last_lineno(node.handlers[-1])
    # All compound statements have a 'body'
    if getattr(node, "body", False):
        return get_node_last_lineno(node.body[-1])
    # Not a compound statement
    return node.lineno


def is_postponed_evaluation_enabled(node: astroid.node_classes.NodeNG) -> bool:
    """Check if the postponed evaluation of annotations is enabled"""
    name = "annotations"
    module = node.root()
    stmt = module.locals.get(name)
    return (
        stmt
        and isinstance(stmt[0], astroid.ImportFrom)
        and stmt[0].modname == "__future__"
    )


def is_subclass_of(child: astroid.ClassDef, parent: astroid.ClassDef) -> bool:
    """
    Check if first node is a subclass of second node.
    :param child: Node to check for subclass.
    :param parent: Node to check for superclass.
    :returns: True if child is derived from parent. False otherwise.
    """
    if not all(isinstance(node, astroid.ClassDef) for node in (child, parent)):
        return False

    for ancestor in child.ancestors():
        try:
            if helpers.is_subtype(ancestor, parent):
                return True
        except _NonDeducibleTypeHierarchy:
            continue
    return False


@lru_cache(maxsize=1024)
def is_overload_stub(node: astroid.node_classes.NodeNG) -> bool:
    """Check if a node if is a function stub decorated with typing.overload.

    :param node: Node to check.
    :returns: True if node is an overload function stub. False otherwise.
    """
    decorators = getattr(node, "decorators", None)
    return bool(decorators and decorated_with(node, ["typing.overload", "overload"]))


def is_protocol_class(cls: astroid.node_classes.NodeNG) -> bool:
    """Check if the given node represents a protocol class

    :param cls: The node to check
    :returns: True if the node is a typing protocol class, false otherwise.
    """
    if not isinstance(cls, astroid.ClassDef):
        return False

    # Use .ancestors() since not all protocol classes can have
    # their mro deduced.
    return any(parent.qname() in TYPING_PROTOCOLS for parent in cls.ancestors())
