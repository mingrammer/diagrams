# -*- coding: utf-8 -*-
# Copyright (c) 2009-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2013-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2013-2014 Google, Inc.
# Copyright (c) 2014 Alexander Presnyakov <flagist0@gmail.com>
# Copyright (c) 2014 Eevee (Alex Munroe) <amunroe@yelp.com>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2016-2017 Derek Gustafson <degustaf@gmail.com>
# Copyright (c) 2016 Jared Garst <jgarst@users.noreply.github.com>
# Copyright (c) 2017 Hugo <hugovk@users.noreply.github.com>
# Copyright (c) 2017 Łukasz Rogalski <rogalski.91@gmail.com>
# Copyright (c) 2017 rr- <rr-@sakuya.pl>
# Copyright (c) 2018 Nick Drozd <nicholasdrozd@gmail.com>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

"""this module contains utilities for rebuilding a _ast tree in
order to get a single Astroid representation
"""

import sys

import astroid
from astroid._ast import _parse, _get_parser_module, parse_function_type_comment
from astroid import nodes


CONST_NAME_TRANSFORMS = {"None": None, "True": True, "False": False}

REDIRECT = {
    "arguments": "Arguments",
    "comprehension": "Comprehension",
    "ListCompFor": "Comprehension",
    "GenExprFor": "Comprehension",
    "excepthandler": "ExceptHandler",
    "keyword": "Keyword",
}
PY37 = sys.version_info >= (3, 7)
PY38 = sys.version_info >= (3, 8)


def _binary_operators_from_module(module):
    binary_operators = {
        module.Add: "+",
        module.BitAnd: "&",
        module.BitOr: "|",
        module.BitXor: "^",
        module.Div: "/",
        module.FloorDiv: "//",
        module.MatMult: "@",
        module.Mod: "%",
        module.Mult: "*",
        module.Pow: "**",
        module.Sub: "-",
        module.LShift: "<<",
        module.RShift: ">>",
    }
    return binary_operators


def _bool_operators_from_module(module):
    return {module.And: "and", module.Or: "or"}


def _unary_operators_from_module(module):
    return {module.UAdd: "+", module.USub: "-", module.Not: "not", module.Invert: "~"}


def _compare_operators_from_module(module):
    return {
        module.Eq: "==",
        module.Gt: ">",
        module.GtE: ">=",
        module.In: "in",
        module.Is: "is",
        module.IsNot: "is not",
        module.Lt: "<",
        module.LtE: "<=",
        module.NotEq: "!=",
        module.NotIn: "not in",
    }


def _contexts_from_module(module):
    return {
        module.Load: astroid.Load,
        module.Store: astroid.Store,
        module.Del: astroid.Del,
        module.Param: astroid.Store,
    }


def _visit_or_none(node, attr, visitor, parent, visit="visit", **kws):
    """If the given node has an attribute, visits the attribute, and
    otherwise returns None.

    """
    value = getattr(node, attr, None)
    if value:
        return getattr(visitor, visit)(value, parent, **kws)

    return None


class TreeRebuilder:
    """Rebuilds the _ast tree to become an Astroid tree"""

    def __init__(self, manager, parse_python_two: bool = False):
        self._manager = manager
        self._global_names = []
        self._import_from_nodes = []
        self._delayed_assattr = []
        self._visit_meths = {}

        # Configure the right classes for the right module
        self._parser_module = _get_parser_module(parse_python_two=parse_python_two)
        self._unary_op_classes = _unary_operators_from_module(self._parser_module)
        self._cmp_op_classes = _compare_operators_from_module(self._parser_module)
        self._bool_op_classes = _bool_operators_from_module(self._parser_module)
        self._bin_op_classes = _binary_operators_from_module(self._parser_module)
        self._context_classes = _contexts_from_module(self._parser_module)

    def _get_doc(self, node):
        try:
            if PY37 and hasattr(node, "docstring"):
                doc = node.docstring
                return node, doc
            if node.body and isinstance(node.body[0], self._parser_module.Expr):

                first_value = node.body[0].value
                if isinstance(first_value, self._parser_module.Str) or (
                    PY38
                    and isinstance(first_value, self._parser_module.Constant)
                    and isinstance(first_value.value, str)
                ):
                    doc = first_value.value if PY38 else first_value.s
                    node.body = node.body[1:]
                    return node, doc
        except IndexError:
            pass  # ast built from scratch
        return node, None

    def _get_context(self, node):
        return self._context_classes.get(type(node.ctx), astroid.Load)

    def visit_module(self, node, modname, modpath, package):
        """visit a Module node by returning a fresh instance of it"""
        node, doc = self._get_doc(node)
        newnode = nodes.Module(
            name=modname,
            doc=doc,
            file=modpath,
            path=[modpath],
            package=package,
            parent=None,
        )
        newnode.postinit([self.visit(child, newnode) for child in node.body])
        return newnode

    def visit(self, node, parent):
        cls = node.__class__
        if cls in self._visit_meths:
            visit_method = self._visit_meths[cls]
        else:
            cls_name = cls.__name__
            visit_name = "visit_" + REDIRECT.get(cls_name, cls_name).lower()
            visit_method = getattr(self, visit_name)
            self._visit_meths[cls] = visit_method
        return visit_method(node, parent)

    def _save_assignment(self, node, name=None):
        """save assignement situation since node.parent is not available yet"""
        if self._global_names and node.name in self._global_names[-1]:
            node.root().set_local(node.name, node)
        else:
            node.parent.set_local(node.name, node)

    def visit_arguments(self, node, parent):
        """visit an Arguments node by returning a fresh instance of it"""
        vararg, kwarg = node.vararg, node.kwarg
        newnode = nodes.Arguments(
            vararg.arg if vararg else None, kwarg.arg if kwarg else None, parent
        )
        args = [self.visit(child, newnode) for child in node.args]
        defaults = [self.visit(child, newnode) for child in node.defaults]
        varargannotation = None
        kwargannotation = None
        posonlyargs = []
        # change added in 82732 (7c5c678e4164), vararg and kwarg
        # are instances of `_ast.arg`, not strings
        if vararg:
            if node.vararg.annotation:
                varargannotation = self.visit(node.vararg.annotation, newnode)
            vararg = vararg.arg
        if kwarg:
            if node.kwarg.annotation:
                kwargannotation = self.visit(node.kwarg.annotation, newnode)
            kwarg = kwarg.arg
        kwonlyargs = [self.visit(child, newnode) for child in node.kwonlyargs]
        kw_defaults = [
            self.visit(child, newnode) if child else None for child in node.kw_defaults
        ]
        annotations = [
            self.visit(arg.annotation, newnode) if arg.annotation else None
            for arg in node.args
        ]
        kwonlyargs_annotations = [
            self.visit(arg.annotation, newnode) if arg.annotation else None
            for arg in node.kwonlyargs
        ]

        posonlyargs_annotations = []
        if PY38:
            posonlyargs = [self.visit(child, newnode) for child in node.posonlyargs]
            posonlyargs_annotations = [
                self.visit(arg.annotation, newnode) if arg.annotation else None
                for arg in node.posonlyargs
            ]
        type_comment_args = [
            self.check_type_comment(child, parent=newnode) for child in node.args
        ]

        newnode.postinit(
            args=args,
            defaults=defaults,
            kwonlyargs=kwonlyargs,
            posonlyargs=posonlyargs,
            kw_defaults=kw_defaults,
            annotations=annotations,
            kwonlyargs_annotations=kwonlyargs_annotations,
            posonlyargs_annotations=posonlyargs_annotations,
            varargannotation=varargannotation,
            kwargannotation=kwargannotation,
            type_comment_args=type_comment_args,
        )
        # save argument names in locals:
        if vararg:
            newnode.parent.set_local(vararg, newnode)
        if kwarg:
            newnode.parent.set_local(kwarg, newnode)
        return newnode

    def visit_assert(self, node, parent):
        """visit a Assert node by returning a fresh instance of it"""
        newnode = nodes.Assert(node.lineno, node.col_offset, parent)
        if node.msg:
            msg = self.visit(node.msg, newnode)
        else:
            msg = None
        newnode.postinit(self.visit(node.test, newnode), msg)
        return newnode

    def check_type_comment(self, node, parent):
        type_comment = getattr(node, "type_comment", None)
        if not type_comment:
            return None

        try:
            type_comment_ast = _parse(type_comment)
        except SyntaxError:
            # Invalid type comment, just skip it.
            return None

        type_object = self.visit(type_comment_ast.body[0], parent=parent)
        if not isinstance(type_object, nodes.Expr):
            return None

        return type_object.value

    def check_function_type_comment(self, node):
        type_comment = getattr(node, "type_comment", None)
        if not type_comment:
            return None

        try:
            type_comment_ast = parse_function_type_comment(type_comment)
        except SyntaxError:
            # Invalid type comment, just skip it.
            return None

        returns = None
        argtypes = [
            self.visit(elem, node) for elem in (type_comment_ast.argtypes or [])
        ]
        if type_comment_ast.returns:
            returns = self.visit(type_comment_ast.returns, node)

        return returns, argtypes

    def visit_assign(self, node, parent):
        """visit a Assign node by returning a fresh instance of it"""
        newnode = nodes.Assign(node.lineno, node.col_offset, parent)
        type_annotation = self.check_type_comment(node, parent=newnode)
        newnode.postinit(
            targets=[self.visit(child, newnode) for child in node.targets],
            value=self.visit(node.value, newnode),
            type_annotation=type_annotation,
        )
        return newnode

    def visit_assignname(self, node, parent, node_name=None):
        """visit a node and return a AssignName node"""
        newnode = nodes.AssignName(
            node_name,
            getattr(node, "lineno", None),
            getattr(node, "col_offset", None),
            parent,
        )
        self._save_assignment(newnode)
        return newnode

    def visit_augassign(self, node, parent):
        """visit a AugAssign node by returning a fresh instance of it"""
        newnode = nodes.AugAssign(
            self._bin_op_classes[type(node.op)] + "=",
            node.lineno,
            node.col_offset,
            parent,
        )
        newnode.postinit(
            self.visit(node.target, newnode), self.visit(node.value, newnode)
        )
        return newnode

    def visit_repr(self, node, parent):
        """visit a Backquote node by returning a fresh instance of it"""
        newnode = nodes.Repr(node.lineno, node.col_offset, parent)
        newnode.postinit(self.visit(node.value, newnode))
        return newnode

    def visit_binop(self, node, parent):
        """visit a BinOp node by returning a fresh instance of it"""
        newnode = nodes.BinOp(
            self._bin_op_classes[type(node.op)], node.lineno, node.col_offset, parent
        )
        newnode.postinit(
            self.visit(node.left, newnode), self.visit(node.right, newnode)
        )
        return newnode

    def visit_boolop(self, node, parent):
        """visit a BoolOp node by returning a fresh instance of it"""
        newnode = nodes.BoolOp(
            self._bool_op_classes[type(node.op)], node.lineno, node.col_offset, parent
        )
        newnode.postinit([self.visit(child, newnode) for child in node.values])
        return newnode

    def visit_break(self, node, parent):
        """visit a Break node by returning a fresh instance of it"""
        return nodes.Break(
            getattr(node, "lineno", None), getattr(node, "col_offset", None), parent
        )

    def visit_call(self, node, parent):
        """visit a CallFunc node by returning a fresh instance of it"""
        newnode = nodes.Call(node.lineno, node.col_offset, parent)
        starargs = _visit_or_none(node, "starargs", self, newnode)
        kwargs = _visit_or_none(node, "kwargs", self, newnode)
        args = [self.visit(child, newnode) for child in node.args]

        if node.keywords:
            keywords = [self.visit(child, newnode) for child in node.keywords]
        else:
            keywords = None
        if starargs:
            new_starargs = nodes.Starred(
                col_offset=starargs.col_offset,
                lineno=starargs.lineno,
                parent=starargs.parent,
            )
            new_starargs.postinit(value=starargs)
            args.append(new_starargs)
        if kwargs:
            new_kwargs = nodes.Keyword(
                arg=None,
                col_offset=kwargs.col_offset,
                lineno=kwargs.lineno,
                parent=kwargs.parent,
            )
            new_kwargs.postinit(value=kwargs)
            if keywords:
                keywords.append(new_kwargs)
            else:
                keywords = [new_kwargs]

        newnode.postinit(self.visit(node.func, newnode), args, keywords)
        return newnode

    def visit_classdef(self, node, parent, newstyle=None):
        """visit a ClassDef node to become astroid"""
        node, doc = self._get_doc(node)
        newnode = nodes.ClassDef(node.name, doc, node.lineno, node.col_offset, parent)
        metaclass = None
        for keyword in node.keywords:
            if keyword.arg == "metaclass":
                metaclass = self.visit(keyword, newnode).value
                break
        if node.decorator_list:
            decorators = self.visit_decorators(node, newnode)
        else:
            decorators = None
        newnode.postinit(
            [self.visit(child, newnode) for child in node.bases],
            [self.visit(child, newnode) for child in node.body],
            decorators,
            newstyle,
            metaclass,
            [
                self.visit(kwd, newnode)
                for kwd in node.keywords
                if kwd.arg != "metaclass"
            ],
        )
        return newnode

    def visit_const(self, node, parent):
        """visit a Const node by returning a fresh instance of it"""
        return nodes.Const(
            node.value,
            getattr(node, "lineno", None),
            getattr(node, "col_offset", None),
            parent,
        )

    def visit_continue(self, node, parent):
        """visit a Continue node by returning a fresh instance of it"""
        return nodes.Continue(
            getattr(node, "lineno", None), getattr(node, "col_offset", None), parent
        )

    def visit_compare(self, node, parent):
        """visit a Compare node by returning a fresh instance of it"""
        newnode = nodes.Compare(node.lineno, node.col_offset, parent)
        newnode.postinit(
            self.visit(node.left, newnode),
            [
                (self._cmp_op_classes[op.__class__], self.visit(expr, newnode))
                for (op, expr) in zip(node.ops, node.comparators)
            ],
        )
        return newnode

    def visit_comprehension(self, node, parent):
        """visit a Comprehension node by returning a fresh instance of it"""
        newnode = nodes.Comprehension(parent)
        newnode.postinit(
            self.visit(node.target, newnode),
            self.visit(node.iter, newnode),
            [self.visit(child, newnode) for child in node.ifs],
            getattr(node, "is_async", None),
        )
        return newnode

    def visit_decorators(self, node, parent):
        """visit a Decorators node by returning a fresh instance of it"""
        # /!\ node is actually a _ast.FunctionDef node while
        # parent is an astroid.nodes.FunctionDef node
        if PY38:
            # Set the line number of the first decorator for Python 3.8+.
            lineno = node.decorator_list[0].lineno
        else:
            lineno = node.lineno
        newnode = nodes.Decorators(lineno, node.col_offset, parent)
        newnode.postinit([self.visit(child, newnode) for child in node.decorator_list])
        return newnode

    def visit_delete(self, node, parent):
        """visit a Delete node by returning a fresh instance of it"""
        newnode = nodes.Delete(node.lineno, node.col_offset, parent)
        newnode.postinit([self.visit(child, newnode) for child in node.targets])
        return newnode

    def _visit_dict_items(self, node, parent, newnode):
        for key, value in zip(node.keys, node.values):
            rebuilt_value = self.visit(value, newnode)
            if not key:
                # Python 3.5 and extended unpacking
                rebuilt_key = nodes.DictUnpack(
                    rebuilt_value.lineno, rebuilt_value.col_offset, parent
                )
            else:
                rebuilt_key = self.visit(key, newnode)
            yield rebuilt_key, rebuilt_value

    def visit_dict(self, node, parent):
        """visit a Dict node by returning a fresh instance of it"""
        newnode = nodes.Dict(node.lineno, node.col_offset, parent)
        items = list(self._visit_dict_items(node, parent, newnode))
        newnode.postinit(items)
        return newnode

    def visit_dictcomp(self, node, parent):
        """visit a DictComp node by returning a fresh instance of it"""
        newnode = nodes.DictComp(node.lineno, node.col_offset, parent)
        newnode.postinit(
            self.visit(node.key, newnode),
            self.visit(node.value, newnode),
            [self.visit(child, newnode) for child in node.generators],
        )
        return newnode

    def visit_expr(self, node, parent):
        """visit a Expr node by returning a fresh instance of it"""
        newnode = nodes.Expr(node.lineno, node.col_offset, parent)
        newnode.postinit(self.visit(node.value, newnode))
        return newnode

    # Not used in Python 3.8+.
    def visit_ellipsis(self, node, parent):
        """visit an Ellipsis node by returning a fresh instance of it"""
        return nodes.Ellipsis(
            getattr(node, "lineno", None), getattr(node, "col_offset", None), parent
        )

    def visit_emptynode(self, node, parent):
        """visit an EmptyNode node by returning a fresh instance of it"""
        return nodes.EmptyNode(
            getattr(node, "lineno", None), getattr(node, "col_offset", None), parent
        )

    def visit_excepthandler(self, node, parent):
        """visit an ExceptHandler node by returning a fresh instance of it"""
        newnode = nodes.ExceptHandler(node.lineno, node.col_offset, parent)
        # /!\ node.name can be a tuple
        newnode.postinit(
            _visit_or_none(node, "type", self, newnode),
            _visit_or_none(node, "name", self, newnode),
            [self.visit(child, newnode) for child in node.body],
        )
        return newnode

    def visit_exec(self, node, parent):
        """visit an Exec node by returning a fresh instance of it"""
        newnode = nodes.Exec(node.lineno, node.col_offset, parent)
        newnode.postinit(
            self.visit(node.body, newnode),
            _visit_or_none(node, "globals", self, newnode),
            _visit_or_none(node, "locals", self, newnode),
        )
        return newnode

    # Not used in Python 3.8+.
    def visit_extslice(self, node, parent):
        """visit an ExtSlice node by returning a fresh instance of it"""
        newnode = nodes.ExtSlice(parent=parent)
        newnode.postinit([self.visit(dim, newnode) for dim in node.dims])
        return newnode

    def _visit_for(self, cls, node, parent):
        """visit a For node by returning a fresh instance of it"""
        newnode = cls(node.lineno, node.col_offset, parent)
        type_annotation = self.check_type_comment(node, parent=newnode)
        newnode.postinit(
            target=self.visit(node.target, newnode),
            iter=self.visit(node.iter, newnode),
            body=[self.visit(child, newnode) for child in node.body],
            orelse=[self.visit(child, newnode) for child in node.orelse],
            type_annotation=type_annotation,
        )
        return newnode

    def visit_for(self, node, parent):
        return self._visit_for(nodes.For, node, parent)

    def visit_importfrom(self, node, parent):
        """visit an ImportFrom node by returning a fresh instance of it"""
        names = [(alias.name, alias.asname) for alias in node.names]
        newnode = nodes.ImportFrom(
            node.module or "",
            names,
            node.level or None,
            getattr(node, "lineno", None),
            getattr(node, "col_offset", None),
            parent,
        )
        # store From names to add them to locals after building
        self._import_from_nodes.append(newnode)
        return newnode

    def _visit_functiondef(self, cls, node, parent):
        """visit an FunctionDef node to become astroid"""
        self._global_names.append({})
        node, doc = self._get_doc(node)

        lineno = node.lineno
        if PY38 and node.decorator_list:
            # Python 3.8 sets the line number of a decorated function
            # to be the actual line number of the function, but the
            # previous versions expected the decorator's line number instead.
            # We reset the function's line number to that of the
            # first decorator to maintain backward compatibility.
            # It's not ideal but this discrepancy was baked into
            # the framework for *years*.
            lineno = node.decorator_list[0].lineno

        newnode = cls(node.name, doc, lineno, node.col_offset, parent)
        if node.decorator_list:
            decorators = self.visit_decorators(node, newnode)
        else:
            decorators = None
        if node.returns:
            returns = self.visit(node.returns, newnode)
        else:
            returns = None

        type_comment_args = type_comment_returns = None
        type_comment_annotation = self.check_function_type_comment(node)
        if type_comment_annotation:
            type_comment_returns, type_comment_args = type_comment_annotation
        newnode.postinit(
            args=self.visit(node.args, newnode),
            body=[self.visit(child, newnode) for child in node.body],
            decorators=decorators,
            returns=returns,
            type_comment_returns=type_comment_returns,
            type_comment_args=type_comment_args,
        )
        self._global_names.pop()
        return newnode

    def visit_functiondef(self, node, parent):
        return self._visit_functiondef(nodes.FunctionDef, node, parent)

    def visit_generatorexp(self, node, parent):
        """visit a GeneratorExp node by returning a fresh instance of it"""
        newnode = nodes.GeneratorExp(node.lineno, node.col_offset, parent)
        newnode.postinit(
            self.visit(node.elt, newnode),
            [self.visit(child, newnode) for child in node.generators],
        )
        return newnode

    def visit_attribute(self, node, parent):
        """visit an Attribute node by returning a fresh instance of it"""
        context = self._get_context(node)
        if context == astroid.Del:
            # FIXME : maybe we should reintroduce and visit_delattr ?
            # for instance, deactivating assign_ctx
            newnode = nodes.DelAttr(node.attr, node.lineno, node.col_offset, parent)
        elif context == astroid.Store:
            newnode = nodes.AssignAttr(node.attr, node.lineno, node.col_offset, parent)
            # Prohibit a local save if we are in an ExceptHandler.
            if not isinstance(parent, astroid.ExceptHandler):
                self._delayed_assattr.append(newnode)
        else:
            newnode = nodes.Attribute(node.attr, node.lineno, node.col_offset, parent)
        newnode.postinit(self.visit(node.value, newnode))
        return newnode

    def visit_global(self, node, parent):
        """visit a Global node to become astroid"""
        newnode = nodes.Global(
            node.names,
            getattr(node, "lineno", None),
            getattr(node, "col_offset", None),
            parent,
        )
        if self._global_names:  # global at the module level, no effect
            for name in node.names:
                self._global_names[-1].setdefault(name, []).append(newnode)
        return newnode

    def visit_if(self, node, parent):
        """visit an If node by returning a fresh instance of it"""
        newnode = nodes.If(node.lineno, node.col_offset, parent)
        newnode.postinit(
            self.visit(node.test, newnode),
            [self.visit(child, newnode) for child in node.body],
            [self.visit(child, newnode) for child in node.orelse],
        )
        return newnode

    def visit_ifexp(self, node, parent):
        """visit a IfExp node by returning a fresh instance of it"""
        newnode = nodes.IfExp(node.lineno, node.col_offset, parent)
        newnode.postinit(
            self.visit(node.test, newnode),
            self.visit(node.body, newnode),
            self.visit(node.orelse, newnode),
        )
        return newnode

    def visit_import(self, node, parent):
        """visit a Import node by returning a fresh instance of it"""
        names = [(alias.name, alias.asname) for alias in node.names]
        newnode = nodes.Import(
            names,
            getattr(node, "lineno", None),
            getattr(node, "col_offset", None),
            parent,
        )
        # save import names in parent's locals:
        for (name, asname) in newnode.names:
            name = asname or name
            parent.set_local(name.split(".")[0], newnode)
        return newnode

    # Not used in Python 3.8+.
    def visit_index(self, node, parent):
        """visit a Index node by returning a fresh instance of it"""
        newnode = nodes.Index(parent=parent)
        newnode.postinit(self.visit(node.value, newnode))
        return newnode

    def visit_keyword(self, node, parent):
        """visit a Keyword node by returning a fresh instance of it"""
        newnode = nodes.Keyword(node.arg, parent=parent)
        newnode.postinit(self.visit(node.value, newnode))
        return newnode

    def visit_lambda(self, node, parent):
        """visit a Lambda node by returning a fresh instance of it"""
        newnode = nodes.Lambda(node.lineno, node.col_offset, parent)
        newnode.postinit(self.visit(node.args, newnode), self.visit(node.body, newnode))
        return newnode

    def visit_list(self, node, parent):
        """visit a List node by returning a fresh instance of it"""
        context = self._get_context(node)
        newnode = nodes.List(
            ctx=context, lineno=node.lineno, col_offset=node.col_offset, parent=parent
        )
        newnode.postinit([self.visit(child, newnode) for child in node.elts])
        return newnode

    def visit_listcomp(self, node, parent):
        """visit a ListComp node by returning a fresh instance of it"""
        newnode = nodes.ListComp(node.lineno, node.col_offset, parent)
        newnode.postinit(
            self.visit(node.elt, newnode),
            [self.visit(child, newnode) for child in node.generators],
        )
        return newnode

    def visit_name(self, node, parent):
        """visit a Name node by returning a fresh instance of it"""
        context = self._get_context(node)
        # True and False can be assigned to something in py2x, so we have to
        # check first the context.
        if context == astroid.Del:
            newnode = nodes.DelName(node.id, node.lineno, node.col_offset, parent)
        elif context == astroid.Store:
            newnode = nodes.AssignName(node.id, node.lineno, node.col_offset, parent)
        elif node.id in CONST_NAME_TRANSFORMS:
            newnode = nodes.Const(
                CONST_NAME_TRANSFORMS[node.id],
                getattr(node, "lineno", None),
                getattr(node, "col_offset", None),
                parent,
            )
            return newnode
        else:
            newnode = nodes.Name(node.id, node.lineno, node.col_offset, parent)
        # XXX REMOVE me :
        if context in (astroid.Del, astroid.Store):  # 'Aug' ??
            self._save_assignment(newnode)
        return newnode

    def visit_constant(self, node, parent):
        """visit a Constant node by returning a fresh instance of Const"""
        return nodes.Const(
            node.value,
            getattr(node, "lineno", None),
            getattr(node, "col_offset", None),
            parent,
        )

    # Not used in Python 3.8+.
    def visit_str(self, node, parent):
        """visit a String/Bytes node by returning a fresh instance of Const"""
        return nodes.Const(
            node.s,
            getattr(node, "lineno", None),
            getattr(node, "col_offset", None),
            parent,
        )

    visit_bytes = visit_str

    # Not used in Python 3.8+.
    def visit_num(self, node, parent):
        """visit a Num node by returning a fresh instance of Const"""
        return nodes.Const(
            node.n,
            getattr(node, "lineno", None),
            getattr(node, "col_offset", None),
            parent,
        )

    def visit_pass(self, node, parent):
        """visit a Pass node by returning a fresh instance of it"""
        return nodes.Pass(node.lineno, node.col_offset, parent)

    def visit_print(self, node, parent):
        """visit a Print node by returning a fresh instance of it"""
        newnode = nodes.Print(node.nl, node.lineno, node.col_offset, parent)
        newnode.postinit(
            _visit_or_none(node, "dest", self, newnode),
            [self.visit(child, newnode) for child in node.values],
        )
        return newnode

    def visit_raise(self, node, parent):
        """visit a Raise node by returning a fresh instance of it"""
        newnode = nodes.Raise(node.lineno, node.col_offset, parent)
        # pylint: disable=too-many-function-args
        newnode.postinit(
            _visit_or_none(node, "type", self, newnode),
            _visit_or_none(node, "inst", self, newnode),
            _visit_or_none(node, "tback", self, newnode),
        )
        return newnode

    def visit_return(self, node, parent):
        """visit a Return node by returning a fresh instance of it"""
        newnode = nodes.Return(node.lineno, node.col_offset, parent)
        if node.value is not None:
            newnode.postinit(self.visit(node.value, newnode))
        return newnode

    def visit_set(self, node, parent):
        """visit a Set node by returning a fresh instance of it"""
        newnode = nodes.Set(node.lineno, node.col_offset, parent)
        newnode.postinit([self.visit(child, newnode) for child in node.elts])
        return newnode

    def visit_setcomp(self, node, parent):
        """visit a SetComp node by returning a fresh instance of it"""
        newnode = nodes.SetComp(node.lineno, node.col_offset, parent)
        newnode.postinit(
            self.visit(node.elt, newnode),
            [self.visit(child, newnode) for child in node.generators],
        )
        return newnode

    def visit_slice(self, node, parent):
        """visit a Slice node by returning a fresh instance of it"""
        newnode = nodes.Slice(parent=parent)
        newnode.postinit(
            _visit_or_none(node, "lower", self, newnode),
            _visit_or_none(node, "upper", self, newnode),
            _visit_or_none(node, "step", self, newnode),
        )
        return newnode

    def visit_subscript(self, node, parent):
        """visit a Subscript node by returning a fresh instance of it"""
        context = self._get_context(node)
        newnode = nodes.Subscript(
            ctx=context, lineno=node.lineno, col_offset=node.col_offset, parent=parent
        )
        newnode.postinit(
            self.visit(node.value, newnode), self.visit(node.slice, newnode)
        )
        return newnode

    def visit_tryexcept(self, node, parent):
        """visit a TryExcept node by returning a fresh instance of it"""
        newnode = nodes.TryExcept(node.lineno, node.col_offset, parent)
        newnode.postinit(
            [self.visit(child, newnode) for child in node.body],
            [self.visit(child, newnode) for child in node.handlers],
            [self.visit(child, newnode) for child in node.orelse],
        )
        return newnode

    def visit_tryfinally(self, node, parent):
        """visit a TryFinally node by returning a fresh instance of it"""
        newnode = nodes.TryFinally(node.lineno, node.col_offset, parent)
        newnode.postinit(
            [self.visit(child, newnode) for child in node.body],
            [self.visit(n, newnode) for n in node.finalbody],
        )
        return newnode

    def visit_tuple(self, node, parent):
        """visit a Tuple node by returning a fresh instance of it"""
        context = self._get_context(node)
        newnode = nodes.Tuple(
            ctx=context, lineno=node.lineno, col_offset=node.col_offset, parent=parent
        )
        newnode.postinit([self.visit(child, newnode) for child in node.elts])
        return newnode

    def visit_unaryop(self, node, parent):
        """visit a UnaryOp node by returning a fresh instance of it"""
        newnode = nodes.UnaryOp(
            self._unary_op_classes[node.op.__class__],
            node.lineno,
            node.col_offset,
            parent,
        )
        newnode.postinit(self.visit(node.operand, newnode))
        return newnode

    def visit_while(self, node, parent):
        """visit a While node by returning a fresh instance of it"""
        newnode = nodes.While(node.lineno, node.col_offset, parent)
        newnode.postinit(
            self.visit(node.test, newnode),
            [self.visit(child, newnode) for child in node.body],
            [self.visit(child, newnode) for child in node.orelse],
        )
        return newnode

    def visit_with(self, node, parent):
        newnode = nodes.With(node.lineno, node.col_offset, parent)
        expr = self.visit(node.context_expr, newnode)
        if node.optional_vars is not None:
            optional_vars = self.visit(node.optional_vars, newnode)
        else:
            optional_vars = None

        type_annotation = self.check_type_comment(node, parent=newnode)
        newnode.postinit(
            items=[(expr, optional_vars)],
            body=[self.visit(child, newnode) for child in node.body],
            type_annotation=type_annotation,
        )
        return newnode

    def visit_yield(self, node, parent):
        """visit a Yield node by returning a fresh instance of it"""
        newnode = nodes.Yield(node.lineno, node.col_offset, parent)
        if node.value is not None:
            newnode.postinit(self.visit(node.value, newnode))
        return newnode


class TreeRebuilder3(TreeRebuilder):
    """extend and overwrite TreeRebuilder for python3k"""

    def visit_arg(self, node, parent):
        """visit an arg node by returning a fresh AssName instance"""
        return self.visit_assignname(node, parent, node.arg)

    # Not used in Python 3.8+.
    def visit_nameconstant(self, node, parent):
        # in Python 3.4 we have NameConstant for True / False / None
        return nodes.Const(
            node.value,
            getattr(node, "lineno", None),
            getattr(node, "col_offset", None),
            parent,
        )

    def visit_excepthandler(self, node, parent):
        """visit an ExceptHandler node by returning a fresh instance of it"""
        newnode = nodes.ExceptHandler(node.lineno, node.col_offset, parent)
        if node.name:
            name = self.visit_assignname(node, newnode, node.name)
        else:
            name = None
        newnode.postinit(
            _visit_or_none(node, "type", self, newnode),
            name,
            [self.visit(child, newnode) for child in node.body],
        )
        return newnode

    def visit_nonlocal(self, node, parent):
        """visit a Nonlocal node and return a new instance of it"""
        return nodes.Nonlocal(
            node.names,
            getattr(node, "lineno", None),
            getattr(node, "col_offset", None),
            parent,
        )

    def visit_raise(self, node, parent):
        """visit a Raise node by returning a fresh instance of it"""
        newnode = nodes.Raise(node.lineno, node.col_offset, parent)
        # no traceback; anyway it is not used in Pylint
        newnode.postinit(
            _visit_or_none(node, "exc", self, newnode),
            _visit_or_none(node, "cause", self, newnode),
        )
        return newnode

    def visit_starred(self, node, parent):
        """visit a Starred node and return a new instance of it"""
        context = self._get_context(node)
        newnode = nodes.Starred(
            ctx=context, lineno=node.lineno, col_offset=node.col_offset, parent=parent
        )
        newnode.postinit(self.visit(node.value, newnode))
        return newnode

    def visit_try(self, node, parent):
        # python 3.3 introduce a new Try node replacing
        # TryFinally/TryExcept nodes
        if node.finalbody:
            newnode = nodes.TryFinally(node.lineno, node.col_offset, parent)
            if node.handlers:
                body = [self.visit_tryexcept(node, newnode)]
            else:
                body = [self.visit(child, newnode) for child in node.body]
            newnode.postinit(body, [self.visit(n, newnode) for n in node.finalbody])
            return newnode
        if node.handlers:
            return self.visit_tryexcept(node, parent)
        return None

    def visit_annassign(self, node, parent):
        """visit an AnnAssign node by returning a fresh instance of it"""
        newnode = nodes.AnnAssign(node.lineno, node.col_offset, parent)
        annotation = _visit_or_none(node, "annotation", self, newnode)
        newnode.postinit(
            target=self.visit(node.target, newnode),
            annotation=annotation,
            simple=node.simple,
            value=_visit_or_none(node, "value", self, newnode),
        )
        return newnode

    def _visit_with(self, cls, node, parent):
        if "items" not in node._fields:
            # python < 3.3
            return super(TreeRebuilder3, self).visit_with(node, parent)

        newnode = cls(node.lineno, node.col_offset, parent)

        def visit_child(child):
            expr = self.visit(child.context_expr, newnode)
            var = _visit_or_none(child, "optional_vars", self, newnode)
            return expr, var

        type_annotation = self.check_type_comment(node, parent=newnode)
        newnode.postinit(
            items=[visit_child(child) for child in node.items],
            body=[self.visit(child, newnode) for child in node.body],
            type_annotation=type_annotation,
        )
        return newnode

    def visit_with(self, node, parent):
        return self._visit_with(nodes.With, node, parent)

    def visit_yieldfrom(self, node, parent):
        newnode = nodes.YieldFrom(node.lineno, node.col_offset, parent)
        if node.value is not None:
            newnode.postinit(self.visit(node.value, newnode))
        return newnode

    def visit_classdef(self, node, parent, newstyle=True):
        return super(TreeRebuilder3, self).visit_classdef(
            node, parent, newstyle=newstyle
        )

    # Async structs added in Python 3.5
    def visit_asyncfunctiondef(self, node, parent):
        return self._visit_functiondef(nodes.AsyncFunctionDef, node, parent)

    def visit_asyncfor(self, node, parent):
        return self._visit_for(nodes.AsyncFor, node, parent)

    def visit_await(self, node, parent):
        newnode = nodes.Await(node.lineno, node.col_offset, parent)
        newnode.postinit(value=self.visit(node.value, newnode))
        return newnode

    def visit_asyncwith(self, node, parent):
        return self._visit_with(nodes.AsyncWith, node, parent)

    def visit_joinedstr(self, node, parent):
        newnode = nodes.JoinedStr(node.lineno, node.col_offset, parent)
        newnode.postinit([self.visit(child, newnode) for child in node.values])
        return newnode

    def visit_formattedvalue(self, node, parent):
        newnode = nodes.FormattedValue(node.lineno, node.col_offset, parent)
        newnode.postinit(
            self.visit(node.value, newnode),
            node.conversion,
            _visit_or_none(node, "format_spec", self, newnode),
        )
        return newnode

    def visit_namedexpr(self, node, parent):
        newnode = nodes.NamedExpr(node.lineno, node.col_offset, parent)
        newnode.postinit(
            self.visit(node.target, newnode), self.visit(node.value, newnode)
        )
        return newnode


TreeRebuilder = TreeRebuilder3
