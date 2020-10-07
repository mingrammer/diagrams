# Copyright (c) 2015-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2017 Derek Gustafson <degustaf@gmail.com>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""Checker for anything related to the async protocol (PEP 492)."""

import sys

import astroid
from astroid import bases, exceptions

from pylint import checkers, interfaces, utils
from pylint.checkers import utils as checker_utils
from pylint.checkers.utils import decorated_with


class AsyncChecker(checkers.BaseChecker):
    __implements__ = interfaces.IAstroidChecker
    name = "async"
    msgs = {
        "E1700": (
            "Yield inside async function",
            "yield-inside-async-function",
            "Used when an `yield` or `yield from` statement is "
            "found inside an async function.",
            {"minversion": (3, 5)},
        ),
        "E1701": (
            "Async context manager '%s' doesn't implement __aenter__ and __aexit__.",
            "not-async-context-manager",
            "Used when an async context manager is used with an object "
            "that does not implement the async context management protocol.",
            {"minversion": (3, 5)},
        ),
    }

    def open(self):
        self._ignore_mixin_members = utils.get_global_option(
            self, "ignore-mixin-members"
        )
        self._async_generators = ["contextlib.asynccontextmanager"]

    @checker_utils.check_messages("yield-inside-async-function")
    def visit_asyncfunctiondef(self, node):
        for child in node.nodes_of_class(astroid.Yield):
            if child.scope() is node and (
                sys.version_info[:2] == (3, 5) or isinstance(child, astroid.YieldFrom)
            ):
                self.add_message("yield-inside-async-function", node=child)

    @checker_utils.check_messages("not-async-context-manager")
    def visit_asyncwith(self, node):
        for ctx_mgr, _ in node.items:
            inferred = checker_utils.safe_infer(ctx_mgr)
            if inferred is None or inferred is astroid.Uninferable:
                continue

            if isinstance(inferred, bases.AsyncGenerator):
                # Check if we are dealing with a function decorated
                # with contextlib.asynccontextmanager.
                if decorated_with(inferred.parent, self._async_generators):
                    continue
            else:
                try:
                    inferred.getattr("__aenter__")
                    inferred.getattr("__aexit__")
                except exceptions.NotFoundError:
                    if isinstance(inferred, astroid.Instance):
                        # If we do not know the bases of this class,
                        # just skip it.
                        if not checker_utils.has_known_bases(inferred):
                            continue
                        # Just ignore mixin classes.
                        if self._ignore_mixin_members:
                            if inferred.name[-5:].lower() == "mixin":
                                continue
                else:
                    continue

            self.add_message(
                "not-async-context-manager", node=node, args=(inferred.name,)
            )


def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(AsyncChecker(linter))
