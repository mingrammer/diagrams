# -*- coding: utf-8 -*-
# Copyright (c) 2009-2011, 2013-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2014-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Google, Inc.
# Copyright (c) 2014 Eevee (Alex Munroe) <amunroe@yelp.com>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2015 Dmitry Pribysh <dmand@yandex.ru>
# Copyright (c) 2016 Derek Gustafson <degustaf@gmail.com>
# Copyright (c) 2017-2018 Ashley Whetter <ashley@awhetter.co.uk>
# Copyright (c) 2017 Łukasz Rogalski <rogalski.91@gmail.com>
# Copyright (c) 2017 rr- <rr-@sakuya.pl>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>
# Copyright (c) 2018 Nick Drozd <nicholasdrozd@gmail.com>
# Copyright (c) 2018 HoverHell <hoverhell@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

"""this module contains a set of functions to handle python protocols for nodes
where it makes sense.
"""

import collections
import operator as operator_mod

import itertools

from astroid import Store
from astroid import arguments
from astroid import bases
from astroid import context as contextmod
from astroid import exceptions
from astroid import decorators
from astroid import node_classes
from astroid import helpers
from astroid import nodes
from astroid import util

raw_building = util.lazy_import("raw_building")
objects = util.lazy_import("objects")


def _reflected_name(name):
    return "__r" + name[2:]


def _augmented_name(name):
    return "__i" + name[2:]


_CONTEXTLIB_MGR = "contextlib.contextmanager"
BIN_OP_METHOD = {
    "+": "__add__",
    "-": "__sub__",
    "/": "__truediv__",
    "//": "__floordiv__",
    "*": "__mul__",
    "**": "__pow__",
    "%": "__mod__",
    "&": "__and__",
    "|": "__or__",
    "^": "__xor__",
    "<<": "__lshift__",
    ">>": "__rshift__",
    "@": "__matmul__",
}

REFLECTED_BIN_OP_METHOD = {
    key: _reflected_name(value) for (key, value) in BIN_OP_METHOD.items()
}
AUGMENTED_OP_METHOD = {
    key + "=": _augmented_name(value) for (key, value) in BIN_OP_METHOD.items()
}

UNARY_OP_METHOD = {
    "+": "__pos__",
    "-": "__neg__",
    "~": "__invert__",
    "not": None,  # XXX not '__nonzero__'
}
_UNARY_OPERATORS = {
    "+": operator_mod.pos,
    "-": operator_mod.neg,
    "~": operator_mod.invert,
    "not": operator_mod.not_,
}


def _infer_unary_op(obj, op):
    func = _UNARY_OPERATORS[op]
    value = func(obj)
    return nodes.const_factory(value)


nodes.Tuple.infer_unary_op = lambda self, op: _infer_unary_op(tuple(self.elts), op)
nodes.List.infer_unary_op = lambda self, op: _infer_unary_op(self.elts, op)
nodes.Set.infer_unary_op = lambda self, op: _infer_unary_op(set(self.elts), op)
nodes.Const.infer_unary_op = lambda self, op: _infer_unary_op(self.value, op)
nodes.Dict.infer_unary_op = lambda self, op: _infer_unary_op(dict(self.items), op)

# Binary operations

BIN_OP_IMPL = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "/": lambda a, b: a / b,
    "//": lambda a, b: a // b,
    "*": lambda a, b: a * b,
    "**": lambda a, b: a ** b,
    "%": lambda a, b: a % b,
    "&": lambda a, b: a & b,
    "|": lambda a, b: a | b,
    "^": lambda a, b: a ^ b,
    "<<": lambda a, b: a << b,
    ">>": lambda a, b: a >> b,
    "@": operator_mod.matmul,
}
for _KEY, _IMPL in list(BIN_OP_IMPL.items()):
    BIN_OP_IMPL[_KEY + "="] = _IMPL


@decorators.yes_if_nothing_inferred
def const_infer_binary_op(self, opnode, operator, other, context, _):
    not_implemented = nodes.Const(NotImplemented)
    if isinstance(other, nodes.Const):
        try:
            impl = BIN_OP_IMPL[operator]
            try:
                yield nodes.const_factory(impl(self.value, other.value))
            except TypeError:
                # ArithmeticError is not enough: float >> float is a TypeError
                yield not_implemented
            except Exception:  # pylint: disable=broad-except
                yield util.Uninferable
        except TypeError:
            yield not_implemented
    elif isinstance(self.value, str) and operator == "%":
        # TODO(cpopa): implement string interpolation later on.
        yield util.Uninferable
    else:
        yield not_implemented


nodes.Const.infer_binary_op = const_infer_binary_op


def _multiply_seq_by_int(self, opnode, other, context):
    node = self.__class__(parent=opnode)
    filtered_elts = (
        helpers.safe_infer(elt, context) or util.Uninferable
        for elt in self.elts
        if elt is not util.Uninferable
    )
    node.elts = list(filtered_elts) * other.value
    return node


def _filter_uninferable_nodes(elts, context):
    for elt in elts:
        if elt is util.Uninferable:
            yield nodes.Unknown()
        else:
            for inferred in elt.infer(context):
                if inferred is not util.Uninferable:
                    yield inferred
                else:
                    yield nodes.Unknown()


@decorators.yes_if_nothing_inferred
def tl_infer_binary_op(self, opnode, operator, other, context, method):
    not_implemented = nodes.Const(NotImplemented)
    if isinstance(other, self.__class__) and operator == "+":
        node = self.__class__(parent=opnode)
        node.elts = list(
            itertools.chain(
                _filter_uninferable_nodes(self.elts, context),
                _filter_uninferable_nodes(other.elts, context),
            )
        )
        yield node
    elif isinstance(other, nodes.Const) and operator == "*":
        if not isinstance(other.value, int):
            yield not_implemented
            return
        yield _multiply_seq_by_int(self, opnode, other, context)
    elif isinstance(other, bases.Instance) and operator == "*":
        # Verify if the instance supports __index__.
        as_index = helpers.class_instance_as_index(other)
        if not as_index:
            yield util.Uninferable
        else:
            yield _multiply_seq_by_int(self, opnode, as_index, context)
    else:
        yield not_implemented


nodes.Tuple.infer_binary_op = tl_infer_binary_op
nodes.List.infer_binary_op = tl_infer_binary_op


@decorators.yes_if_nothing_inferred
def instance_class_infer_binary_op(self, opnode, operator, other, context, method):
    return method.infer_call_result(self, context)


bases.Instance.infer_binary_op = instance_class_infer_binary_op
nodes.ClassDef.infer_binary_op = instance_class_infer_binary_op


# assignment ##################################################################

"""the assigned_stmts method is responsible to return the assigned statement
(e.g. not inferred) according to the assignment type.

The `assign_path` argument is used to record the lhs path of the original node.
For instance if we want assigned statements for 'c' in 'a, (b,c)', assign_path
will be [1, 1] once arrived to the Assign node.

The `context` argument is the current inference context which should be given
to any intermediary inference necessary.
"""


def _resolve_looppart(parts, assign_path, context):
    """recursive function to resolve multiple assignments on loops"""
    assign_path = assign_path[:]
    index = assign_path.pop(0)
    for part in parts:
        if part is util.Uninferable:
            continue
        if not hasattr(part, "itered"):
            continue
        try:
            itered = part.itered()
        except TypeError:
            continue
        for stmt in itered:
            index_node = nodes.Const(index)
            try:
                assigned = stmt.getitem(index_node, context)
            except (
                AttributeError,
                exceptions.AstroidTypeError,
                exceptions.AstroidIndexError,
            ):
                continue
            if not assign_path:
                # we achieved to resolved the assignment path,
                # don't infer the last part
                yield assigned
            elif assigned is util.Uninferable:
                break
            else:
                # we are not yet on the last part of the path
                # search on each possibly inferred value
                try:
                    yield from _resolve_looppart(
                        assigned.infer(context), assign_path, context
                    )
                except exceptions.InferenceError:
                    break


@decorators.raise_if_nothing_inferred
def for_assigned_stmts(self, node=None, context=None, assign_path=None):
    if isinstance(self, nodes.AsyncFor) or getattr(self, "is_async", False):
        # Skip inferring of async code for now
        return dict(node=self, unknown=node, assign_path=assign_path, context=context)
    if assign_path is None:
        for lst in self.iter.infer(context):
            if isinstance(lst, (nodes.Tuple, nodes.List)):
                yield from lst.elts
    else:
        yield from _resolve_looppart(self.iter.infer(context), assign_path, context)
    return dict(node=self, unknown=node, assign_path=assign_path, context=context)


nodes.For.assigned_stmts = for_assigned_stmts
nodes.Comprehension.assigned_stmts = for_assigned_stmts


def sequence_assigned_stmts(self, node=None, context=None, assign_path=None):
    if assign_path is None:
        assign_path = []
    try:
        index = self.elts.index(node)
    except ValueError as exc:
        raise exceptions.InferenceError(
            "Tried to retrieve a node {node!r} which does not exist",
            node=self,
            assign_path=assign_path,
            context=context,
        ) from exc

    assign_path.insert(0, index)
    return self.parent.assigned_stmts(
        node=self, context=context, assign_path=assign_path
    )


nodes.Tuple.assigned_stmts = sequence_assigned_stmts
nodes.List.assigned_stmts = sequence_assigned_stmts


def assend_assigned_stmts(self, node=None, context=None, assign_path=None):
    return self.parent.assigned_stmts(node=self, context=context)


nodes.AssignName.assigned_stmts = assend_assigned_stmts
nodes.AssignAttr.assigned_stmts = assend_assigned_stmts


def _arguments_infer_argname(self, name, context):
    # arguments information may be missing, in which case we can't do anything
    # more
    if not (self.args or self.vararg or self.kwarg):
        yield util.Uninferable
        return
    # first argument of instance/class method
    if self.args and getattr(self.args[0], "name", None) == name:
        functype = self.parent.type
        cls = self.parent.parent.scope()
        is_metaclass = isinstance(cls, nodes.ClassDef) and cls.type == "metaclass"
        # If this is a metaclass, then the first argument will always
        # be the class, not an instance.
        if is_metaclass or functype == "classmethod":
            yield cls
            return
        if functype == "method":
            yield bases.Instance(cls)
            return

    if context and context.callcontext:
        call_site = arguments.CallSite(context.callcontext, context.extra_context)
        yield from call_site.infer_argument(self.parent, name, context)
        return

    if name == self.vararg:
        vararg = nodes.const_factory(())
        vararg.parent = self
        yield vararg
        return
    if name == self.kwarg:
        kwarg = nodes.const_factory({})
        kwarg.parent = self
        yield kwarg
        return
    # if there is a default value, yield it. And then yield Uninferable to reflect
    # we can't guess given argument value
    try:
        context = contextmod.copy_context(context)
        yield from self.default_value(name).infer(context)
        yield util.Uninferable
    except exceptions.NoDefault:
        yield util.Uninferable


def arguments_assigned_stmts(self, node=None, context=None, assign_path=None):
    if context.callcontext:
        # reset call context/name
        callcontext = context.callcontext
        context = contextmod.copy_context(context)
        context.callcontext = None
        args = arguments.CallSite(callcontext)
        return args.infer_argument(self.parent, node.name, context)
    return _arguments_infer_argname(self, node.name, context)


nodes.Arguments.assigned_stmts = arguments_assigned_stmts


@decorators.raise_if_nothing_inferred
def assign_assigned_stmts(self, node=None, context=None, assign_path=None):
    if not assign_path:
        yield self.value
        return None
    yield from _resolve_assignment_parts(
        self.value.infer(context), assign_path, context
    )

    return dict(node=self, unknown=node, assign_path=assign_path, context=context)


def assign_annassigned_stmts(self, node=None, context=None, assign_path=None):
    for inferred in assign_assigned_stmts(self, node, context, assign_path):
        if inferred is None:
            yield util.Uninferable
        else:
            yield inferred


nodes.Assign.assigned_stmts = assign_assigned_stmts
nodes.AnnAssign.assigned_stmts = assign_annassigned_stmts
nodes.AugAssign.assigned_stmts = assign_assigned_stmts


def _resolve_assignment_parts(parts, assign_path, context):
    """recursive function to resolve multiple assignments"""
    assign_path = assign_path[:]
    index = assign_path.pop(0)
    for part in parts:
        assigned = None
        if isinstance(part, nodes.Dict):
            # A dictionary in an iterating context
            try:
                assigned, _ = part.items[index]
            except IndexError:
                return

        elif hasattr(part, "getitem"):
            index_node = nodes.Const(index)
            try:
                assigned = part.getitem(index_node, context)
            except (exceptions.AstroidTypeError, exceptions.AstroidIndexError):
                return

        if not assigned:
            return

        if not assign_path:
            # we achieved to resolved the assignment path, don't infer the
            # last part
            yield assigned
        elif assigned is util.Uninferable:
            return
        else:
            # we are not yet on the last part of the path search on each
            # possibly inferred value
            try:
                yield from _resolve_assignment_parts(
                    assigned.infer(context), assign_path, context
                )
            except exceptions.InferenceError:
                return


@decorators.raise_if_nothing_inferred
def excepthandler_assigned_stmts(self, node=None, context=None, assign_path=None):
    for assigned in node_classes.unpack_infer(self.type):
        if isinstance(assigned, nodes.ClassDef):
            assigned = objects.ExceptionInstance(assigned)

        yield assigned
    return dict(node=self, unknown=node, assign_path=assign_path, context=context)


nodes.ExceptHandler.assigned_stmts = excepthandler_assigned_stmts


def _infer_context_manager(self, mgr, context):
    inferred = next(mgr.infer(context=context))
    if isinstance(inferred, bases.Generator):
        # Check if it is decorated with contextlib.contextmanager.
        func = inferred.parent
        if not func.decorators:
            raise exceptions.InferenceError(
                "No decorators found on inferred generator %s", node=func
            )

        for decorator_node in func.decorators.nodes:
            decorator = next(decorator_node.infer(context))
            if isinstance(decorator, nodes.FunctionDef):
                if decorator.qname() == _CONTEXTLIB_MGR:
                    break
        else:
            # It doesn't interest us.
            raise exceptions.InferenceError(node=func)

        # Get the first yield point. If it has multiple yields,
        # then a RuntimeError will be raised.

        possible_yield_points = func.nodes_of_class(nodes.Yield)
        # Ignore yields in nested functions
        yield_point = next(
            (node for node in possible_yield_points if node.scope() == func), None
        )
        if yield_point:
            if not yield_point.value:
                const = nodes.Const(None)
                const.parent = yield_point
                const.lineno = yield_point.lineno
                yield const
            else:
                yield from yield_point.value.infer(context=context)
    elif isinstance(inferred, bases.Instance):
        try:
            enter = next(inferred.igetattr("__enter__", context=context))
        except (exceptions.InferenceError, exceptions.AttributeInferenceError):
            raise exceptions.InferenceError(node=inferred)
        if not isinstance(enter, bases.BoundMethod):
            raise exceptions.InferenceError(node=enter)
        yield from enter.infer_call_result(self, context)
    else:
        raise exceptions.InferenceError(node=mgr)


@decorators.raise_if_nothing_inferred
def with_assigned_stmts(self, node=None, context=None, assign_path=None):
    """Infer names and other nodes from a *with* statement.

    This enables only inference for name binding in a *with* statement.
    For instance, in the following code, inferring `func` will return
    the `ContextManager` class, not whatever ``__enter__`` returns.
    We are doing this intentionally, because we consider that the context
    manager result is whatever __enter__ returns and what it is binded
    using the ``as`` keyword.

        class ContextManager(object):
            def __enter__(self):
                return 42
        with ContextManager() as f:
            pass

        # ContextManager().infer() will return ContextManager
        # f.infer() will return 42.

    Arguments:
        self: nodes.With
        node: The target of the assignment, `as (a, b)` in `with foo as (a, b)`.
        context: Inference context used for caching already inferred objects
        assign_path:
            A list of indices, where each index specifies what item to fetch from
            the inference results.
    """
    try:
        mgr = next(mgr for (mgr, vars) in self.items if vars == node)
    except StopIteration:
        return None
    if assign_path is None:
        yield from _infer_context_manager(self, mgr, context)
    else:
        for result in _infer_context_manager(self, mgr, context):
            # Walk the assign_path and get the item at the final index.
            obj = result
            for index in assign_path:
                if not hasattr(obj, "elts"):
                    raise exceptions.InferenceError(
                        "Wrong type ({targets!r}) for {node!r} assignment",
                        node=self,
                        targets=node,
                        assign_path=assign_path,
                        context=context,
                    )
                try:
                    obj = obj.elts[index]
                except IndexError as exc:
                    raise exceptions.InferenceError(
                        "Tried to infer a nonexistent target with index {index} "
                        "in {node!r}.",
                        node=self,
                        targets=node,
                        assign_path=assign_path,
                        context=context,
                    ) from exc
                except TypeError as exc:
                    raise exceptions.InferenceError(
                        "Tried to unpack a non-iterable value " "in {node!r}.",
                        node=self,
                        targets=node,
                        assign_path=assign_path,
                        context=context,
                    ) from exc
            yield obj
    return dict(node=self, unknown=node, assign_path=assign_path, context=context)


nodes.With.assigned_stmts = with_assigned_stmts


@decorators.raise_if_nothing_inferred
def named_expr_assigned_stmts(self, node, context=None, assign_path=None):
    """Infer names and other nodes from an assignment expression"""
    if self.target == node:
        yield from self.value.infer(context=context)
    else:
        raise exceptions.InferenceError(
            "Cannot infer NamedExpr node {node!r}",
            node=self,
            assign_path=assign_path,
            context=context,
        )


nodes.NamedExpr.assigned_stmts = named_expr_assigned_stmts


@decorators.yes_if_nothing_inferred
def starred_assigned_stmts(self, node=None, context=None, assign_path=None):
    """
    Arguments:
        self: nodes.Starred
        node: a node related to the current underlying Node.
        context: Inference context used for caching already inferred objects
        assign_path:
            A list of indices, where each index specifies what item to fetch from
            the inference results.
    """
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    def _determine_starred_iteration_lookups(starred, target, lookups):
        # Determine the lookups for the rhs of the iteration
        itered = target.itered()
        for index, element in enumerate(itered):
            if (
                isinstance(element, nodes.Starred)
                and element.value.name == starred.value.name
            ):
                lookups.append((index, len(itered)))
                break
            if isinstance(element, nodes.Tuple):
                lookups.append((index, len(element.itered())))
                _determine_starred_iteration_lookups(starred, element, lookups)

    stmt = self.statement()
    if not isinstance(stmt, (nodes.Assign, nodes.For)):
        raise exceptions.InferenceError(
            "Statement {stmt!r} enclosing {node!r} " "must be an Assign or For node.",
            node=self,
            stmt=stmt,
            unknown=node,
            context=context,
        )

    if context is None:
        context = contextmod.InferenceContext()

    if isinstance(stmt, nodes.Assign):
        value = stmt.value
        lhs = stmt.targets[0]

        if sum(1 for _ in lhs.nodes_of_class(nodes.Starred)) > 1:
            raise exceptions.InferenceError(
                "Too many starred arguments in the " " assignment targets {lhs!r}.",
                node=self,
                targets=lhs,
                unknown=node,
                context=context,
            )

        try:
            rhs = next(value.infer(context))
        except exceptions.InferenceError:
            yield util.Uninferable
            return
        if rhs is util.Uninferable or not hasattr(rhs, "itered"):
            yield util.Uninferable
            return

        try:
            elts = collections.deque(rhs.itered())
        except TypeError:
            yield util.Uninferable
            return

        # Unpack iteratively the values from the rhs of the assignment,
        # until the find the starred node. What will remain will
        # be the list of values which the Starred node will represent
        # This is done in two steps, from left to right to remove
        # anything before the starred node and from right to left
        # to remove anything after the starred node.

        for index, left_node in enumerate(lhs.elts):
            if not isinstance(left_node, nodes.Starred):
                if not elts:
                    break
                elts.popleft()
                continue
            lhs_elts = collections.deque(reversed(lhs.elts[index:]))
            for right_node in lhs_elts:
                if not isinstance(right_node, nodes.Starred):
                    if not elts:
                        break
                    elts.pop()
                    continue
                # We're done
                packed = nodes.List(
                    ctx=Store, parent=self, lineno=lhs.lineno, col_offset=lhs.col_offset
                )
                packed.postinit(elts=elts)
                yield packed
                break

    if isinstance(stmt, nodes.For):
        try:
            inferred_iterable = next(stmt.iter.infer(context=context))
        except exceptions.InferenceError:
            yield util.Uninferable
            return
        if inferred_iterable is util.Uninferable or not hasattr(
            inferred_iterable, "itered"
        ):
            yield util.Uninferable
            return
        try:
            itered = inferred_iterable.itered()
        except TypeError:
            yield util.Uninferable
            return

        target = stmt.target

        if not isinstance(target, nodes.Tuple):
            raise exceptions.InferenceError(
                "Could not make sense of this, the target must be a tuple",
                context=context,
            )

        lookups = []
        _determine_starred_iteration_lookups(self, target, lookups)
        if not lookups:
            raise exceptions.InferenceError(
                "Could not make sense of this, needs at least a lookup", context=context
            )

        # Make the last lookup a slice, since that what we want for a Starred node
        last_element_index, last_element_length = lookups[-1]
        is_starred_last = last_element_index == (last_element_length - 1)

        lookup_slice = slice(
            last_element_index,
            None if is_starred_last else (last_element_length - last_element_index),
        )
        lookups[-1] = lookup_slice

        for element in itered:

            # We probably want to infer the potential values *for each* element in an
            # iterable, but we can't infer a list of all values, when only a list of
            # step values are expected:
            #
            # for a, *b in [...]:
            #   b
            #
            # *b* should now point to just the elements at that particular iteration step,
            # which astroid can't know about.

            found_element = None
            for lookup in lookups:
                if not hasattr(element, "itered"):
                    break
                if not isinstance(lookup, slice):
                    # Grab just the index, not the whole length
                    lookup = lookup[0]
                try:
                    itered_inner_element = element.itered()
                    element = itered_inner_element[lookup]
                except IndexError:
                    break
                except TypeError:
                    # Most likely the itered() call failed, cannot make sense of this
                    yield util.Uninferable
                    return
                else:
                    found_element = element

            unpacked = nodes.List(
                ctx=Store, parent=self, lineno=self.lineno, col_offset=self.col_offset
            )
            unpacked.postinit(elts=found_element or [])
            yield unpacked
            return

        yield util.Uninferable


nodes.Starred.assigned_stmts = starred_assigned_stmts
