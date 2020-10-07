# Copyright (c) 2010-2011, 2013-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2014-2016, 2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Google, Inc.
# Copyright (c) 2014 Eevee (Alex Munroe) <amunroe@yelp.com>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2015 Florian Bruhin <me@the-compiler.org>
# Copyright (c) 2016 Jakub Wilk <jwilk@jwilk.net>
# Copyright (c) 2018 Nick Drozd <nicholasdrozd@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

"""This module contains some mixins for the different nodes.
"""
import itertools

from astroid import decorators
from astroid import exceptions


class BlockRangeMixIn:
    """override block range """

    @decorators.cachedproperty
    def blockstart_tolineno(self):
        return self.lineno

    def _elsed_block_range(self, lineno, orelse, last=None):
        """handle block line numbers range for try/finally, for, if and while
        statements
        """
        if lineno == self.fromlineno:
            return lineno, lineno
        if orelse:
            if lineno >= orelse[0].fromlineno:
                return lineno, orelse[-1].tolineno
            return lineno, orelse[0].fromlineno - 1
        return lineno, last or self.tolineno


class FilterStmtsMixin:
    """Mixin for statement filtering and assignment type"""

    def _get_filtered_stmts(self, _, node, _stmts, mystmt):
        """method used in _filter_stmts to get statements and trigger break"""
        if self.statement() is mystmt:
            # original node's statement is the assignment, only keep
            # current node (gen exp, list comp)
            return [node], True
        return _stmts, False

    def assign_type(self):
        return self


class AssignTypeMixin:
    def assign_type(self):
        return self

    def _get_filtered_stmts(self, lookup_node, node, _stmts, mystmt):
        """method used in filter_stmts"""
        if self is mystmt:
            return _stmts, True
        if self.statement() is mystmt:
            # original node's statement is the assignment, only keep
            # current node (gen exp, list comp)
            return [node], True
        return _stmts, False


class ParentAssignTypeMixin(AssignTypeMixin):
    def assign_type(self):
        return self.parent.assign_type()


class ImportFromMixin(FilterStmtsMixin):
    """MixIn for From and Import Nodes"""

    def _infer_name(self, frame, name):
        return name

    def do_import_module(self, modname=None):
        """return the ast for a module whose name is <modname> imported by <self>
        """
        # handle special case where we are on a package node importing a module
        # using the same name as the package, which may end in an infinite loop
        # on relative imports
        # XXX: no more needed ?
        mymodule = self.root()
        level = getattr(self, "level", None)  # Import as no level
        if modname is None:
            modname = self.modname
        # XXX we should investigate deeper if we really want to check
        # importing itself: modname and mymodule.name be relative or absolute
        if mymodule.relative_to_absolute_name(modname, level) == mymodule.name:
            # FIXME: we used to raise InferenceError here, but why ?
            return mymodule

        return mymodule.import_module(
            modname, level=level, relative_only=level and level >= 1
        )

    def real_name(self, asname):
        """get name from 'as' name"""
        for name, _asname in self.names:
            if name == "*":
                return asname
            if not _asname:
                name = name.split(".", 1)[0]
                _asname = name
            if asname == _asname:
                return name
        raise exceptions.AttributeInferenceError(
            "Could not find original name for {attribute} in {target!r}",
            target=self,
            attribute=asname,
        )


class MultiLineBlockMixin:
    """Mixin for nodes with multi-line blocks, e.g. For and FunctionDef.
    Note that this does not apply to every node with a `body` field.
    For instance, an If node has a multi-line body, but the body of an
    IfExpr is not multi-line, and hence cannot contain Return nodes,
    Assign nodes, etc.
    """

    @decorators.cachedproperty
    def _multi_line_blocks(self):
        return tuple(getattr(self, field) for field in self._multi_line_block_fields)

    def _get_return_nodes_skip_functions(self):
        for block in self._multi_line_blocks:
            for child_node in block:
                if child_node.is_function:
                    continue
                yield from child_node._get_return_nodes_skip_functions()

    def _get_yield_nodes_skip_lambdas(self):
        for block in self._multi_line_blocks:
            for child_node in block:
                if child_node.is_lambda:
                    continue
                yield from child_node._get_yield_nodes_skip_lambdas()

    @decorators.cached
    def _get_assign_nodes(self):
        children_assign_nodes = (
            child_node._get_assign_nodes()
            for block in self._multi_line_blocks
            for child_node in block
        )
        return list(itertools.chain.from_iterable(children_assign_nodes))


class NoChildrenMixin:
    """Mixin for nodes with no children, e.g. Pass."""

    def get_children(self):
        yield from ()
