# -*- coding: utf-8 -*-
# Copyright (c) 2009-2011, 2013-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2010 Daniel Harding <dharding@gmail.com>
# Copyright (c) 2012 FELD Boris <lothiraldan@gmail.com>
# Copyright (c) 2013-2014 Google, Inc.
# Copyright (c) 2014-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Eevee (Alex Munroe) <amunroe@yelp.com>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2015 Florian Bruhin <me@the-compiler.org>
# Copyright (c) 2016-2017 Derek Gustafson <degustaf@gmail.com>
# Copyright (c) 2016 Jared Garst <jgarst@users.noreply.github.com>
# Copyright (c) 2016 Jakub Wilk <jwilk@jwilk.net>
# Copyright (c) 2016 Dave Baum <dbaum@google.com>
# Copyright (c) 2017-2018 Ashley Whetter <ashley@awhetter.co.uk>
# Copyright (c) 2017 Łukasz Rogalski <rogalski.91@gmail.com>
# Copyright (c) 2017 rr- <rr-@sakuya.pl>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>
# Copyright (c) 2018 brendanator <brendan.maginnis@gmail.com>
# Copyright (c) 2018 Nick Drozd <nicholasdrozd@gmail.com>
# Copyright (c) 2018 HoverHell <hoverhell@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

# pylint: disable=too-many-lines; https://github.com/PyCQA/astroid/issues/465

"""Module for some node classes. More nodes in scoped_nodes.py
"""

import abc
import builtins as builtins_mod
import itertools
import pprint
import sys
from functools import lru_cache, singledispatch as _singledispatch

from astroid import as_string
from astroid import bases
from astroid import context as contextmod
from astroid import decorators
from astroid import exceptions
from astroid import manager
from astroid import mixins
from astroid import util


BUILTINS = builtins_mod.__name__
MANAGER = manager.AstroidManager()
PY38 = sys.version_info[:2] >= (3, 8)


def _is_const(value):
    return isinstance(value, tuple(CONST_CLS))


@decorators.raise_if_nothing_inferred
def unpack_infer(stmt, context=None):
    """recursively generate nodes inferred by the given statement.
    If the inferred value is a list or a tuple, recurse on the elements
    """
    if isinstance(stmt, (List, Tuple)):
        for elt in stmt.elts:
            if elt is util.Uninferable:
                yield elt
                continue
            yield from unpack_infer(elt, context)
        return dict(node=stmt, context=context)
    # if inferred is a final node, return it and stop
    inferred = next(stmt.infer(context))
    if inferred is stmt:
        yield inferred
        return dict(node=stmt, context=context)
    # else, infer recursively, except Uninferable object that should be returned as is
    for inferred in stmt.infer(context):
        if inferred is util.Uninferable:
            yield inferred
        else:
            yield from unpack_infer(inferred, context)

    return dict(node=stmt, context=context)


def are_exclusive(
    stmt1, stmt2, exceptions=None
):  # pylint: disable=redefined-outer-name
    """return true if the two given statements are mutually exclusive

    `exceptions` may be a list of exception names. If specified, discard If
    branches and check one of the statement is in an exception handler catching
    one of the given exceptions.

    algorithm :
     1) index stmt1's parents
     2) climb among stmt2's parents until we find a common parent
     3) if the common parent is a If or TryExcept statement, look if nodes are
        in exclusive branches
    """
    # index stmt1's parents
    stmt1_parents = {}
    children = {}
    node = stmt1.parent
    previous = stmt1
    while node:
        stmt1_parents[node] = 1
        children[node] = previous
        previous = node
        node = node.parent
    # climb among stmt2's parents until we find a common parent
    node = stmt2.parent
    previous = stmt2
    while node:
        if node in stmt1_parents:
            # if the common parent is a If or TryExcept statement, look if
            # nodes are in exclusive branches
            if isinstance(node, If) and exceptions is None:
                if (
                    node.locate_child(previous)[1]
                    is not node.locate_child(children[node])[1]
                ):
                    return True
            elif isinstance(node, TryExcept):
                c2attr, c2node = node.locate_child(previous)
                c1attr, c1node = node.locate_child(children[node])
                if c1node is not c2node:
                    first_in_body_caught_by_handlers = (
                        c2attr == "handlers"
                        and c1attr == "body"
                        and previous.catch(exceptions)
                    )
                    second_in_body_caught_by_handlers = (
                        c2attr == "body"
                        and c1attr == "handlers"
                        and children[node].catch(exceptions)
                    )
                    first_in_else_other_in_handlers = (
                        c2attr == "handlers" and c1attr == "orelse"
                    )
                    second_in_else_other_in_handlers = (
                        c2attr == "orelse" and c1attr == "handlers"
                    )
                    if any(
                        (
                            first_in_body_caught_by_handlers,
                            second_in_body_caught_by_handlers,
                            first_in_else_other_in_handlers,
                            second_in_else_other_in_handlers,
                        )
                    ):
                        return True
                elif c2attr == "handlers" and c1attr == "handlers":
                    return previous is not children[node]
            return False
        previous = node
        node = node.parent
    return False


# getitem() helpers.

_SLICE_SENTINEL = object()


def _slice_value(index, context=None):
    """Get the value of the given slice index."""

    if isinstance(index, Const):
        if isinstance(index.value, (int, type(None))):
            return index.value
    elif index is None:
        return None
    else:
        # Try to infer what the index actually is.
        # Since we can't return all the possible values,
        # we'll stop at the first possible value.
        try:
            inferred = next(index.infer(context=context))
        except exceptions.InferenceError:
            pass
        else:
            if isinstance(inferred, Const):
                if isinstance(inferred.value, (int, type(None))):
                    return inferred.value

    # Use a sentinel, because None can be a valid
    # value that this function can return,
    # as it is the case for unspecified bounds.
    return _SLICE_SENTINEL


def _infer_slice(node, context=None):
    lower = _slice_value(node.lower, context)
    upper = _slice_value(node.upper, context)
    step = _slice_value(node.step, context)
    if all(elem is not _SLICE_SENTINEL for elem in (lower, upper, step)):
        return slice(lower, upper, step)

    raise exceptions.AstroidTypeError(
        message="Could not infer slice used in subscript",
        node=node,
        index=node.parent,
        context=context,
    )


def _container_getitem(instance, elts, index, context=None):
    """Get a slice or an item, using the given *index*, for the given sequence."""
    try:
        if isinstance(index, Slice):
            index_slice = _infer_slice(index, context=context)
            new_cls = instance.__class__()
            new_cls.elts = elts[index_slice]
            new_cls.parent = instance.parent
            return new_cls
        if isinstance(index, Const):
            return elts[index.value]
    except IndexError as exc:
        raise exceptions.AstroidIndexError(
            message="Index {index!s} out of range",
            node=instance,
            index=index,
            context=context,
        ) from exc
    except TypeError as exc:
        raise exceptions.AstroidTypeError(
            message="Type error {error!r}", node=instance, index=index, context=context
        ) from exc

    raise exceptions.AstroidTypeError("Could not use %s as subscript index" % index)


OP_PRECEDENCE = {
    op: precedence
    for precedence, ops in enumerate(
        [
            ["Lambda"],  # lambda x: x + 1
            ["IfExp"],  # 1 if True else 2
            ["or"],
            ["and"],
            ["not"],
            ["Compare"],  # in, not in, is, is not, <, <=, >, >=, !=, ==
            ["|"],
            ["^"],
            ["&"],
            ["<<", ">>"],
            ["+", "-"],
            ["*", "@", "/", "//", "%"],
            ["UnaryOp"],  # +, -, ~
            ["**"],
            ["Await"],
        ]
    )
    for op in ops
}


class NodeNG:
    """ A node of the new Abstract Syntax Tree (AST).

    This is the base class for all Astroid node classes.
    """

    is_statement = False
    """Whether this node indicates a statement.

    :type: bool
    """
    optional_assign = False  # True for For (and for Comprehension if py <3.0)
    """Whether this node optionally assigns a variable.

    This is for loop assignments because loop won't necessarily perform an
    assignment if the loop has no iterations.
    This is also the case from comprehensions in Python 2.

    :type: bool
    """
    is_function = False  # True for FunctionDef nodes
    """Whether this node indicates a function.

    :type: bool
    """
    is_lambda = False
    # Attributes below are set by the builder module or by raw factories
    lineno = None
    """The line that this node appears on in the source code.

    :type: int or None
    """
    col_offset = None
    """The column that this node appears on in the source code.

    :type: int or None
    """
    parent = None
    """The parent node in the syntax tree.

    :type: NodeNG or None
    """
    _astroid_fields = ()
    """Node attributes that contain child nodes.

    This is redefined in most concrete classes.

    :type: tuple(str)
    """
    _other_fields = ()
    """Node attributes that do not contain child nodes.

    :type: tuple(str)
    """
    _other_other_fields = ()
    """Attributes that contain AST-dependent fields.

    :type: tuple(str)
    """
    # instance specific inference function infer(node, context)
    _explicit_inference = None

    def __init__(self, lineno=None, col_offset=None, parent=None):
        """
        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.lineno = lineno
        self.col_offset = col_offset
        self.parent = parent

    def infer(self, context=None, **kwargs):
        """Get a generator of the inferred values.

        This is the main entry point to the inference system.

        .. seealso:: :ref:`inference`

        If the instance has some explicit inference function set, it will be
        called instead of the default interface.

        :returns: The inferred values.
        :rtype: iterable
        """
        if context is not None:
            context = context.extra_context.get(self, context)
        if self._explicit_inference is not None:
            # explicit_inference is not bound, give it self explicitly
            try:
                # pylint: disable=not-callable
                return self._explicit_inference(self, context, **kwargs)
            except exceptions.UseInferenceDefault:
                pass

        if not context:
            return self._infer(context, **kwargs)

        key = (self, context.lookupname, context.callcontext, context.boundnode)
        if key in context.inferred:
            return iter(context.inferred[key])

        gen = context.cache_generator(key, self._infer(context, **kwargs))
        return util.limit_inference(gen, MANAGER.max_inferable_values)

    def _repr_name(self):
        """Get a name for nice representation.

        This is either :attr:`name`, :attr:`attrname`, or the empty string.

        :returns: The nice name.
        :rtype: str
        """
        names = {"name", "attrname"}
        if all(name not in self._astroid_fields for name in names):
            return getattr(self, "name", getattr(self, "attrname", ""))
        return ""

    def __str__(self):
        rname = self._repr_name()
        cname = type(self).__name__
        if rname:
            string = "%(cname)s.%(rname)s(%(fields)s)"
            alignment = len(cname) + len(rname) + 2
        else:
            string = "%(cname)s(%(fields)s)"
            alignment = len(cname) + 1
        result = []
        for field in self._other_fields + self._astroid_fields:
            value = getattr(self, field)
            width = 80 - len(field) - alignment
            lines = pprint.pformat(value, indent=2, width=width).splitlines(True)

            inner = [lines[0]]
            for line in lines[1:]:
                inner.append(" " * alignment + line)
            result.append("%s=%s" % (field, "".join(inner)))

        return string % {
            "cname": cname,
            "rname": rname,
            "fields": (",\n" + " " * alignment).join(result),
        }

    def __repr__(self):
        rname = self._repr_name()
        if rname:
            string = "<%(cname)s.%(rname)s l.%(lineno)s at 0x%(id)x>"
        else:
            string = "<%(cname)s l.%(lineno)s at 0x%(id)x>"
        return string % {
            "cname": type(self).__name__,
            "rname": rname,
            "lineno": self.fromlineno,
            "id": id(self),
        }

    def accept(self, visitor):
        """Visit this node using the given visitor."""
        func = getattr(visitor, "visit_" + self.__class__.__name__.lower())
        return func(self)

    def get_children(self):
        """Get the child nodes below this node.

        :returns: The children.
        :rtype: iterable(NodeNG)
        """
        for field in self._astroid_fields:
            attr = getattr(self, field)
            if attr is None:
                continue
            if isinstance(attr, (list, tuple)):
                yield from attr
            else:
                yield attr

    def last_child(self):
        """An optimized version of list(get_children())[-1]

        :returns: The last child, or None if no children exist.
        :rtype: NodeNG or None
        """
        for field in self._astroid_fields[::-1]:
            attr = getattr(self, field)
            if not attr:  # None or empty listy / tuple
                continue
            if isinstance(attr, (list, tuple)):
                return attr[-1]

            return attr
        return None

    def parent_of(self, node):
        """Check if this node is the parent of the given node.

        :param node: The node to check if it is the child.
        :type node: NodeNG

        :returns: True if this node is the parent of the given node,
            False otherwise.
        :rtype: bool
        """
        parent = node.parent
        while parent is not None:
            if self is parent:
                return True
            parent = parent.parent
        return False

    def statement(self):
        """The first parent node, including self, marked as statement node.

        :returns: The first parent statement.
        :rtype: NodeNG
        """
        if self.is_statement:
            return self
        return self.parent.statement()

    def frame(self):
        """The first parent frame node.

        A frame node is a :class:`Module`, :class:`FunctionDef`,
        or :class:`ClassDef`.

        :returns: The first parent frame node.
        :rtype: Module or FunctionDef or ClassDef
        """
        return self.parent.frame()

    def scope(self):
        """The first parent node defining a new scope.

        :returns: The first parent scope node.
        :rtype: Module or FunctionDef or ClassDef or Lambda or GenExpr
        """
        if self.parent:
            return self.parent.scope()
        return None

    def root(self):
        """Return the root node of the syntax tree.

        :returns: The root node.
        :rtype: Module
        """
        if self.parent:
            return self.parent.root()
        return self

    def child_sequence(self, child):
        """Search for the sequence that contains this child.

        :param child: The child node to search sequences for.
        :type child: NodeNG

        :returns: The sequence containing the given child node.
        :rtype: iterable(NodeNG)

        :raises AstroidError: If no sequence could be found that contains
            the given child.
        """
        for field in self._astroid_fields:
            node_or_sequence = getattr(self, field)
            if node_or_sequence is child:
                return [node_or_sequence]
            # /!\ compiler.ast Nodes have an __iter__ walking over child nodes
            if (
                isinstance(node_or_sequence, (tuple, list))
                and child in node_or_sequence
            ):
                return node_or_sequence

        msg = "Could not find %s in %s's children"
        raise exceptions.AstroidError(msg % (repr(child), repr(self)))

    def locate_child(self, child):
        """Find the field of this node that contains the given child.

        :param child: The child node to search fields for.
        :type child: NodeNG

        :returns: A tuple of the name of the field that contains the child,
            and the sequence or node that contains the child node.
        :rtype: tuple(str, iterable(NodeNG) or NodeNG)

        :raises AstroidError: If no field could be found that contains
            the given child.
        """
        for field in self._astroid_fields:
            node_or_sequence = getattr(self, field)
            # /!\ compiler.ast Nodes have an __iter__ walking over child nodes
            if child is node_or_sequence:
                return field, child
            if (
                isinstance(node_or_sequence, (tuple, list))
                and child in node_or_sequence
            ):
                return field, node_or_sequence
        msg = "Could not find %s in %s's children"
        raise exceptions.AstroidError(msg % (repr(child), repr(self)))

    # FIXME : should we merge child_sequence and locate_child ? locate_child
    # is only used in are_exclusive, child_sequence one time in pylint.

    def next_sibling(self):
        """The next sibling statement node.

        :returns: The next sibling statement node.
        :rtype: NodeNG or None
        """
        return self.parent.next_sibling()

    def previous_sibling(self):
        """The previous sibling statement.

        :returns: The previous sibling statement node.
        :rtype: NodeNG or None
        """
        return self.parent.previous_sibling()

    # these are lazy because they're relatively expensive to compute for every
    # single node, and they rarely get looked at

    @decorators.cachedproperty
    def fromlineno(self):
        """The first line that this node appears on in the source code.

        :type: int or None
        """
        if self.lineno is None:
            return self._fixed_source_line()

        return self.lineno

    @decorators.cachedproperty
    def tolineno(self):
        """The last line that this node appears on in the source code.

        :type: int or None
        """
        if not self._astroid_fields:
            # can't have children
            lastchild = None
        else:
            lastchild = self.last_child()
        if lastchild is None:
            return self.fromlineno

        return lastchild.tolineno

    def _fixed_source_line(self):
        """Attempt to find the line that this node appears on.

        We need this method since not all nodes have :attr:`lineno` set.

        :returns: The line number of this node,
            or None if this could not be determined.
        :rtype: int or None
        """
        line = self.lineno
        _node = self
        try:
            while line is None:
                _node = next(_node.get_children())
                line = _node.lineno
        except StopIteration:
            _node = self.parent
            while _node and line is None:
                line = _node.lineno
                _node = _node.parent
        return line

    def block_range(self, lineno):
        """Get a range from the given line number to where this node ends.

        :param lineno: The line number to start the range at.
        :type lineno: int

        :returns: The range of line numbers that this node belongs to,
            starting at the given line number.
        :rtype: tuple(int, int or None)
        """
        return lineno, self.tolineno

    def set_local(self, name, stmt):
        """Define that the given name is declared in the given statement node.

        This definition is stored on the parent scope node.

        .. seealso:: :meth:`scope`

        :param name: The name that is being defined.
        :type name: str

        :param stmt: The statement that defines the given name.
        :type stmt: NodeNG
        """
        self.parent.set_local(name, stmt)

    def nodes_of_class(self, klass, skip_klass=None):
        """Get the nodes (including this one or below) of the given types.

        :param klass: The types of node to search for.
        :type klass: builtins.type or tuple(builtins.type)

        :param skip_klass: The types of node to ignore. This is useful to ignore
            subclasses of :attr:`klass`.
        :type skip_klass: builtins.type or tuple(builtins.type)

        :returns: The node of the given types.
        :rtype: iterable(NodeNG)
        """
        if isinstance(self, klass):
            yield self

        if skip_klass is None:
            for child_node in self.get_children():
                yield from child_node.nodes_of_class(klass, skip_klass)

            return

        for child_node in self.get_children():
            if isinstance(child_node, skip_klass):
                continue
            yield from child_node.nodes_of_class(klass, skip_klass)

    @decorators.cached
    def _get_assign_nodes(self):
        return []

    def _get_name_nodes(self):
        for child_node in self.get_children():
            yield from child_node._get_name_nodes()

    def _get_return_nodes_skip_functions(self):
        yield from ()

    def _get_yield_nodes_skip_lambdas(self):
        yield from ()

    def _infer_name(self, frame, name):
        # overridden for ImportFrom, Import, Global, TryExcept and Arguments
        pass

    def _infer(self, context=None):
        """we don't know how to resolve a statement by default"""
        # this method is overridden by most concrete classes
        raise exceptions.InferenceError(
            "No inference function for {node!r}.", node=self, context=context
        )

    def inferred(self):
        """Get a list of the inferred values.

        .. seealso:: :ref:`inference`

        :returns: The inferred values.
        :rtype: list
        """
        return list(self.infer())

    def instantiate_class(self):
        """Instantiate an instance of the defined class.

        .. note::

            On anything other than a :class:`ClassDef` this will return self.

        :returns: An instance of the defined class.
        :rtype: object
        """
        return self

    def has_base(self, node):
        """Check if this node inherits from the given type.

        :param node: The node defining the base to look for.
            Usually this is a :class:`Name` node.
        :type node: NodeNG
        """
        return False

    def callable(self):
        """Whether this node defines something that is callable.

        :returns: True if this defines something that is callable,
            False otherwise.
        :rtype: bool
        """
        return False

    def eq(self, value):
        return False

    def as_string(self):
        """Get the source code that this node represents.

        :returns: The source code.
        :rtype: str
        """
        return as_string.to_code(self)

    def repr_tree(
        self,
        ids=False,
        include_linenos=False,
        ast_state=False,
        indent="   ",
        max_depth=0,
        max_width=80,
    ):
        """Get a string representation of the AST from this node.

        :param ids: If true, includes the ids with the node type names.
        :type ids: bool

        :param include_linenos: If true, includes the line numbers and
            column offsets.
        :type include_linenos: bool

        :param ast_state: If true, includes information derived from
            the whole AST like local and global variables.
        :type ast_state: bool

        :param indent: A string to use to indent the output string.
        :type indent: str

        :param max_depth: If set to a positive integer, won't return
            nodes deeper than max_depth in the string.
        :type max_depth: int

        :param max_width: Attempt to format the output string to stay
            within this number of characters, but can exceed it under some
            circumstances. Only positive integer values are valid, the default is 80.
        :type max_width: int

        :returns: The string representation of the AST.
        :rtype: str
        """
        # pylint: disable=too-many-statements
        @_singledispatch
        def _repr_tree(node, result, done, cur_indent="", depth=1):
            """Outputs a representation of a non-tuple/list, non-node that's
            contained within an AST, including strings.
            """
            lines = pprint.pformat(
                node, width=max(max_width - len(cur_indent), 1)
            ).splitlines(True)
            result.append(lines[0])
            result.extend([cur_indent + line for line in lines[1:]])
            return len(lines) != 1

        # pylint: disable=unused-variable; doesn't understand singledispatch
        @_repr_tree.register(tuple)
        @_repr_tree.register(list)
        def _repr_seq(node, result, done, cur_indent="", depth=1):
            """Outputs a representation of a sequence that's contained within an AST."""
            cur_indent += indent
            result.append("[")
            if not node:
                broken = False
            elif len(node) == 1:
                broken = _repr_tree(node[0], result, done, cur_indent, depth)
            elif len(node) == 2:
                broken = _repr_tree(node[0], result, done, cur_indent, depth)
                if not broken:
                    result.append(", ")
                else:
                    result.append(",\n")
                    result.append(cur_indent)
                broken = _repr_tree(node[1], result, done, cur_indent, depth) or broken
            else:
                result.append("\n")
                result.append(cur_indent)
                for child in node[:-1]:
                    _repr_tree(child, result, done, cur_indent, depth)
                    result.append(",\n")
                    result.append(cur_indent)
                _repr_tree(node[-1], result, done, cur_indent, depth)
                broken = True
            result.append("]")
            return broken

        # pylint: disable=unused-variable; doesn't understand singledispatch
        @_repr_tree.register(NodeNG)
        def _repr_node(node, result, done, cur_indent="", depth=1):
            """Outputs a strings representation of an astroid node."""
            if node in done:
                result.append(
                    indent
                    + "<Recursion on %s with id=%s" % (type(node).__name__, id(node))
                )
                return False
            done.add(node)

            if max_depth and depth > max_depth:
                result.append("...")
                return False
            depth += 1
            cur_indent += indent
            if ids:
                result.append("%s<0x%x>(\n" % (type(node).__name__, id(node)))
            else:
                result.append("%s(" % type(node).__name__)
            fields = []
            if include_linenos:
                fields.extend(("lineno", "col_offset"))
            fields.extend(node._other_fields)
            fields.extend(node._astroid_fields)
            if ast_state:
                fields.extend(node._other_other_fields)
            if not fields:
                broken = False
            elif len(fields) == 1:
                result.append("%s=" % fields[0])
                broken = _repr_tree(
                    getattr(node, fields[0]), result, done, cur_indent, depth
                )
            else:
                result.append("\n")
                result.append(cur_indent)
                for field in fields[:-1]:
                    result.append("%s=" % field)
                    _repr_tree(getattr(node, field), result, done, cur_indent, depth)
                    result.append(",\n")
                    result.append(cur_indent)
                result.append("%s=" % fields[-1])
                _repr_tree(getattr(node, fields[-1]), result, done, cur_indent, depth)
                broken = True
            result.append(")")
            return broken

        result = []
        _repr_tree(self, result, set())
        return "".join(result)

    def bool_value(self):
        """Determine the boolean value of this node.

        The boolean value of a node can have three
        possible values:

            * False: For instance, empty data structures,
              False, empty strings, instances which return
              explicitly False from the __nonzero__ / __bool__
              method.
            * True: Most of constructs are True by default:
              classes, functions, modules etc
            * Uninferable: The inference engine is uncertain of the
              node's value.

        :returns: The boolean value of this node.
        :rtype: bool or Uninferable
        """
        return util.Uninferable

    def op_precedence(self):
        # Look up by class name or default to highest precedence
        return OP_PRECEDENCE.get(self.__class__.__name__, len(OP_PRECEDENCE))

    def op_left_associative(self):
        # Everything is left associative except `**` and IfExp
        return True


class Statement(NodeNG):
    """Statement node adding a few attributes"""

    is_statement = True
    """Whether this node indicates a statement.

    :type: bool
    """

    def next_sibling(self):
        """The next sibling statement node.

        :returns: The next sibling statement node.
        :rtype: NodeNG or None
        """
        stmts = self.parent.child_sequence(self)
        index = stmts.index(self)
        try:
            return stmts[index + 1]
        except IndexError:
            pass

    def previous_sibling(self):
        """The previous sibling statement.

        :returns: The previous sibling statement node.
        :rtype: NodeNG or None
        """
        stmts = self.parent.child_sequence(self)
        index = stmts.index(self)
        if index >= 1:
            return stmts[index - 1]
        return None


class _BaseContainer(
    mixins.ParentAssignTypeMixin, NodeNG, bases.Instance, metaclass=abc.ABCMeta
):
    """Base class for Set, FrozenSet, Tuple and List."""

    _astroid_fields = ("elts",)

    def __init__(self, lineno=None, col_offset=None, parent=None):
        """
        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.elts = []
        """The elements in the node.

        :type: list(NodeNG)
        """

        super(_BaseContainer, self).__init__(lineno, col_offset, parent)

    def postinit(self, elts):
        """Do some setup after initialisation.

        :param elts: The list of elements the that node contains.
        :type elts: list(NodeNG)
        """
        self.elts = elts

    @classmethod
    def from_elements(cls, elts=None):
        """Create a node of this type from the given list of elements.

        :param elts: The list of elements that the node should contain.
        :type elts: list(NodeNG)

        :returns: A new node containing the given elements.
        :rtype: NodeNG
        """
        node = cls()
        if elts is None:
            node.elts = []
        else:
            node.elts = [const_factory(e) if _is_const(e) else e for e in elts]
        return node

    def itered(self):
        """An iterator over the elements this node contains.

        :returns: The contents of this node.
        :rtype: iterable(NodeNG)
        """
        return self.elts

    def bool_value(self):
        """Determine the boolean value of this node.

        :returns: The boolean value of this node.
        :rtype: bool or Uninferable
        """
        return bool(self.elts)

    @abc.abstractmethod
    def pytype(self):
        """Get the name of the type that this node represents.

        :returns: The name of the type.
        :rtype: str
        """

    def get_children(self):
        yield from self.elts


class LookupMixIn:
    """Mixin to look up a name in the right scope."""

    @lru_cache(maxsize=None)
    def lookup(self, name):
        """Lookup where the given variable is assigned.

        The lookup starts from self's scope. If self is not a frame itself
        and the name is found in the inner frame locals, statements will be
        filtered to remove ignorable statements according to self's location.

        :param name: The name of the variable to find assignments for.
        :type name: str

        :returns: The scope node and the list of assignments associated to the
            given name according to the scope where it has been found (locals,
            globals or builtin).
        :rtype: tuple(str, list(NodeNG))
        """
        return self.scope().scope_lookup(self, name)

    def ilookup(self, name):
        """Lookup the inferred values of the given variable.

        :param name: The variable name to find values for.
        :type name: str

        :returns: The inferred values of the statements returned from
            :meth:`lookup`.
        :rtype: iterable
        """
        frame, stmts = self.lookup(name)
        context = contextmod.InferenceContext()
        return bases._infer_stmts(stmts, context, frame)

    def _get_filtered_node_statements(self, nodes):
        statements = [(node, node.statement()) for node in nodes]
        # Next we check if we have ExceptHandlers that are parent
        # of the underlying variable, in which case the last one survives
        if len(statements) > 1 and all(
            isinstance(stmt, ExceptHandler) for _, stmt in statements
        ):
            statements = [
                (node, stmt) for node, stmt in statements if stmt.parent_of(self)
            ]
        return statements

    def _filter_stmts(self, stmts, frame, offset):
        """Filter the given list of statements to remove ignorable statements.

        If self is not a frame itself and the name is found in the inner
        frame locals, statements will be filtered to remove ignorable
        statements according to self's location.

        :param stmts: The statements to filter.
        :type stmts: list(NodeNG)

        :param frame: The frame that all of the given statements belong to.
        :type frame: NodeNG

        :param offset: The line offset to filter statements up to.
        :type offset: int

        :returns: The filtered statements.
        :rtype: list(NodeNG)
        """
        # if offset == -1, my actual frame is not the inner frame but its parent
        #
        # class A(B): pass
        #
        # we need this to resolve B correctly
        if offset == -1:
            myframe = self.frame().parent.frame()
        else:
            myframe = self.frame()
            # If the frame of this node is the same as the statement
            # of this node, then the node is part of a class or
            # a function definition and the frame of this node should be the
            # the upper frame, not the frame of the definition.
            # For more information why this is important,
            # see Pylint issue #295.
            # For example, for 'b', the statement is the same
            # as the frame / scope:
            #
            # def test(b=1):
            #     ...

            if self.statement() is myframe and myframe.parent:
                myframe = myframe.parent.frame()
        mystmt = self.statement()
        # line filtering if we are in the same frame
        #
        # take care node may be missing lineno information (this is the case for
        # nodes inserted for living objects)
        if myframe is frame and mystmt.fromlineno is not None:
            assert mystmt.fromlineno is not None, mystmt
            mylineno = mystmt.fromlineno + offset
        else:
            # disabling lineno filtering
            mylineno = 0

        _stmts = []
        _stmt_parents = []
        statements = self._get_filtered_node_statements(stmts)

        for node, stmt in statements:
            # line filtering is on and we have reached our location, break
            if stmt.fromlineno > mylineno > 0:
                break
            # Ignore decorators with the same name as the
            # decorated function
            # Fixes issue #375
            if mystmt is stmt and is_from_decorator(self):
                continue
            assert hasattr(node, "assign_type"), (
                node,
                node.scope(),
                node.scope().locals,
            )
            assign_type = node.assign_type()
            if node.has_base(self):
                break

            _stmts, done = assign_type._get_filtered_stmts(self, node, _stmts, mystmt)
            if done:
                break

            optional_assign = assign_type.optional_assign
            if optional_assign and assign_type.parent_of(self):
                # we are inside a loop, loop var assignment is hiding previous
                # assignment
                _stmts = [node]
                _stmt_parents = [stmt.parent]
                continue

            if isinstance(assign_type, NamedExpr):
                _stmts = [node]
                continue

            # XXX comment various branches below!!!
            try:
                pindex = _stmt_parents.index(stmt.parent)
            except ValueError:
                pass
            else:
                # we got a parent index, this means the currently visited node
                # is at the same block level as a previously visited node
                if _stmts[pindex].assign_type().parent_of(assign_type):
                    # both statements are not at the same block level
                    continue
                # if currently visited node is following previously considered
                # assignment and both are not exclusive, we can drop the
                # previous one. For instance in the following code ::
                #
                #   if a:
                #     x = 1
                #   else:
                #     x = 2
                #   print x
                #
                # we can't remove neither x = 1 nor x = 2 when looking for 'x'
                # of 'print x'; while in the following ::
                #
                #   x = 1
                #   x = 2
                #   print x
                #
                # we can remove x = 1 when we see x = 2
                #
                # moreover, on loop assignment types, assignment won't
                # necessarily be done if the loop has no iteration, so we don't
                # want to clear previous assignments if any (hence the test on
                # optional_assign)
                if not (optional_assign or are_exclusive(_stmts[pindex], node)):
                    if (
                        # In case of partial function node, if the statement is different
                        # from the origin function then it can be deleted otherwise it should
                        # remain to be able to correctly infer the call to origin function.
                        not node.is_function
                        or node.qname() != "PartialFunction"
                        or node.name != _stmts[pindex].name
                    ):
                        del _stmt_parents[pindex]
                        del _stmts[pindex]
            if isinstance(node, AssignName):
                if not optional_assign and stmt.parent is mystmt.parent:
                    _stmts = []
                    _stmt_parents = []
            elif isinstance(node, DelName):
                _stmts = []
                _stmt_parents = []
                continue
            if not are_exclusive(self, node):
                _stmts.append(node)
                _stmt_parents.append(stmt.parent)
        return _stmts


# Name classes


class AssignName(
    mixins.NoChildrenMixin, LookupMixIn, mixins.ParentAssignTypeMixin, NodeNG
):
    """Variation of :class:`ast.Assign` representing assignment to a name.

    An :class:`AssignName` is the name of something that is assigned to.
    This includes variables defined in a function signature or in a loop.

    >>> node = astroid.extract_node('variable = range(10)')
    >>> node
    <Assign l.1 at 0x7effe1db8550>
    >>> list(node.get_children())
    [<AssignName.variable l.1 at 0x7effe1db8748>, <Call l.1 at 0x7effe1db8630>]
    >>> list(node.get_children())[0].as_string()
    'variable'
    """

    _other_fields = ("name",)

    def __init__(self, name=None, lineno=None, col_offset=None, parent=None):
        """
        :param name: The name that is assigned to.
        :type name: str or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.name = name
        """The name that is assigned to.

        :type: str or None
        """

        super(AssignName, self).__init__(lineno, col_offset, parent)


class DelName(
    mixins.NoChildrenMixin, LookupMixIn, mixins.ParentAssignTypeMixin, NodeNG
):
    """Variation of :class:`ast.Delete` representing deletion of a name.

    A :class:`DelName` is the name of something that is deleted.

    >>> node = astroid.extract_node("del variable #@")
    >>> list(node.get_children())
    [<DelName.variable l.1 at 0x7effe1da4d30>]
    >>> list(node.get_children())[0].as_string()
    'variable'
    """

    _other_fields = ("name",)

    def __init__(self, name=None, lineno=None, col_offset=None, parent=None):
        """
        :param name: The name that is being deleted.
        :type name: str or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.name = name
        """The name that is being deleted.

        :type: str or None
        """

        super(DelName, self).__init__(lineno, col_offset, parent)


class Name(mixins.NoChildrenMixin, LookupMixIn, NodeNG):
    """Class representing an :class:`ast.Name` node.

    A :class:`Name` node is something that is named, but not covered by
    :class:`AssignName` or :class:`DelName`.

    >>> node = astroid.extract_node('range(10)')
    >>> node
    <Call l.1 at 0x7effe1db8710>
    >>> list(node.get_children())
    [<Name.range l.1 at 0x7effe1db86a0>, <Const.int l.1 at 0x7effe1db8518>]
    >>> list(node.get_children())[0].as_string()
    'range'
    """

    _other_fields = ("name",)

    def __init__(self, name=None, lineno=None, col_offset=None, parent=None):
        """
        :param name: The name that this node refers to.
        :type name: str or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.name = name
        """The name that this node refers to.

        :type: str or None
        """

        super(Name, self).__init__(lineno, col_offset, parent)

    def _get_name_nodes(self):
        yield self

        for child_node in self.get_children():
            yield from child_node._get_name_nodes()


class Arguments(mixins.AssignTypeMixin, NodeNG):
    """Class representing an :class:`ast.arguments` node.

    An :class:`Arguments` node represents that arguments in a
    function definition.

    >>> node = astroid.extract_node('def foo(bar): pass')
    >>> node
    <FunctionDef.foo l.1 at 0x7effe1db8198>
    >>> node.args
    <Arguments l.1 at 0x7effe1db82e8>
    """

    # Python 3.4+ uses a different approach regarding annotations,
    # each argument is a new class, _ast.arg, which exposes an
    # 'annotation' attribute. In astroid though, arguments are exposed
    # as is in the Arguments node and the only way to expose annotations
    # is by using something similar with Python 3.3:
    #  - we expose 'varargannotation' and 'kwargannotation' of annotations
    #    of varargs and kwargs.
    #  - we expose 'annotation', a list with annotations for
    #    for each normal argument. If an argument doesn't have an
    #    annotation, its value will be None.

    _astroid_fields = (
        "args",
        "defaults",
        "kwonlyargs",
        "posonlyargs",
        "kw_defaults",
        "annotations",
        "varargannotation",
        "kwargannotation",
        "kwonlyargs_annotations",
        "type_comment_args",
    )
    varargannotation = None
    """The type annotation for the variable length arguments.

    :type: NodeNG
    """
    kwargannotation = None
    """The type annotation for the variable length keyword arguments.

    :type: NodeNG
    """

    _other_fields = ("vararg", "kwarg")

    def __init__(self, vararg=None, kwarg=None, parent=None):
        """
        :param vararg: The name of the variable length arguments.
        :type vararg: str or None

        :param kwarg: The name of the variable length keyword arguments.
        :type kwarg: str or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        super(Arguments, self).__init__(parent=parent)
        self.vararg = vararg
        """The name of the variable length arguments.

        :type: str or None
        """

        self.kwarg = kwarg
        """The name of the variable length keyword arguments.

        :type: str or None
        """

        self.args = []
        """The names of the required arguments.

        :type: list(AssignName)
        """

        self.defaults = []
        """The default values for arguments that can be passed positionally.

        :type: list(NodeNG)
        """

        self.kwonlyargs = []
        """The keyword arguments that cannot be passed positionally.

        :type: list(AssignName)
        """

        self.posonlyargs = []
        """The arguments that can only be passed positionally.

        :type: list(AssignName)
        """

        self.kw_defaults = []
        """The default values for keyword arguments that cannot be passed positionally.

        :type: list(NodeNG)
        """

        self.annotations = []
        """The type annotations of arguments that can be passed positionally.

        :type: list(NodeNG)
        """

        self.posonlyargs_annotations = []
        """The type annotations of arguments that can only be passed positionally.

        :type: list(NodeNG)
        """

        self.kwonlyargs_annotations = []
        """The type annotations of arguments that cannot be passed positionally.

        :type: list(NodeNG)
        """

        self.type_comment_args = []
        """The type annotation, passed by a type comment, of each argument.

        If an argument does not have a type comment,
        the value for that argument will be None.

        :type: list(NodeNG or None)
        """

    # pylint: disable=too-many-arguments
    def postinit(
        self,
        args,
        defaults,
        kwonlyargs,
        kw_defaults,
        annotations,
        posonlyargs=None,
        kwonlyargs_annotations=None,
        posonlyargs_annotations=None,
        varargannotation=None,
        kwargannotation=None,
        type_comment_args=None,
    ):
        """Do some setup after initialisation.

        :param args: The names of the required arguments.
        :type args: list(AssignName)

        :param defaults: The default values for arguments that can be passed
            positionally.
        :type defaults: list(NodeNG)

        :param kwonlyargs: The keyword arguments that cannot be passed
            positionally.
        :type kwonlyargs: list(AssignName)

        :param posonlyargs: The arguments that can only be passed
            positionally.
        :type kwonlyargs: list(AssignName)

        :param kw_defaults: The default values for keyword arguments that
            cannot be passed positionally.
        :type kw_defaults: list(NodeNG)

        :param annotations: The type annotations of arguments that can be
            passed positionally.
        :type annotations: list(NodeNG)

        :param kwonlyargs_annotations: The type annotations of arguments that
            cannot be passed positionally. This should always be passed in
            Python 3.
        :type kwonlyargs_annotations: list(NodeNG)

        :param posonlyargs_annotations: The type annotations of arguments that
            can only be passed positionally. This should always be passed in
            Python 3.
        :type posonlyargs_annotations: list(NodeNG)

        :param varargannotation: The type annotation for the variable length
            arguments.
        :type varargannotation: NodeNG

        :param kwargannotation: The type annotation for the variable length
            keyword arguments.
        :type kwargannotation: NodeNG

        :param type_comment_args: The type annotation,
            passed by a type comment, of each argument.
        :type type_comment_args: list(NodeNG or None)
        """
        self.args = args
        self.defaults = defaults
        self.kwonlyargs = kwonlyargs
        self.posonlyargs = posonlyargs
        self.kw_defaults = kw_defaults
        self.annotations = annotations
        self.kwonlyargs_annotations = kwonlyargs_annotations
        self.posonlyargs_annotations = posonlyargs_annotations
        self.varargannotation = varargannotation
        self.kwargannotation = kwargannotation
        self.type_comment_args = type_comment_args

    # pylint: disable=too-many-arguments

    def _infer_name(self, frame, name):
        if self.parent is frame:
            return name
        return None

    @decorators.cachedproperty
    def fromlineno(self):
        """The first line that this node appears on in the source code.

        :type: int or None
        """
        lineno = super(Arguments, self).fromlineno
        return max(lineno, self.parent.fromlineno or 0)

    def format_args(self):
        """Get the arguments formatted as string.

        :returns: The formatted arguments.
        :rtype: str
        """
        result = []
        positional_only_defaults = []
        positional_or_keyword_defaults = self.defaults
        if self.defaults:
            args = self.args or []
            positional_or_keyword_defaults = self.defaults[-len(args) :]
            positional_only_defaults = self.defaults[: len(self.defaults) - len(args)]

        if self.posonlyargs:
            result.append(_format_args(self.posonlyargs, positional_only_defaults))
            result.append("/")
        if self.args:
            result.append(
                _format_args(
                    self.args,
                    positional_or_keyword_defaults,
                    getattr(self, "annotations", None),
                )
            )
        if self.vararg:
            result.append("*%s" % self.vararg)
        if self.kwonlyargs:
            if not self.vararg:
                result.append("*")
            result.append(
                _format_args(
                    self.kwonlyargs, self.kw_defaults, self.kwonlyargs_annotations
                )
            )
        if self.kwarg:
            result.append("**%s" % self.kwarg)
        return ", ".join(result)

    def default_value(self, argname):
        """Get the default value for an argument.

        :param argname: The name of the argument to get the default value for.
        :type argname: str

        :raises NoDefault: If there is no default value defined for the
            given argument.
        """
        args = list(itertools.chain((self.posonlyargs or ()), self.args or ()))
        index = _find_arg(argname, args)[0]
        if index is not None:
            idx = index - (len(args) - len(self.defaults))
            if idx >= 0:
                return self.defaults[idx]
        index = _find_arg(argname, self.kwonlyargs)[0]
        if index is not None and self.kw_defaults[index] is not None:
            return self.kw_defaults[index]
        raise exceptions.NoDefault(func=self.parent, name=argname)

    def is_argument(self, name):
        """Check if the given name is defined in the arguments.

        :param name: The name to check for.
        :type name: str

        :returns: True if the given name is defined in the arguments,
            False otherwise.
        :rtype: bool
        """
        if name == self.vararg:
            return True
        if name == self.kwarg:
            return True
        return (
            self.find_argname(name, rec=True)[1] is not None
            or self.kwonlyargs
            and _find_arg(name, self.kwonlyargs, rec=True)[1] is not None
        )

    def find_argname(self, argname, rec=False):
        """Get the index and :class:`AssignName` node for given name.

        :param argname: The name of the argument to search for.
        :type argname: str

        :param rec: Whether or not to include arguments in unpacked tuples
            in the search.
        :type rec: bool

        :returns: The index and node for the argument.
        :rtype: tuple(str or None, AssignName or None)
        """
        if (
            self.args or self.posonlyargs
        ):  # self.args may be None in some cases (builtin function)
            arguments = itertools.chain(self.posonlyargs or (), self.args or ())
            return _find_arg(argname, arguments, rec)
        return None, None

    def get_children(self):
        yield from self.posonlyargs or ()
        yield from self.args or ()

        yield from self.defaults
        yield from self.kwonlyargs

        for elt in self.kw_defaults:
            if elt is not None:
                yield elt

        for elt in self.annotations:
            if elt is not None:
                yield elt

        if self.varargannotation is not None:
            yield self.varargannotation

        if self.kwargannotation is not None:
            yield self.kwargannotation

        for elt in self.kwonlyargs_annotations:
            if elt is not None:
                yield elt


def _find_arg(argname, args, rec=False):
    for i, arg in enumerate(args):
        if isinstance(arg, Tuple):
            if rec:
                found = _find_arg(argname, arg.elts)
                if found[0] is not None:
                    return found
        elif arg.name == argname:
            return i, arg
    return None, None


def _format_args(args, defaults=None, annotations=None):
    values = []
    if args is None:
        return ""
    if annotations is None:
        annotations = []
    if defaults is not None:
        default_offset = len(args) - len(defaults)
    packed = itertools.zip_longest(args, annotations)
    for i, (arg, annotation) in enumerate(packed):
        if isinstance(arg, Tuple):
            values.append("(%s)" % _format_args(arg.elts))
        else:
            argname = arg.name
            default_sep = "="
            if annotation is not None:
                argname += ": " + annotation.as_string()
                default_sep = " = "
            values.append(argname)

            if defaults is not None and i >= default_offset:
                if defaults[i - default_offset] is not None:
                    values[-1] += default_sep + defaults[i - default_offset].as_string()
    return ", ".join(values)


class AssignAttr(mixins.ParentAssignTypeMixin, NodeNG):
    """Variation of :class:`ast.Assign` representing assignment to an attribute.

    >>> node = astroid.extract_node('self.attribute = range(10)')
    >>> node
    <Assign l.1 at 0x7effe1d521d0>
    >>> list(node.get_children())
    [<AssignAttr.attribute l.1 at 0x7effe1d52320>, <Call l.1 at 0x7effe1d522e8>]
    >>> list(node.get_children())[0].as_string()
    'self.attribute'
    """

    _astroid_fields = ("expr",)
    _other_fields = ("attrname",)
    expr = None
    """What has the attribute that is being assigned to.

    :type: NodeNG or None
    """

    def __init__(self, attrname=None, lineno=None, col_offset=None, parent=None):
        """
        :param attrname: The name of the attribute being assigned to.
        :type attrname: str or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.attrname = attrname
        """The name of the attribute being assigned to.

        :type: str or None
        """

        super(AssignAttr, self).__init__(lineno, col_offset, parent)

    def postinit(self, expr=None):
        """Do some setup after initialisation.

        :param expr: What has the attribute that is being assigned to.
        :type expr: NodeNG or None
        """
        self.expr = expr

    def get_children(self):
        yield self.expr


class Assert(Statement):
    """Class representing an :class:`ast.Assert` node.

    An :class:`Assert` node represents an assert statement.

    >>> node = astroid.extract_node('assert len(things) == 10, "Not enough things"')
    >>> node
    <Assert l.1 at 0x7effe1d527b8>
    """

    _astroid_fields = ("test", "fail")
    test = None
    """The test that passes or fails the assertion.

    :type: NodeNG or None
    """
    fail = None
    """The message shown when the assertion fails.

    :type: NodeNG or None
    """

    def postinit(self, test=None, fail=None):
        """Do some setup after initialisation.

        :param test: The test that passes or fails the assertion.
        :type test: NodeNG or None

        :param fail: The message shown when the assertion fails.
        :type fail: NodeNG or None
        """
        self.fail = fail
        self.test = test

    def get_children(self):
        yield self.test

        if self.fail is not None:
            yield self.fail


class Assign(mixins.AssignTypeMixin, Statement):
    """Class representing an :class:`ast.Assign` node.

    An :class:`Assign` is a statement where something is explicitly
    asssigned to.

    >>> node = astroid.extract_node('variable = range(10)')
    >>> node
    <Assign l.1 at 0x7effe1db8550>
    """

    _astroid_fields = ("targets", "value")
    _other_other_fields = ("type_annotation",)
    targets = None
    """What is being assigned to.

    :type: list(NodeNG) or None
    """
    value = None
    """The value being assigned to the variables.

    :type: NodeNG or None
    """
    type_annotation = None
    """If present, this will contain the type annotation passed by a type comment

    :type: NodeNG or None
    """

    def postinit(self, targets=None, value=None, type_annotation=None):
        """Do some setup after initialisation.

        :param targets: What is being assigned to.
        :type targets: list(NodeNG) or None

        :param value: The value being assigned to the variables.
        :type: NodeNG or None
        """
        self.targets = targets
        self.value = value
        self.type_annotation = type_annotation

    def get_children(self):
        yield from self.targets

        yield self.value

    @decorators.cached
    def _get_assign_nodes(self):
        return [self] + list(self.value._get_assign_nodes())

    def _get_yield_nodes_skip_lambdas(self):
        yield from self.value._get_yield_nodes_skip_lambdas()


class AnnAssign(mixins.AssignTypeMixin, Statement):
    """Class representing an :class:`ast.AnnAssign` node.

    An :class:`AnnAssign` is an assignment with a type annotation.

    >>> node = astroid.extract_node('variable: List[int] = range(10)')
    >>> node
    <AnnAssign l.1 at 0x7effe1d4c630>
    """

    _astroid_fields = ("target", "annotation", "value")
    _other_fields = ("simple",)
    target = None
    """What is being assigned to.

    :type: NodeNG or None
    """
    annotation = None
    """The type annotation of what is being assigned to.

    :type: NodeNG
    """
    value = None
    """The value being assigned to the variables.

    :type: NodeNG or None
    """
    simple = None
    """Whether :attr:`target` is a pure name or a complex statement.

    :type: int
    """

    def postinit(self, target, annotation, simple, value=None):
        """Do some setup after initialisation.

        :param target: What is being assigned to.
        :type target: NodeNG

        :param annotation: The type annotation of what is being assigned to.
        :type: NodeNG

        :param simple: Whether :attr:`target` is a pure name
            or a complex statement.
        :type simple: int

        :param value: The value being assigned to the variables.
        :type: NodeNG or None
        """
        self.target = target
        self.annotation = annotation
        self.value = value
        self.simple = simple

    def get_children(self):
        yield self.target
        yield self.annotation

        if self.value is not None:
            yield self.value


class AugAssign(mixins.AssignTypeMixin, Statement):
    """Class representing an :class:`ast.AugAssign` node.

    An :class:`AugAssign` is an assignment paired with an operator.

    >>> node = astroid.extract_node('variable += 1')
    >>> node
    <AugAssign l.1 at 0x7effe1db4d68>
    """

    _astroid_fields = ("target", "value")
    _other_fields = ("op",)
    target = None
    """What is being assigned to.

    :type: NodeNG or None
    """
    value = None
    """The value being assigned to the variable.

    :type: NodeNG or None
    """

    def __init__(self, op=None, lineno=None, col_offset=None, parent=None):
        """
        :param op: The operator that is being combined with the assignment.
            This includes the equals sign.
        :type op: str or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.op = op
        """The operator that is being combined with the assignment.

        This includes the equals sign.

        :type: str or None
        """

        super(AugAssign, self).__init__(lineno, col_offset, parent)

    def postinit(self, target=None, value=None):
        """Do some setup after initialisation.

        :param target: What is being assigned to.
        :type target: NodeNG or None

        :param value: The value being assigned to the variable.
        :type: NodeNG or None
        """
        self.target = target
        self.value = value

    # This is set by inference.py
    def _infer_augassign(self, context=None):
        raise NotImplementedError

    def type_errors(self, context=None):
        """Get a list of type errors which can occur during inference.

        Each TypeError is represented by a :class:`BadBinaryOperationMessage` ,
        which holds the original exception.

        :returns: The list of possible type errors.
        :rtype: list(BadBinaryOperationMessage)
        """
        try:
            results = self._infer_augassign(context=context)
            return [
                result
                for result in results
                if isinstance(result, util.BadBinaryOperationMessage)
            ]
        except exceptions.InferenceError:
            return []

    def get_children(self):
        yield self.target
        yield self.value


class Repr(NodeNG):
    """Class representing an :class:`ast.Repr` node.

    A :class:`Repr` node represents the backtick syntax,
    which is a deprecated alias for :func:`repr` removed in Python 3.

    >>> node = astroid.extract_node('`variable`')
    >>> node
    <Repr l.1 at 0x7fa0951d75d0>
    """

    _astroid_fields = ("value",)
    value = None
    """What is having :func:`repr` called on it.

    :type: NodeNG or None
    """

    def postinit(self, value=None):
        """Do some setup after initialisation.

        :param value: What is having :func:`repr` called on it.
        :type value: NodeNG or None
        """
        self.value = value


class BinOp(NodeNG):
    """Class representing an :class:`ast.BinOp` node.

    A :class:`BinOp` node is an application of a binary operator.

    >>> node = astroid.extract_node('a + b')
    >>> node
    <BinOp l.1 at 0x7f23b2e8cfd0>
    """

    _astroid_fields = ("left", "right")
    _other_fields = ("op",)
    left = None
    """What is being applied to the operator on the left side.

    :type: NodeNG or None
    """
    right = None
    """What is being applied to the operator on the right side.

    :type: NodeNG or None
    """

    def __init__(self, op=None, lineno=None, col_offset=None, parent=None):
        """
        :param op: The operator.
        :type: str or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.op = op
        """The operator.

        :type: str or None
        """

        super(BinOp, self).__init__(lineno, col_offset, parent)

    def postinit(self, left=None, right=None):
        """Do some setup after initialisation.

        :param left: What is being applied to the operator on the left side.
        :type left: NodeNG or None

        :param right: What is being applied to the operator on the right side.
        :type right: NodeNG or None
        """
        self.left = left
        self.right = right

    # This is set by inference.py
    def _infer_binop(self, context=None):
        raise NotImplementedError

    def type_errors(self, context=None):
        """Get a list of type errors which can occur during inference.

        Each TypeError is represented by a :class:`BadBinaryOperationMessage`,
        which holds the original exception.

        :returns: The list of possible type errors.
        :rtype: list(BadBinaryOperationMessage)
        """
        try:
            results = self._infer_binop(context=context)
            return [
                result
                for result in results
                if isinstance(result, util.BadBinaryOperationMessage)
            ]
        except exceptions.InferenceError:
            return []

    def get_children(self):
        yield self.left
        yield self.right

    def op_precedence(self):
        return OP_PRECEDENCE[self.op]

    def op_left_associative(self):
        # 2**3**4 == 2**(3**4)
        return self.op != "**"


class BoolOp(NodeNG):
    """Class representing an :class:`ast.BoolOp` node.

    A :class:`BoolOp` is an application of a boolean operator.

    >>> node = astroid.extract_node('a and b')
    >>> node
    <BinOp l.1 at 0x7f23b2e71c50>
    """

    _astroid_fields = ("values",)
    _other_fields = ("op",)
    values = None
    """The values being applied to the operator.

    :type: list(NodeNG) or None
    """

    def __init__(self, op=None, lineno=None, col_offset=None, parent=None):
        """
        :param op: The operator.
        :type: str or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.op = op
        """The operator.

        :type: str or None
        """

        super(BoolOp, self).__init__(lineno, col_offset, parent)

    def postinit(self, values=None):
        """Do some setup after initialisation.

        :param values: The values being applied to the operator.
        :type values: list(NodeNG) or None
        """
        self.values = values

    def get_children(self):
        yield from self.values

    def op_precedence(self):
        return OP_PRECEDENCE[self.op]


class Break(mixins.NoChildrenMixin, Statement):
    """Class representing an :class:`ast.Break` node.

    >>> node = astroid.extract_node('break')
    >>> node
    <Break l.1 at 0x7f23b2e9e5c0>
    """


class Call(NodeNG):
    """Class representing an :class:`ast.Call` node.

    A :class:`Call` node is a call to a function, method, etc.

    >>> node = astroid.extract_node('function()')
    >>> node
    <Call l.1 at 0x7f23b2e71eb8>
    """

    _astroid_fields = ("func", "args", "keywords")
    func = None
    """What is being called.

    :type: NodeNG or None
    """
    args = None
    """The positional arguments being given to the call.

    :type: list(NodeNG) or None
    """
    keywords = None
    """The keyword arguments being given to the call.

    :type: list(NodeNG) or None
    """

    def postinit(self, func=None, args=None, keywords=None):
        """Do some setup after initialisation.

        :param func: What is being called.
        :type func: NodeNG or None

        :param args: The positional arguments being given to the call.
        :type args: list(NodeNG) or None

        :param keywords: The keyword arguments being given to the call.
        :type keywords: list(NodeNG) or None
        """
        self.func = func
        self.args = args
        self.keywords = keywords

    @property
    def starargs(self):
        """The positional arguments that unpack something.

        :type: list(Starred)
        """
        args = self.args or []
        return [arg for arg in args if isinstance(arg, Starred)]

    @property
    def kwargs(self):
        """The keyword arguments that unpack something.

        :type: list(Keyword)
        """
        keywords = self.keywords or []
        return [keyword for keyword in keywords if keyword.arg is None]

    def get_children(self):
        yield self.func

        yield from self.args

        yield from self.keywords or ()


class Compare(NodeNG):
    """Class representing an :class:`ast.Compare` node.

    A :class:`Compare` node indicates a comparison.

    >>> node = astroid.extract_node('a <= b <= c')
    >>> node
    <Compare l.1 at 0x7f23b2e9e6d8>
    >>> node.ops
    [('<=', <Name.b l.1 at 0x7f23b2e9e2b0>), ('<=', <Name.c l.1 at 0x7f23b2e9e390>)]
    """

    _astroid_fields = ("left", "ops")
    left = None
    """The value at the left being applied to a comparison operator.

    :type: NodeNG or None
    """
    ops = None
    """The remainder of the operators and their relevant right hand value.

    :type: list(tuple(str, NodeNG)) or None
    """

    def postinit(self, left=None, ops=None):
        """Do some setup after initialisation.

        :param left: The value at the left being applied to a comparison
            operator.
        :type left: NodeNG or None

        :param ops: The remainder of the operators
            and their relevant right hand value.
        :type ops: list(tuple(str, NodeNG)) or None
        """
        self.left = left
        self.ops = ops

    def get_children(self):
        """Get the child nodes below this node.

        Overridden to handle the tuple fields and skip returning the operator
        strings.

        :returns: The children.
        :rtype: iterable(NodeNG)
        """
        yield self.left
        for _, comparator in self.ops:
            yield comparator  # we don't want the 'op'

    def last_child(self):
        """An optimized version of list(get_children())[-1]

        :returns: The last child.
        :rtype: NodeNG
        """
        # XXX maybe if self.ops:
        return self.ops[-1][1]
        # return self.left


class Comprehension(NodeNG):
    """Class representing an :class:`ast.comprehension` node.

    A :class:`Comprehension` indicates the loop inside any type of
    comprehension including generator expressions.

    >>> node = astroid.extract_node('[x for x in some_values]')
    >>> list(node.get_children())
    [<Name.x l.1 at 0x7f23b2e352b0>, <Comprehension l.1 at 0x7f23b2e35320>]
    >>> list(node.get_children())[1].as_string()
    'for x in some_values'
    """

    _astroid_fields = ("target", "iter", "ifs")
    _other_fields = ("is_async",)
    target = None
    """What is assigned to by the comprehension.

    :type: NodeNG or None
    """
    iter = None
    """What is iterated over by the comprehension.

    :type: NodeNG or None
    """
    ifs = None
    """The contents of any if statements that filter the comprehension.

    :type: list(NodeNG) or None
    """
    is_async = None
    """Whether this is an asynchronous comprehension or not.

    :type: bool or None
    """

    def __init__(self, parent=None):
        """
        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        super(Comprehension, self).__init__()
        self.parent = parent

    # pylint: disable=redefined-builtin; same name as builtin ast module.
    def postinit(self, target=None, iter=None, ifs=None, is_async=None):
        """Do some setup after initialisation.

        :param target: What is assigned to by the comprehension.
        :type target: NodeNG or None

        :param iter: What is iterated over by the comprehension.
        :type iter: NodeNG or None

        :param ifs: The contents of any if statements that filter
            the comprehension.
        :type ifs: list(NodeNG) or None

        :param is_async: Whether this is an asynchronous comprehension or not.
        :type: bool or None
        """
        self.target = target
        self.iter = iter
        self.ifs = ifs
        self.is_async = is_async

    optional_assign = True
    """Whether this node optionally assigns a variable.

    :type: bool
    """

    def assign_type(self):
        """The type of assignment that this node performs.

        :returns: The assignment type.
        :rtype: NodeNG
        """
        return self

    def _get_filtered_stmts(self, lookup_node, node, stmts, mystmt):
        """method used in filter_stmts"""
        if self is mystmt:
            if isinstance(lookup_node, (Const, Name)):
                return [lookup_node], True

        elif self.statement() is mystmt:
            # original node's statement is the assignment, only keeps
            # current node (gen exp, list comp)

            return [node], True

        return stmts, False

    def get_children(self):
        yield self.target
        yield self.iter

        yield from self.ifs


class Const(mixins.NoChildrenMixin, NodeNG, bases.Instance):
    """Class representing any constant including num, str, bool, None, bytes.

    >>> node = astroid.extract_node('(5, "This is a string.", True, None, b"bytes")')
    >>> node
    <Tuple.tuple l.1 at 0x7f23b2e358d0>
    >>> list(node.get_children())
    [<Const.int l.1 at 0x7f23b2e35940>,
    <Const.str l.1 at 0x7f23b2e35978>,
    <Const.bool l.1 at 0x7f23b2e359b0>,
    <Const.NoneType l.1 at 0x7f23b2e359e8>,
    <Const.bytes l.1 at 0x7f23b2e35a20>]
    """

    _other_fields = ("value",)

    def __init__(self, value, lineno=None, col_offset=None, parent=None):
        """
        :param value: The value that the constant represents.
        :type value: object

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.value = value
        """The value that the constant represents.

        :type: object
        """

        super(Const, self).__init__(lineno, col_offset, parent)

    def __getattr__(self, name):
        # This is needed because of Proxy's __getattr__ method.
        # Calling object.__new__ on this class without calling
        # __init__ would result in an infinite loop otherwise
        # since __getattr__ is called when an attribute doesn't
        # exist and self._proxied indirectly calls self.value
        # and Proxy __getattr__ calls self.value
        if name == "value":
            raise AttributeError
        return super().__getattr__(name)

    def getitem(self, index, context=None):
        """Get an item from this node if subscriptable.

        :param index: The node to use as a subscript index.
        :type index: Const or Slice

        :raises AstroidTypeError: When the given index cannot be used as a
            subscript index, or if this node is not subscriptable.
        """
        if isinstance(index, Const):
            index_value = index.value
        elif isinstance(index, Slice):
            index_value = _infer_slice(index, context=context)

        else:
            raise exceptions.AstroidTypeError(
                "Could not use type {} as subscript index".format(type(index))
            )

        try:
            if isinstance(self.value, (str, bytes)):
                return Const(self.value[index_value])
        except IndexError as exc:
            raise exceptions.AstroidIndexError(
                message="Index {index!r} out of range",
                node=self,
                index=index,
                context=context,
            ) from exc
        except TypeError as exc:
            raise exceptions.AstroidTypeError(
                message="Type error {error!r}", node=self, index=index, context=context
            ) from exc

        raise exceptions.AstroidTypeError("%r (value=%s)" % (self, self.value))

    def has_dynamic_getattr(self):
        """Check if the node has a custom __getattr__ or __getattribute__.

        :returns: True if the class has a custom
            __getattr__ or __getattribute__, False otherwise.
            For a :class:`Const` this is always ``False``.
        :rtype: bool
        """
        return False

    def itered(self):
        """An iterator over the elements this node contains.

        :returns: The contents of this node.
        :rtype: iterable(str)

        :raises TypeError: If this node does not represent something that is iterable.
        """
        if isinstance(self.value, str):
            return self.value
        raise TypeError()

    def pytype(self):
        """Get the name of the type that this node represents.

        :returns: The name of the type.
        :rtype: str
        """
        return self._proxied.qname()

    def bool_value(self):
        """Determine the boolean value of this node.

        :returns: The boolean value of this node.
        :rtype: bool
        """
        return bool(self.value)


class Continue(mixins.NoChildrenMixin, Statement):
    """Class representing an :class:`ast.Continue` node.

    >>> node = astroid.extract_node('continue')
    >>> node
    <Continue l.1 at 0x7f23b2e35588>
    """


class Decorators(NodeNG):
    """A node representing a list of decorators.

    A :class:`Decorators` is the decorators that are applied to
    a method or function.

    >>> node = astroid.extract_node('''
    @property
    def my_property(self):
        return 3
    ''')
    >>> node
    <FunctionDef.my_property l.2 at 0x7f23b2e35d30>
    >>> list(node.get_children())[0]
    <Decorators l.1 at 0x7f23b2e35d68>
    """

    _astroid_fields = ("nodes",)
    nodes = None
    """The decorators that this node contains.

    :type: list(Name or Call) or None
    """

    def postinit(self, nodes):
        """Do some setup after initialisation.

        :param nodes: The decorators that this node contains.
        :type nodes: list(Name or Call)
        """
        self.nodes = nodes

    def scope(self):
        """The first parent node defining a new scope.

        :returns: The first parent scope node.
        :rtype: Module or FunctionDef or ClassDef or Lambda or GenExpr
        """
        # skip the function node to go directly to the upper level scope
        return self.parent.parent.scope()

    def get_children(self):
        yield from self.nodes


class DelAttr(mixins.ParentAssignTypeMixin, NodeNG):
    """Variation of :class:`ast.Delete` representing deletion of an attribute.

    >>> node = astroid.extract_node('del self.attr')
    >>> node
    <Delete l.1 at 0x7f23b2e35f60>
    >>> list(node.get_children())[0]
    <DelAttr.attr l.1 at 0x7f23b2e411d0>
    """

    _astroid_fields = ("expr",)
    _other_fields = ("attrname",)
    expr = None
    """The name that this node represents.

    :type: Name or None
    """

    def __init__(self, attrname=None, lineno=None, col_offset=None, parent=None):
        """
        :param attrname: The name of the attribute that is being deleted.
        :type attrname: str or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.attrname = attrname
        """The name of the attribute that is being deleted.

        :type: str or None
        """

        super(DelAttr, self).__init__(lineno, col_offset, parent)

    def postinit(self, expr=None):
        """Do some setup after initialisation.

        :param expr: The name that this node represents.
        :type expr: Name or None
        """
        self.expr = expr

    def get_children(self):
        yield self.expr


class Delete(mixins.AssignTypeMixin, Statement):
    """Class representing an :class:`ast.Delete` node.

    A :class:`Delete` is a ``del`` statement this is deleting something.

    >>> node = astroid.extract_node('del self.attr')
    >>> node
    <Delete l.1 at 0x7f23b2e35f60>
    """

    _astroid_fields = ("targets",)
    targets = None
    """What is being deleted.

    :type: list(NodeNG) or None
    """

    def postinit(self, targets=None):
        """Do some setup after initialisation.

        :param targets: What is being deleted.
        :type targets: list(NodeNG) or None
        """
        self.targets = targets

    def get_children(self):
        yield from self.targets


class Dict(NodeNG, bases.Instance):
    """Class representing an :class:`ast.Dict` node.

    A :class:`Dict` is a dictionary that is created with ``{}`` syntax.

    >>> node = astroid.extract_node('{1: "1"}')
    >>> node
    <Dict.dict l.1 at 0x7f23b2e35cc0>
    """

    _astroid_fields = ("items",)

    def __init__(self, lineno=None, col_offset=None, parent=None):
        """
        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.items = []
        """The key-value pairs contained in the dictionary.

        :type: list(tuple(NodeNG, NodeNG))
        """

        super(Dict, self).__init__(lineno, col_offset, parent)

    def postinit(self, items):
        """Do some setup after initialisation.

        :param items: The key-value pairs contained in the dictionary.
        :type items: list(tuple(NodeNG, NodeNG))
        """
        self.items = items

    @classmethod
    def from_elements(cls, items=None):
        """Create a :class:`Dict` of constants from a live dictionary.

        :param items: The items to store in the node.
        :type items: dict

        :returns: The created dictionary node.
        :rtype: Dict
        """
        node = cls()
        if items is None:
            node.items = []
        else:
            node.items = [
                (const_factory(k), const_factory(v) if _is_const(v) else v)
                for k, v in items.items()
                # The keys need to be constants
                if _is_const(k)
            ]
        return node

    def pytype(self):
        """Get the name of the type that this node represents.

        :returns: The name of the type.
        :rtype: str
        """
        return "%s.dict" % BUILTINS

    def get_children(self):
        """Get the key and value nodes below this node.

        Children are returned in the order that they are defined in the source
        code, key first then the value.

        :returns: The children.
        :rtype: iterable(NodeNG)
        """
        for key, value in self.items:
            yield key
            yield value

    def last_child(self):
        """An optimized version of list(get_children())[-1]

        :returns: The last child, or None if no children exist.
        :rtype: NodeNG or None
        """
        if self.items:
            return self.items[-1][1]
        return None

    def itered(self):
        """An iterator over the keys this node contains.

        :returns: The keys of this node.
        :rtype: iterable(NodeNG)
        """
        return [key for (key, _) in self.items]

    def getitem(self, index, context=None):
        """Get an item from this node.

        :param index: The node to use as a subscript index.
        :type index: Const or Slice

        :raises AstroidTypeError: When the given index cannot be used as a
            subscript index, or if this node is not subscriptable.
        :raises AstroidIndexError: If the given index does not exist in the
            dictionary.
        """
        for key, value in self.items:
            # TODO(cpopa): no support for overriding yet, {1:2, **{1: 3}}.
            if isinstance(key, DictUnpack):
                try:
                    return value.getitem(index, context)
                except (exceptions.AstroidTypeError, exceptions.AstroidIndexError):
                    continue
            for inferredkey in key.infer(context):
                if inferredkey is util.Uninferable:
                    continue
                if isinstance(inferredkey, Const) and isinstance(index, Const):
                    if inferredkey.value == index.value:
                        return value

        raise exceptions.AstroidIndexError(index)

    def bool_value(self):
        """Determine the boolean value of this node.

        :returns: The boolean value of this node.
        :rtype: bool
        """
        return bool(self.items)


class Expr(Statement):
    """Class representing an :class:`ast.Expr` node.

    An :class:`Expr` is any expression that does not have its value used or
    stored.

    >>> node = astroid.extract_node('method()')
    >>> node
    <Call l.1 at 0x7f23b2e352b0>
    >>> node.parent
    <Expr l.1 at 0x7f23b2e35278>
    """

    _astroid_fields = ("value",)
    value = None
    """What the expression does.

    :type: NodeNG or None
    """

    def postinit(self, value=None):
        """Do some setup after initialisation.

        :param value: What the expression does.
        :type value: NodeNG or None
        """
        self.value = value

    def get_children(self):
        yield self.value

    def _get_yield_nodes_skip_lambdas(self):
        if not self.value.is_lambda:
            yield from self.value._get_yield_nodes_skip_lambdas()


class Ellipsis(mixins.NoChildrenMixin, NodeNG):  # pylint: disable=redefined-builtin
    """Class representing an :class:`ast.Ellipsis` node.

    An :class:`Ellipsis` is the ``...`` syntax.

    >>> node = astroid.extract_node('...')
    >>> node
    <Ellipsis l.1 at 0x7f23b2e35160>
    """

    def bool_value(self):
        """Determine the boolean value of this node.

        :returns: The boolean value of this node.
            For an :class:`Ellipsis` this is always ``True``.
        :rtype: bool
        """
        return True


class EmptyNode(mixins.NoChildrenMixin, NodeNG):
    """Holds an arbitrary object in the :attr:`LocalsDictNodeNG.locals`."""

    object = None


class ExceptHandler(mixins.MultiLineBlockMixin, mixins.AssignTypeMixin, Statement):
    """Class representing an :class:`ast.ExceptHandler`. node.

    An :class:`ExceptHandler` is an ``except`` block on a try-except.

    >>> node = astroid.extract_node('''
        try:
            do_something()
        except Exception as error:
            print("Error!")
        ''')
    >>> node
    <TryExcept l.2 at 0x7f23b2e9d908>
    >>> >>> node.handlers
    [<ExceptHandler l.4 at 0x7f23b2e9e860>]
    """

    _astroid_fields = ("type", "name", "body")
    _multi_line_block_fields = ("body",)
    type = None
    """The types that the block handles.

    :type: Tuple or NodeNG or None
    """
    name = None
    """The name that the caught exception is assigned to.

    :type: AssignName or None
    """
    body = None
    """The contents of the block.

    :type: list(NodeNG) or None
    """

    def get_children(self):
        if self.type is not None:
            yield self.type

        if self.name is not None:
            yield self.name

        yield from self.body

    # pylint: disable=redefined-builtin; had to use the same name as builtin ast module.
    def postinit(self, type=None, name=None, body=None):
        """Do some setup after initialisation.

        :param type: The types that the block handles.
        :type type: Tuple or NodeNG or None

        :param name: The name that the caught exception is assigned to.
        :type name: AssignName or None

        :param body:The contents of the block.
        :type body: list(NodeNG) or None
        """
        self.type = type
        self.name = name
        self.body = body

    @decorators.cachedproperty
    def blockstart_tolineno(self):
        """The line on which the beginning of this block ends.

        :type: int
        """
        if self.name:
            return self.name.tolineno
        if self.type:
            return self.type.tolineno
        return self.lineno

    def catch(self, exceptions):  # pylint: disable=redefined-outer-name
        """Check if this node handles any of the given exceptions.

        If ``exceptions`` is empty, this will default to ``True``.

        :param exceptions: The name of the exceptions to check for.
        :type exceptions: list(str)
        """
        if self.type is None or exceptions is None:
            return True
        for node in self.type._get_name_nodes():
            if node.name in exceptions:
                return True
        return False


class Exec(Statement):
    """Class representing the ``exec`` statement.

    >>> node = astroid.extract_node('exec "True"')
    >>> node
    <Exec l.1 at 0x7f0e8106c6d0>
    """

    _astroid_fields = ("expr", "globals", "locals")
    expr = None
    """The expression to be executed.

    :type: NodeNG or None
    """
    globals = None
    """The globals dictionary to execute with.

    :type: NodeNG or None
    """
    locals = None
    """The locals dictionary to execute with.

    :type: NodeNG or None
    """

    # pylint: disable=redefined-builtin; had to use the same name as builtin ast module.
    def postinit(self, expr=None, globals=None, locals=None):
        """Do some setup after initialisation.

        :param expr: The expression to be executed.
        :type expr: NodeNG or None

        :param globals:The globals dictionary to execute with.
        :type globals: NodeNG or None

        :param locals: The locals dictionary to execute with.
        :type locals: NodeNG or None
        """
        self.expr = expr
        self.globals = globals
        self.locals = locals


class ExtSlice(NodeNG):
    """Class representing an :class:`ast.ExtSlice` node.

    An :class:`ExtSlice` is a complex slice expression.

    >>> node = astroid.extract_node('l[1:3, 5]')
    >>> node
    <Subscript l.1 at 0x7f23b2e9e550>
    >>> node.slice
    <ExtSlice l.1 at 0x7f23b7b05ef0>
    """

    _astroid_fields = ("dims",)
    dims = None
    """The simple dimensions that form the complete slice.

    :type: list(NodeNG) or None
    """

    def postinit(self, dims=None):
        """Do some setup after initialisation.

        :param dims: The simple dimensions that form the complete slice.
        :type dims: list(NodeNG) or None
        """
        self.dims = dims


class For(
    mixins.MultiLineBlockMixin,
    mixins.BlockRangeMixIn,
    mixins.AssignTypeMixin,
    Statement,
):
    """Class representing an :class:`ast.For` node.

    >>> node = astroid.extract_node('for thing in things: print(thing)')
    >>> node
    <For l.1 at 0x7f23b2e8cf28>
    """

    _astroid_fields = ("target", "iter", "body", "orelse")
    _other_other_fields = ("type_annotation",)
    _multi_line_block_fields = ("body", "orelse")
    target = None
    """What the loop assigns to.

    :type: NodeNG or None
    """
    iter = None
    """What the loop iterates over.

    :type: NodeNG or None
    """
    body = None
    """The contents of the body of the loop.

    :type: list(NodeNG) or None
    """
    orelse = None
    """The contents of the ``else`` block of the loop.

    :type: list(NodeNG) or None
    """
    type_annotation = None
    """If present, this will contain the type annotation passed by a type comment

    :type: NodeNG or None
    """

    # pylint: disable=redefined-builtin; had to use the same name as builtin ast module.
    def postinit(
        self, target=None, iter=None, body=None, orelse=None, type_annotation=None
    ):
        """Do some setup after initialisation.

        :param target: What the loop assigns to.
        :type target: NodeNG or None

        :param iter: What the loop iterates over.
        :type iter: NodeNG or None

        :param body: The contents of the body of the loop.
        :type body: list(NodeNG) or None

        :param orelse: The contents of the ``else`` block of the loop.
        :type orelse: list(NodeNG) or None
        """
        self.target = target
        self.iter = iter
        self.body = body
        self.orelse = orelse
        self.type_annotation = type_annotation

    optional_assign = True
    """Whether this node optionally assigns a variable.

    This is always ``True`` for :class:`For` nodes.

    :type: bool
    """

    @decorators.cachedproperty
    def blockstart_tolineno(self):
        """The line on which the beginning of this block ends.

        :type: int
        """
        return self.iter.tolineno

    def get_children(self):
        yield self.target
        yield self.iter

        yield from self.body
        yield from self.orelse


class AsyncFor(For):
    """Class representing an :class:`ast.AsyncFor` node.

    An :class:`AsyncFor` is an asynchronous :class:`For` built with
    the ``async`` keyword.

    >>> node = astroid.extract_node('''
    async def func(things):
        async for thing in things:
            print(thing)
    ''')
    >>> node
    <AsyncFunctionDef.func l.2 at 0x7f23b2e416d8>
    >>> node.body[0]
    <AsyncFor l.3 at 0x7f23b2e417b8>
    """


class Await(NodeNG):
    """Class representing an :class:`ast.Await` node.

    An :class:`Await` is the ``await`` keyword.

    >>> node = astroid.extract_node('''
    async def func(things):
        await other_func()
    ''')
    >>> node
    <AsyncFunctionDef.func l.2 at 0x7f23b2e41748>
    >>> node.body[0]
    <Expr l.3 at 0x7f23b2e419e8>
    >>> list(node.body[0].get_children())[0]
    <Await l.3 at 0x7f23b2e41a20>
    """

    _astroid_fields = ("value",)
    value = None
    """What to wait for.

    :type: NodeNG or None
    """

    def postinit(self, value=None):
        """Do some setup after initialisation.

        :param value: What to wait for.
        :type value: NodeNG or None
        """
        self.value = value

    def get_children(self):
        yield self.value


class ImportFrom(mixins.NoChildrenMixin, mixins.ImportFromMixin, Statement):
    """Class representing an :class:`ast.ImportFrom` node.

    >>> node = astroid.extract_node('from my_package import my_module')
    >>> node
    <ImportFrom l.1 at 0x7f23b2e415c0>
    """

    _other_fields = ("modname", "names", "level")

    def __init__(
        self, fromname, names, level=0, lineno=None, col_offset=None, parent=None
    ):
        """
        :param fromname: The module that is being imported from.
        :type fromname: str or None

        :param names: What is being imported from the module.
        :type names: list(tuple(str, str or None))

        :param level: The level of relative import.
        :type level: int

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.modname = fromname
        """The module that is being imported from.

        This is ``None`` for relative imports.

        :type: str or None
        """

        self.names = names
        """What is being imported from the module.

        Each entry is a :class:`tuple` of the name being imported,
        and the alias that the name is assigned to (if any).

        :type: list(tuple(str, str or None))
        """

        self.level = level
        """The level of relative import.

        Essentially this is the number of dots in the import.
        This is always 0 for absolute imports.

        :type: int
        """

        super(ImportFrom, self).__init__(lineno, col_offset, parent)


class Attribute(NodeNG):
    """Class representing an :class:`ast.Attribute` node."""

    _astroid_fields = ("expr",)
    _other_fields = ("attrname",)
    expr = None
    """The name that this node represents.

    :type: Name or None
    """

    def __init__(self, attrname=None, lineno=None, col_offset=None, parent=None):
        """
        :param attrname: The name of the attribute.
        :type attrname: str or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.attrname = attrname
        """The name of the attribute.

        :type: str or None
        """

        super(Attribute, self).__init__(lineno, col_offset, parent)

    def postinit(self, expr=None):
        """Do some setup after initialisation.

        :param expr: The name that this node represents.
        :type expr: Name or None
        """
        self.expr = expr

    def get_children(self):
        yield self.expr


class Global(mixins.NoChildrenMixin, Statement):
    """Class representing an :class:`ast.Global` node.

    >>> node = astroid.extract_node('global a_global')
    >>> node
    <Global l.1 at 0x7f23b2e9de10>
    """

    _other_fields = ("names",)

    def __init__(self, names, lineno=None, col_offset=None, parent=None):
        """
        :param names: The names being declared as global.
        :type names: list(str)

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.names = names
        """The names being declared as global.

        :type: list(str)
        """

        super(Global, self).__init__(lineno, col_offset, parent)

    def _infer_name(self, frame, name):
        return name


class If(mixins.MultiLineBlockMixin, mixins.BlockRangeMixIn, Statement):
    """Class representing an :class:`ast.If` node.

    >>> node = astroid.extract_node('if condition: print(True)')
    >>> node
    <If l.1 at 0x7f23b2e9dd30>
    """

    _astroid_fields = ("test", "body", "orelse")
    _multi_line_block_fields = ("body", "orelse")
    test = None
    """The condition that the statement tests.

    :type: NodeNG or None
    """
    body = None
    """The contents of the block.

    :type: list(NodeNG) or None
    """
    orelse = None
    """The contents of the ``else`` block.

    :type: list(NodeNG) or None
    """

    def postinit(self, test=None, body=None, orelse=None):
        """Do some setup after initialisation.

        :param test: The condition that the statement tests.
        :type test: NodeNG or None

        :param body: The contents of the block.
        :type body: list(NodeNG) or None

        :param orelse: The contents of the ``else`` block.
        :type orelse: list(NodeNG) or None
        """
        self.test = test
        self.body = body
        self.orelse = orelse

    @decorators.cachedproperty
    def blockstart_tolineno(self):
        """The line on which the beginning of this block ends.

        :type: int
        """
        return self.test.tolineno

    def block_range(self, lineno):
        """Get a range from the given line number to where this node ends.

        :param lineno: The line number to start the range at.
        :type lineno: int

        :returns: The range of line numbers that this node belongs to,
            starting at the given line number.
        :rtype: tuple(int, int)
        """
        if lineno == self.body[0].fromlineno:
            return lineno, lineno
        if lineno <= self.body[-1].tolineno:
            return lineno, self.body[-1].tolineno
        return self._elsed_block_range(lineno, self.orelse, self.body[0].fromlineno - 1)

    def get_children(self):
        yield self.test

        yield from self.body
        yield from self.orelse

    def has_elif_block(self):
        return len(self.orelse) == 1 and isinstance(self.orelse[0], If)


class IfExp(NodeNG):
    """Class representing an :class:`ast.IfExp` node.

    >>> node = astroid.extract_node('value if condition else other')
    >>> node
    <IfExp l.1 at 0x7f23b2e9dbe0>
    """

    _astroid_fields = ("test", "body", "orelse")
    test = None
    """The condition that the statement tests.

    :type: NodeNG or None
    """
    body = None
    """The contents of the block.

    :type: list(NodeNG) or None
    """
    orelse = None
    """The contents of the ``else`` block.

    :type: list(NodeNG) or None
    """

    def postinit(self, test=None, body=None, orelse=None):
        """Do some setup after initialisation.

        :param test: The condition that the statement tests.
        :type test: NodeNG or None

        :param body: The contents of the block.
        :type body: list(NodeNG) or None

        :param orelse: The contents of the ``else`` block.
        :type orelse: list(NodeNG) or None
        """
        self.test = test
        self.body = body
        self.orelse = orelse

    def get_children(self):
        yield self.test
        yield self.body
        yield self.orelse

    def op_left_associative(self):
        # `1 if True else 2 if False else 3` is parsed as
        # `1 if True else (2 if False else 3)`
        return False


class Import(mixins.NoChildrenMixin, mixins.ImportFromMixin, Statement):
    """Class representing an :class:`ast.Import` node.

    >>> node = astroid.extract_node('import astroid')
    >>> node
    <Import l.1 at 0x7f23b2e4e5c0>
    """

    _other_fields = ("names",)

    def __init__(self, names=None, lineno=None, col_offset=None, parent=None):
        """
        :param names: The names being imported.
        :type names: list(tuple(str, str or None)) or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.names = names
        """The names being imported.

        Each entry is a :class:`tuple` of the name being imported,
        and the alias that the name is assigned to (if any).

        :type: list(tuple(str, str or None)) or None
        """

        super(Import, self).__init__(lineno, col_offset, parent)


class Index(NodeNG):
    """Class representing an :class:`ast.Index` node.

    An :class:`Index` is a simple subscript.

    >>> node = astroid.extract_node('things[1]')
    >>> node
    <Subscript l.1 at 0x7f23b2e9e2b0>
    >>> node.slice
    <Index l.1 at 0x7f23b2e9e6a0>
    """

    _astroid_fields = ("value",)
    value = None
    """The value to subscript with.

    :type: NodeNG or None
    """

    def postinit(self, value=None):
        """Do some setup after initialisation.

        :param value: The value to subscript with.
        :type value: NodeNG or None
        """
        self.value = value

    def get_children(self):
        yield self.value


class Keyword(NodeNG):
    """Class representing an :class:`ast.keyword` node.

    >>> node = astroid.extract_node('function(a_kwarg=True)')
    >>> node
    <Call l.1 at 0x7f23b2e9e320>
    >>> node.keywords
    [<Keyword l.1 at 0x7f23b2e9e9b0>]
    """

    _astroid_fields = ("value",)
    _other_fields = ("arg",)
    value = None
    """The value being assigned to the keyword argument.

    :type: NodeNG or None
    """

    def __init__(self, arg=None, lineno=None, col_offset=None, parent=None):
        """
        :param arg: The argument being assigned to.
        :type arg: Name or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.arg = arg
        """The argument being assigned to.

        :type: Name or None
        """

        super(Keyword, self).__init__(lineno, col_offset, parent)

    def postinit(self, value=None):
        """Do some setup after initialisation.

        :param value: The value being assigned to the ketword argument.
        :type value: NodeNG or None
        """
        self.value = value

    def get_children(self):
        yield self.value


class List(_BaseContainer):
    """Class representing an :class:`ast.List` node.

    >>> node = astroid.extract_node('[1, 2, 3]')
    >>> node
    <List.list l.1 at 0x7f23b2e9e128>
    """

    _other_fields = ("ctx",)

    def __init__(self, ctx=None, lineno=None, col_offset=None, parent=None):
        """
        :param ctx: Whether the list is assigned to or loaded from.
        :type ctx: Context or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.ctx = ctx
        """Whether the list is assigned to or loaded from.

        :type: Context or None
        """

        super(List, self).__init__(lineno, col_offset, parent)

    def pytype(self):
        """Get the name of the type that this node represents.

        :returns: The name of the type.
        :rtype: str
        """
        return "%s.list" % BUILTINS

    def getitem(self, index, context=None):
        """Get an item from this node.

        :param index: The node to use as a subscript index.
        :type index: Const or Slice
        """
        return _container_getitem(self, self.elts, index, context=context)


class Nonlocal(mixins.NoChildrenMixin, Statement):
    """Class representing an :class:`ast.Nonlocal` node.

    >>> node = astroid.extract_node('''
    def function():
        nonlocal var
    ''')
    >>> node
    <FunctionDef.function l.2 at 0x7f23b2e9e208>
    >>> node.body[0]
    <Nonlocal l.3 at 0x7f23b2e9e908>
    """

    _other_fields = ("names",)

    def __init__(self, names, lineno=None, col_offset=None, parent=None):
        """
        :param names: The names being declared as not local.
        :type names: list(str)

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.names = names
        """The names being declared as not local.

        :type: list(str)
        """

        super(Nonlocal, self).__init__(lineno, col_offset, parent)

    def _infer_name(self, frame, name):
        return name


class Pass(mixins.NoChildrenMixin, Statement):
    """Class representing an :class:`ast.Pass` node.

    >>> node = astroid.extract_node('pass')
    >>> node
    <Pass l.1 at 0x7f23b2e9e748>
    """


class Print(Statement):
    """Class representing an :class:`ast.Print` node.

    >>> node = astroid.extract_node('print "A message"')
    >>> node
    <Print l.1 at 0x7f0e8101d290>
    """

    _astroid_fields = ("dest", "values")
    dest = None
    """Where to print to.

    :type: NodeNG or None
    """
    values = None
    """What to print.

    :type: list(NodeNG) or None
    """

    def __init__(self, nl=None, lineno=None, col_offset=None, parent=None):
        """
        :param nl: Whether to print a new line.
        :type nl: bool or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.nl = nl
        """Whether to print a new line.

        :type: bool or None
        """

        super(Print, self).__init__(lineno, col_offset, parent)

    def postinit(self, dest=None, values=None):
        """Do some setup after initialisation.

        :param dest: Where to print to.
        :type dest: NodeNG or None

        :param values: What to print.
        :type values: list(NodeNG) or None
        """
        self.dest = dest
        self.values = values


class Raise(Statement):
    """Class representing an :class:`ast.Raise` node.

    >>> node = astroid.extract_node('raise RuntimeError("Something bad happened!")')
    >>> node
    <Raise l.1 at 0x7f23b2e9e828>
    """

    exc = None
    """What is being raised.

    :type: NodeNG or None
    """
    _astroid_fields = ("exc", "cause")
    cause = None
    """The exception being used to raise this one.

    :type: NodeNG or None
    """

    def postinit(self, exc=None, cause=None):
        """Do some setup after initialisation.

        :param exc: What is being raised.
        :type exc: NodeNG or None

        :param cause: The exception being used to raise this one.
        :type cause: NodeNG or None
        """
        self.exc = exc
        self.cause = cause

    def raises_not_implemented(self):
        """Check if this node raises a :class:`NotImplementedError`.

        :returns: True if this node raises a :class:`NotImplementedError`,
            False otherwise.
        :rtype: bool
        """
        if not self.exc:
            return False
        for name in self.exc._get_name_nodes():
            if name.name == "NotImplementedError":
                return True
        return False

    def get_children(self):
        if self.exc is not None:
            yield self.exc

        if self.cause is not None:
            yield self.cause


class Return(Statement):
    """Class representing an :class:`ast.Return` node.

    >>> node = astroid.extract_node('return True')
    >>> node
    <Return l.1 at 0x7f23b8211908>
    """

    _astroid_fields = ("value",)
    value = None
    """The value being returned.

    :type: NodeNG or None
    """

    def postinit(self, value=None):
        """Do some setup after initialisation.

        :param value: The value being returned.
        :type value: NodeNG or None
        """
        self.value = value

    def get_children(self):
        if self.value is not None:
            yield self.value

    def is_tuple_return(self):
        return isinstance(self.value, Tuple)

    def _get_return_nodes_skip_functions(self):
        yield self


class Set(_BaseContainer):
    """Class representing an :class:`ast.Set` node.

    >>> node = astroid.extract_node('{1, 2, 3}')
    >>> node
    <Set.set l.1 at 0x7f23b2e71d68>
    """

    def pytype(self):
        """Get the name of the type that this node represents.

        :returns: The name of the type.
        :rtype: str
        """
        return "%s.set" % BUILTINS


class Slice(NodeNG):
    """Class representing an :class:`ast.Slice` node.

    >>> node = astroid.extract_node('things[1:3]')
    >>> node
    <Subscript l.1 at 0x7f23b2e71f60>
    >>> node.slice
    <Slice l.1 at 0x7f23b2e71e80>
    """

    _astroid_fields = ("lower", "upper", "step")
    lower = None
    """The lower index in the slice.

    :type: NodeNG or None
    """
    upper = None
    """The upper index in the slice.

    :type: NodeNG or None
    """
    step = None
    """The step to take between indexes.

    :type: NodeNG or None
    """

    def postinit(self, lower=None, upper=None, step=None):
        """Do some setup after initialisation.

        :param lower: The lower index in the slice.
        :value lower: NodeNG or None

        :param upper: The upper index in the slice.
        :value upper: NodeNG or None

        :param step: The step to take between index.
        :param step: NodeNG or None
        """
        self.lower = lower
        self.upper = upper
        self.step = step

    def _wrap_attribute(self, attr):
        """Wrap the empty attributes of the Slice in a Const node."""
        if not attr:
            const = const_factory(attr)
            const.parent = self
            return const
        return attr

    @decorators.cachedproperty
    def _proxied(self):
        builtins = MANAGER.builtins_module
        return builtins.getattr("slice")[0]

    def pytype(self):
        """Get the name of the type that this node represents.

        :returns: The name of the type.
        :rtype: str
        """
        return "%s.slice" % BUILTINS

    def igetattr(self, attrname, context=None):
        """Infer the possible values of the given attribute on the slice.

        :param attrname: The name of the attribute to infer.
        :type attrname: str

        :returns: The inferred possible values.
        :rtype: iterable(NodeNG)
        """
        if attrname == "start":
            yield self._wrap_attribute(self.lower)
        elif attrname == "stop":
            yield self._wrap_attribute(self.upper)
        elif attrname == "step":
            yield self._wrap_attribute(self.step)
        else:
            yield from self.getattr(attrname, context=context)

    def getattr(self, attrname, context=None):
        return self._proxied.getattr(attrname, context)

    def get_children(self):
        if self.lower is not None:
            yield self.lower

        if self.upper is not None:
            yield self.upper

        if self.step is not None:
            yield self.step


class Starred(mixins.ParentAssignTypeMixin, NodeNG):
    """Class representing an :class:`ast.Starred` node.

    >>> node = astroid.extract_node('*args')
    >>> node
    <Starred l.1 at 0x7f23b2e41978>
    """

    _astroid_fields = ("value",)
    _other_fields = ("ctx",)
    value = None
    """What is being unpacked.

    :type: NodeNG or None
    """

    def __init__(self, ctx=None, lineno=None, col_offset=None, parent=None):
        """
        :param ctx: Whether the list is assigned to or loaded from.
        :type ctx: Context or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.ctx = ctx
        """Whether the starred item is assigned to or loaded from.

        :type: Context or None
        """

        super(Starred, self).__init__(
            lineno=lineno, col_offset=col_offset, parent=parent
        )

    def postinit(self, value=None):
        """Do some setup after initialisation.

        :param value: What is being unpacked.
        :type value: NodeNG or None
        """
        self.value = value

    def get_children(self):
        yield self.value


class Subscript(NodeNG):
    """Class representing an :class:`ast.Subscript` node.

    >>> node = astroid.extract_node('things[1:3]')
    >>> node
    <Subscript l.1 at 0x7f23b2e71f60>
    """

    _astroid_fields = ("value", "slice")
    _other_fields = ("ctx",)
    value = None
    """What is being indexed.

    :type: NodeNG or None
    """
    slice = None
    """The slice being used to lookup.

    :type: NodeNG or None
    """

    def __init__(self, ctx=None, lineno=None, col_offset=None, parent=None):
        """
        :param ctx: Whether the subscripted item is assigned to or loaded from.
        :type ctx: Context or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.ctx = ctx
        """Whether the subscripted item is assigned to or loaded from.

        :type: Context or None
        """

        super(Subscript, self).__init__(
            lineno=lineno, col_offset=col_offset, parent=parent
        )

    # pylint: disable=redefined-builtin; had to use the same name as builtin ast module.
    def postinit(self, value=None, slice=None):
        """Do some setup after initialisation.

        :param value: What is being indexed.
        :type value: NodeNG or None

        :param slice: The slice being used to lookup.
        :type slice: NodeNG or None
        """
        self.value = value
        self.slice = slice

    def get_children(self):
        yield self.value
        yield self.slice


class TryExcept(mixins.MultiLineBlockMixin, mixins.BlockRangeMixIn, Statement):
    """Class representing an :class:`ast.TryExcept` node.

    >>> node = astroid.extract_node('''
        try:
            do_something()
        except Exception as error:
            print("Error!")
        ''')
    >>> node
    <TryExcept l.2 at 0x7f23b2e9d908>
    """

    _astroid_fields = ("body", "handlers", "orelse")
    _multi_line_block_fields = ("body", "handlers", "orelse")
    body = None
    """The contents of the block to catch exceptions from.

    :type: list(NodeNG) or None
    """
    handlers = None
    """The exception handlers.

    :type: list(ExceptHandler) or None
    """
    orelse = None
    """The contents of the ``else`` block.

    :type: list(NodeNG) or None
    """

    def postinit(self, body=None, handlers=None, orelse=None):
        """Do some setup after initialisation.

        :param body: The contents of the block to catch exceptions from.
        :type body: list(NodeNG) or None

        :param handlers: The exception handlers.
        :type handlers: list(ExceptHandler) or None

        :param orelse: The contents of the ``else`` block.
        :type orelse: list(NodeNG) or None
        """
        self.body = body
        self.handlers = handlers
        self.orelse = orelse

    def _infer_name(self, frame, name):
        return name

    def block_range(self, lineno):
        """Get a range from the given line number to where this node ends.

        :param lineno: The line number to start the range at.
        :type lineno: int

        :returns: The range of line numbers that this node belongs to,
            starting at the given line number.
        :rtype: tuple(int, int)
        """
        last = None
        for exhandler in self.handlers:
            if exhandler.type and lineno == exhandler.type.fromlineno:
                return lineno, lineno
            if exhandler.body[0].fromlineno <= lineno <= exhandler.body[-1].tolineno:
                return lineno, exhandler.body[-1].tolineno
            if last is None:
                last = exhandler.body[0].fromlineno - 1
        return self._elsed_block_range(lineno, self.orelse, last)

    def get_children(self):
        yield from self.body

        yield from self.handlers or ()
        yield from self.orelse or ()


class TryFinally(mixins.MultiLineBlockMixin, mixins.BlockRangeMixIn, Statement):
    """Class representing an :class:`ast.TryFinally` node.

    >>> node = astroid.extract_node('''
    try:
        do_something()
    except Exception as error:
        print("Error!")
    finally:
        print("Cleanup!")
    ''')
    >>> node
    <TryFinally l.2 at 0x7f23b2e41d68>
    """

    _astroid_fields = ("body", "finalbody")
    _multi_line_block_fields = ("body", "finalbody")
    body = None
    """The try-except that the finally is attached to.

    :type: list(TryExcept) or None
    """
    finalbody = None
    """The contents of the ``finally`` block.

    :type: list(NodeNG) or None
    """

    def postinit(self, body=None, finalbody=None):
        """Do some setup after initialisation.

        :param body: The try-except that the finally is attached to.
        :type body: list(TryExcept) or None

        :param finalbody: The contents of the ``finally`` block.
        :type finalbody: list(NodeNG) or None
        """
        self.body = body
        self.finalbody = finalbody

    def block_range(self, lineno):
        """Get a range from the given line number to where this node ends.

        :param lineno: The line number to start the range at.
        :type lineno: int

        :returns: The range of line numbers that this node belongs to,
            starting at the given line number.
        :rtype: tuple(int, int)
        """
        child = self.body[0]
        # py2.5 try: except: finally:
        if (
            isinstance(child, TryExcept)
            and child.fromlineno == self.fromlineno
            and child.tolineno >= lineno > self.fromlineno
        ):
            return child.block_range(lineno)
        return self._elsed_block_range(lineno, self.finalbody)

    def get_children(self):
        yield from self.body
        yield from self.finalbody


class Tuple(_BaseContainer):
    """Class representing an :class:`ast.Tuple` node.

    >>> node = astroid.extract_node('(1, 2, 3)')
    >>> node
    <Tuple.tuple l.1 at 0x7f23b2e41780>
    """

    _other_fields = ("ctx",)

    def __init__(self, ctx=None, lineno=None, col_offset=None, parent=None):
        """
        :param ctx: Whether the tuple is assigned to or loaded from.
        :type ctx: Context or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.ctx = ctx
        """Whether the tuple is assigned to or loaded from.

        :type: Context or None
        """

        super(Tuple, self).__init__(lineno, col_offset, parent)

    def pytype(self):
        """Get the name of the type that this node represents.

        :returns: The name of the type.
        :rtype: str
        """
        return "%s.tuple" % BUILTINS

    def getitem(self, index, context=None):
        """Get an item from this node.

        :param index: The node to use as a subscript index.
        :type index: Const or Slice
        """
        return _container_getitem(self, self.elts, index, context=context)


class UnaryOp(NodeNG):
    """Class representing an :class:`ast.UnaryOp` node.

    >>> node = astroid.extract_node('-5')
    >>> node
    <UnaryOp l.1 at 0x7f23b2e4e198>
    """

    _astroid_fields = ("operand",)
    _other_fields = ("op",)
    operand = None
    """What the unary operator is applied to.

    :type: NodeNG or None
    """

    def __init__(self, op=None, lineno=None, col_offset=None, parent=None):
        """
        :param op: The operator.
        :type: str or None

        :param lineno: The line that this node appears on in the source code.
        :type lineno: int or None

        :param col_offset: The column that this node appears on in the
            source code.
        :type col_offset: int or None

        :param parent: The parent node in the syntax tree.
        :type parent: NodeNG or None
        """
        self.op = op
        """The operator.

        :type: str or None
        """

        super(UnaryOp, self).__init__(lineno, col_offset, parent)

    def postinit(self, operand=None):
        """Do some setup after initialisation.

        :param operand: What the unary operator is applied to.
        :type operand: NodeNG or None
        """
        self.operand = operand

    # This is set by inference.py
    def _infer_unaryop(self, context=None):
        raise NotImplementedError

    def type_errors(self, context=None):
        """Get a list of type errors which can occur during inference.

        Each TypeError is represented by a :class:`BadBinaryOperationMessage`,
        which holds the original exception.

        :returns: The list of possible type errors.
        :rtype: list(BadBinaryOperationMessage)
        """
        try:
            results = self._infer_unaryop(context=context)
            return [
                result
                for result in results
                if isinstance(result, util.BadUnaryOperationMessage)
            ]
        except exceptions.InferenceError:
            return []

    def get_children(self):
        yield self.operand

    def op_precedence(self):
        if self.op == "not":
            return OP_PRECEDENCE[self.op]

        return super().op_precedence()


class While(mixins.MultiLineBlockMixin, mixins.BlockRangeMixIn, Statement):
    """Class representing an :class:`ast.While` node.

    >>> node = astroid.extract_node('''
    while condition():
        print("True")
    ''')
    >>> node
    <While l.2 at 0x7f23b2e4e390>
    """

    _astroid_fields = ("test", "body", "orelse")
    _multi_line_block_fields = ("body", "orelse")
    test = None
    """The condition that the loop tests.

    :type: NodeNG or None
    """
    body = None
    """The contents of the loop.

    :type: list(NodeNG) or None
    """
    orelse = None
    """The contents of the ``else`` block.

    :type: list(NodeNG) or None
    """

    def postinit(self, test=None, body=None, orelse=None):
        """Do some setup after initialisation.

        :param test: The condition that the loop tests.
        :type test: NodeNG or None

        :param body: The contents of the loop.
        :type body: list(NodeNG) or None

        :param orelse: The contents of the ``else`` block.
        :type orelse: list(NodeNG) or None
        """
        self.test = test
        self.body = body
        self.orelse = orelse

    @decorators.cachedproperty
    def blockstart_tolineno(self):
        """The line on which the beginning of this block ends.

        :type: int
        """
        return self.test.tolineno

    def block_range(self, lineno):
        """Get a range from the given line number to where this node ends.

        :param lineno: The line number to start the range at.
        :type lineno: int

        :returns: The range of line numbers that this node belongs to,
            starting at the given line number.
        :rtype: tuple(int, int)
        """
        return self._elsed_block_range(lineno, self.orelse)

    def get_children(self):
        yield self.test

        yield from self.body
        yield from self.orelse


class With(
    mixins.MultiLineBlockMixin,
    mixins.BlockRangeMixIn,
    mixins.AssignTypeMixin,
    Statement,
):
    """Class representing an :class:`ast.With` node.

    >>> node = astroid.extract_node('''
    with open(file_path) as file_:
        print(file_.read())
    ''')
    >>> node
    <With l.2 at 0x7f23b2e4e710>
    """

    _astroid_fields = ("items", "body")
    _other_other_fields = ("type_annotation",)
    _multi_line_block_fields = ("body",)
    items = None
    """The pairs of context managers and the names they are assigned to.

    :type: list(tuple(NodeNG, AssignName or None)) or None
    """
    body = None
    """The contents of the ``with`` block.

    :type: list(NodeNG) or None
    """
    type_annotation = None
    """If present, this will contain the type annotation passed by a type comment

    :type: NodeNG or None
    """

    def postinit(self, items=None, body=None, type_annotation=None):
        """Do some setup after initialisation.

        :param items: The pairs of context managers and the names
            they are assigned to.
        :type items: list(tuple(NodeNG, AssignName or None)) or None

        :param body: The contents of the ``with`` block.
        :type body: list(NodeNG) or None
        """
        self.items = items
        self.body = body
        self.type_annotation = type_annotation

    @decorators.cachedproperty
    def blockstart_tolineno(self):
        """The line on which the beginning of this block ends.

        :type: int
        """
        return self.items[-1][0].tolineno

    def get_children(self):
        """Get the child nodes below this node.

        :returns: The children.
        :rtype: iterable(NodeNG)
        """
        for expr, var in self.items:
            yield expr
            if var:
                yield var
        yield from self.body


class AsyncWith(With):
    """Asynchronous ``with`` built with the ``async`` keyword."""


class Yield(NodeNG):
    """Class representing an :class:`ast.Yield` node.

    >>> node = astroid.extract_node('yield True')
    >>> node
    <Yield l.1 at 0x7f23b2e4e5f8>
    """

    _astroid_fields = ("value",)
    value = None
    """The value to yield.

    :type: NodeNG or None
    """

    def postinit(self, value=None):
        """Do some setup after initialisation.

        :param value: The value to yield.
        :type value: NodeNG or None
        """
        self.value = value

    def get_children(self):
        if self.value is not None:
            yield self.value

    def _get_yield_nodes_skip_lambdas(self):
        yield self


class YieldFrom(Yield):
    """Class representing an :class:`ast.YieldFrom` node."""


class DictUnpack(mixins.NoChildrenMixin, NodeNG):
    """Represents the unpacking of dicts into dicts using :pep:`448`."""


class FormattedValue(NodeNG):
    """Class representing an :class:`ast.FormattedValue` node.

    Represents a :pep:`498` format string.

    >>> node = astroid.extract_node('f"Format {type_}"')
    >>> node
    <JoinedStr l.1 at 0x7f23b2e4ed30>
    >>> node.values
    [<Const.str l.1 at 0x7f23b2e4eda0>, <FormattedValue l.1 at 0x7f23b2e4edd8>]
    """

    _astroid_fields = ("value", "format_spec")
    value = None
    """The value to be formatted into the string.

    :type: NodeNG or None
    """
    conversion = None
    """The type of formatting to be applied to the value.

    .. seealso::
        :class:`ast.FormattedValue`

    :type: int or None
    """
    format_spec = None
    """The formatting to be applied to the value.

    .. seealso::
        :class:`ast.FormattedValue`

    :type: JoinedStr or None
    """

    def postinit(self, value, conversion=None, format_spec=None):
        """Do some setup after initialisation.

        :param value: The value to be formatted into the string.
        :type value: NodeNG

        :param conversion: The type of formatting to be applied to the value.
        :type conversion: int or None

        :param format_spec: The formatting to be applied to the value.
        :type format_spec: JoinedStr or None
        """
        self.value = value
        self.conversion = conversion
        self.format_spec = format_spec

    def get_children(self):
        yield self.value

        if self.format_spec is not None:
            yield self.format_spec


class JoinedStr(NodeNG):
    """Represents a list of string expressions to be joined.

    >>> node = astroid.extract_node('f"Format {type_}"')
    >>> node
    <JoinedStr l.1 at 0x7f23b2e4ed30>
    """

    _astroid_fields = ("values",)
    values = None
    """The string expressions to be joined.

    :type: list(FormattedValue or Const) or None
    """

    def postinit(self, values=None):
        """Do some setup after initialisation.

        :param value: The string expressions to be joined.

        :type: list(FormattedValue or Const) or None
        """
        self.values = values

    def get_children(self):
        yield from self.values


class NamedExpr(mixins.AssignTypeMixin, NodeNG):
    """Represents the assignment from the assignment expression

    >>> module = astroid.parse('if a := 1: pass')
    >>> module.body[0].test
    <NamedExpr l.1 at 0x7f23b2e4ed30>
    """

    _astroid_fields = ("target", "value")
    target = None
    """The assignment target

    :type: Name
    """
    value = None
    """The value that gets assigned in the expression

    :type: NodeNG
    """

    def postinit(self, target, value):
        self.target = target
        self.value = value


class Unknown(mixins.AssignTypeMixin, NodeNG):
    """This node represents a node in a constructed AST where
    introspection is not possible.  At the moment, it's only used in
    the args attribute of FunctionDef nodes where function signature
    introspection failed.
    """

    name = "Unknown"

    def qname(self):
        return "Unknown"

    def infer(self, context=None, **kwargs):
        """Inference on an Unknown node immediately terminates."""
        yield util.Uninferable


# constants ##############################################################

CONST_CLS = {
    list: List,
    tuple: Tuple,
    dict: Dict,
    set: Set,
    type(None): Const,
    type(NotImplemented): Const,
}
if PY38:
    CONST_CLS[type(...)] = Const


def _update_const_classes():
    """update constant classes, so the keys of CONST_CLS can be reused"""
    klasses = (bool, int, float, complex, str, bytes)
    for kls in klasses:
        CONST_CLS[kls] = Const


_update_const_classes()


def _two_step_initialization(cls, value):
    instance = cls()
    instance.postinit(value)
    return instance


def _dict_initialization(cls, value):
    if isinstance(value, dict):
        value = tuple(value.items())
    return _two_step_initialization(cls, value)


_CONST_CLS_CONSTRUCTORS = {
    List: _two_step_initialization,
    Tuple: _two_step_initialization,
    Dict: _dict_initialization,
    Set: _two_step_initialization,
    Const: lambda cls, value: cls(value),
}


def const_factory(value):
    """return an astroid node for a python value"""
    # XXX we should probably be stricter here and only consider stuff in
    # CONST_CLS or do better treatment: in case where value is not in CONST_CLS,
    # we should rather recall the builder on this value than returning an empty
    # node (another option being that const_factory shouldn't be called with something
    # not in CONST_CLS)
    assert not isinstance(value, NodeNG)

    # Hack for ignoring elements of a sequence
    # or a mapping, in order to avoid transforming
    # each element to an AST. This is fixed in 2.0
    # and this approach is a temporary hack.
    if isinstance(value, (list, set, tuple, dict)):
        elts = []
    else:
        elts = value

    try:
        initializer_cls = CONST_CLS[value.__class__]
        initializer = _CONST_CLS_CONSTRUCTORS[initializer_cls]
        return initializer(initializer_cls, elts)
    except (KeyError, AttributeError):
        node = EmptyNode()
        node.object = value
        return node


def is_from_decorator(node):
    """Return True if the given node is the child of a decorator"""
    parent = node.parent
    while parent is not None:
        if isinstance(parent, Decorators):
            return True
        parent = parent.parent
    return False
