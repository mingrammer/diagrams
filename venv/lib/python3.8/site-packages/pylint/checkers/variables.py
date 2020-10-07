# -*- coding: utf-8 -*-
# Copyright (c) 2006-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2009 Mads Kiilerich <mads@kiilerich.com>
# Copyright (c) 2010 Daniel Harding <dharding@gmail.com>
# Copyright (c) 2011-2014, 2017 Google, Inc.
# Copyright (c) 2012 FELD Boris <lothiraldan@gmail.com>
# Copyright (c) 2013-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Michal Nowikowski <godfryd@gmail.com>
# Copyright (c) 2014 Brett Cannon <brett@python.org>
# Copyright (c) 2014 Ricardo Gemignani <ricardo.gemignani@gmail.com>
# Copyright (c) 2014 Arun Persaud <arun@nubati.net>
# Copyright (c) 2015 Dmitry Pribysh <dmand@yandex.ru>
# Copyright (c) 2015 Radu Ciorba <radu@devrandom.ro>
# Copyright (c) 2015 Simu Toni <simutoni@gmail.com>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2016, 2018 Ashley Whetter <ashley@awhetter.co.uk>
# Copyright (c) 2016, 2018 Jakub Wilk <jwilk@jwilk.net>
# Copyright (c) 2016-2017 Derek Gustafson <degustaf@gmail.com>
# Copyright (c) 2016-2017 Łukasz Rogalski <rogalski.91@gmail.com>
# Copyright (c) 2016 Grant Welch <gwelch925+github@gmail.com>
# Copyright (c) 2017 Ville Skyttä <ville.skytta@iki.fi>
# Copyright (c) 2017-2018 hippo91 <guillaume.peillex@gmail.com>
# Copyright (c) 2017 Dan Garrette <dhgarrette@gmail.com>
# Copyright (c) 2018 Bryce Guinta <bryce.guinta@protonmail.com>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>
# Copyright (c) 2018 Mike Frysinger <vapier@gmail.com>
# Copyright (c) 2018 ssolanki <sushobhitsolanki@gmail.com>
# Copyright (c) 2018 Marianna Polatoglou <mpolatoglou@bloomberg.net>
# Copyright (c) 2018 mar-chi-pan <mar.polatoglou@gmail.com>
# Copyright (c) 2018 Ville Skyttä <ville.skytta@upcloud.com>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""variables checkers for Python code
"""
import collections
import copy
import itertools
import os
import re
from functools import lru_cache

import astroid
from astroid import decorators, modutils, objects
from astroid.context import InferenceContext

from pylint.checkers import BaseChecker, utils
from pylint.checkers.utils import is_postponed_evaluation_enabled
from pylint.interfaces import HIGH, INFERENCE, INFERENCE_FAILURE, IAstroidChecker
from pylint.utils import get_global_option

SPECIAL_OBJ = re.compile("^_{2}[a-z]+_{2}$")
FUTURE = "__future__"
# regexp for ignored argument name
IGNORED_ARGUMENT_NAMES = re.compile("_.*|^ignored_|^unused_")
# In Python 3.7 abc has a Python implementation which is preferred
# by astroid. Unfortunately this also messes up our explicit checks
# for `abc`
METACLASS_NAME_TRANSFORMS = {"_py_abc": "abc"}
TYPING_TYPE_CHECKS_GUARDS = frozenset({"typing.TYPE_CHECKING", "TYPE_CHECKING"})
BUILTIN_RANGE = "builtins.range"
TYPING_MODULE = "typing"
TYPING_NAMES = frozenset(
    {
        "Any",
        "Callable",
        "ClassVar",
        "Generic",
        "Optional",
        "Tuple",
        "Type",
        "TypeVar",
        "Union",
        "AbstractSet",
        "ByteString",
        "Container",
        "ContextManager",
        "Hashable",
        "ItemsView",
        "Iterable",
        "Iterator",
        "KeysView",
        "Mapping",
        "MappingView",
        "MutableMapping",
        "MutableSequence",
        "MutableSet",
        "Sequence",
        "Sized",
        "ValuesView",
        "Awaitable",
        "AsyncIterator",
        "AsyncIterable",
        "Coroutine",
        "Collection",
        "AsyncGenerator",
        "AsyncContextManager",
        "Reversible",
        "SupportsAbs",
        "SupportsBytes",
        "SupportsComplex",
        "SupportsFloat",
        "SupportsInt",
        "SupportsRound",
        "Counter",
        "Deque",
        "Dict",
        "DefaultDict",
        "List",
        "Set",
        "FrozenSet",
        "NamedTuple",
        "Generator",
        "AnyStr",
        "Text",
        "Pattern",
    }
)


def _is_from_future_import(stmt, name):
    """Check if the name is a future import from another module."""
    try:
        module = stmt.do_import_module(stmt.modname)
    except astroid.AstroidBuildingException:
        return None

    for local_node in module.locals.get(name, []):
        if isinstance(local_node, astroid.ImportFrom) and local_node.modname == FUTURE:
            return True
    return None


def in_for_else_branch(parent, stmt):
    """Returns True if stmt in inside the else branch for a parent For stmt."""
    return isinstance(parent, astroid.For) and any(
        else_stmt.parent_of(stmt) or else_stmt == stmt for else_stmt in parent.orelse
    )


@lru_cache(maxsize=1000)
def overridden_method(klass, name):
    """get overridden method if any"""
    try:
        parent = next(klass.local_attr_ancestors(name))
    except (StopIteration, KeyError):
        return None
    try:
        meth_node = parent[name]
    except KeyError:
        # We have found an ancestor defining <name> but it's not in the local
        # dictionary. This may happen with astroid built from living objects.
        return None
    if isinstance(meth_node, astroid.FunctionDef):
        return meth_node
    return None


def _get_unpacking_extra_info(node, inferred):
    """return extra information to add to the message for unpacking-non-sequence
    and unbalanced-tuple-unpacking errors
    """
    more = ""
    inferred_module = inferred.root().name
    if node.root().name == inferred_module:
        if node.lineno == inferred.lineno:
            more = " %s" % inferred.as_string()
        elif inferred.lineno:
            more = " defined at line %s" % inferred.lineno
    elif inferred.lineno:
        more = " defined at line %s of %s" % (inferred.lineno, inferred_module)
    return more


def _detect_global_scope(node, frame, defframe):
    """ Detect that the given frames shares a global
    scope.

    Two frames shares a global scope when neither
    of them are hidden under a function scope, as well
    as any of parent scope of them, until the root scope.
    In this case, depending from something defined later on
    will not work, because it is still undefined.

    Example:
        class A:
            # B has the same global scope as `C`, leading to a NameError.
            class B(C): ...
        class C: ...

    """
    def_scope = scope = None
    if frame and frame.parent:
        scope = frame.parent.scope()
    if defframe and defframe.parent:
        def_scope = defframe.parent.scope()
    if isinstance(frame, astroid.FunctionDef):
        # If the parent of the current node is a
        # function, then it can be under its scope
        # (defined in, which doesn't concern us) or
        # the `->` part of annotations. The same goes
        # for annotations of function arguments, they'll have
        # their parent the Arguments node.
        if not isinstance(node.parent, (astroid.FunctionDef, astroid.Arguments)):
            return False
    elif any(
        not isinstance(f, (astroid.ClassDef, astroid.Module)) for f in (frame, defframe)
    ):
        # Not interested in other frames, since they are already
        # not in a global scope.
        return False

    break_scopes = []
    for current_scope in (scope, def_scope):
        # Look for parent scopes. If there is anything different
        # than a module or a class scope, then they frames don't
        # share a global scope.
        parent_scope = current_scope
        while parent_scope:
            if not isinstance(parent_scope, (astroid.ClassDef, astroid.Module)):
                break_scopes.append(parent_scope)
                break
            if parent_scope.parent:
                parent_scope = parent_scope.parent.scope()
            else:
                break
    if break_scopes and len(set(break_scopes)) != 1:
        # Store different scopes than expected.
        # If the stored scopes are, in fact, the very same, then it means
        # that the two frames (frame and defframe) shares the same scope,
        # and we could apply our lineno analysis over them.
        # For instance, this works when they are inside a function, the node
        # that uses a definition and the definition itself.
        return False
    # At this point, we are certain that frame and defframe shares a scope
    # and the definition of the first depends on the second.
    return frame.lineno < defframe.lineno


def _infer_name_module(node, name):
    context = InferenceContext()
    context.lookupname = name
    return node.infer(context, asname=False)


def _fix_dot_imports(not_consumed):
    """ Try to fix imports with multiple dots, by returning a dictionary
    with the import names expanded. The function unflattens root imports,
    like 'xml' (when we have both 'xml.etree' and 'xml.sax'), to 'xml.etree'
    and 'xml.sax' respectively.
    """
    names = {}
    for name, stmts in not_consumed.items():
        if any(
            isinstance(stmt, astroid.AssignName)
            and isinstance(stmt.assign_type(), astroid.AugAssign)
            for stmt in stmts
        ):
            continue
        for stmt in stmts:
            if not isinstance(stmt, (astroid.ImportFrom, astroid.Import)):
                continue
            for imports in stmt.names:
                second_name = None
                import_module_name = imports[0]
                if import_module_name == "*":
                    # In case of wildcard imports,
                    # pick the name from inside the imported module.
                    second_name = name
                else:
                    name_matches_dotted_import = False
                    if (
                        import_module_name.startswith(name)
                        and import_module_name.find(".") > -1
                    ):
                        name_matches_dotted_import = True

                    if name_matches_dotted_import or name in imports:
                        # Most likely something like 'xml.etree',
                        # which will appear in the .locals as 'xml'.
                        # Only pick the name if it wasn't consumed.
                        second_name = import_module_name
                if second_name and second_name not in names:
                    names[second_name] = stmt
    return sorted(names.items(), key=lambda a: a[1].fromlineno)


def _find_frame_imports(name, frame):
    """
    Detect imports in the frame, with the required
    *name*. Such imports can be considered assignments.
    Returns True if an import for the given name was found.
    """
    imports = frame.nodes_of_class((astroid.Import, astroid.ImportFrom))
    for import_node in imports:
        for import_name, import_alias in import_node.names:
            # If the import uses an alias, check only that.
            # Otherwise, check only the import name.
            if import_alias:
                if import_alias == name:
                    return True
            elif import_name and import_name == name:
                return True
    return None


def _import_name_is_global(stmt, global_names):
    for import_name, import_alias in stmt.names:
        # If the import uses an alias, check only that.
        # Otherwise, check only the import name.
        if import_alias:
            if import_alias in global_names:
                return True
        elif import_name in global_names:
            return True
    return False


def _flattened_scope_names(iterator):
    values = (set(stmt.names) for stmt in iterator)
    return set(itertools.chain.from_iterable(values))


def _assigned_locally(name_node):
    """
    Checks if name_node has corresponding assign statement in same scope
    """
    assign_stmts = name_node.scope().nodes_of_class(astroid.AssignName)
    return any(a.name == name_node.name for a in assign_stmts)


def _is_type_checking_import(node):
    parent = node.parent
    if not isinstance(parent, astroid.If):
        return False
    test = parent.test
    return test.as_string() in TYPING_TYPE_CHECKS_GUARDS


def _has_locals_call_after_node(stmt, scope):
    skip_nodes = (
        astroid.FunctionDef,
        astroid.ClassDef,
        astroid.Import,
        astroid.ImportFrom,
    )
    for call in scope.nodes_of_class(astroid.Call, skip_klass=skip_nodes):
        inferred = utils.safe_infer(call.func)
        if (
            utils.is_builtin_object(inferred)
            and getattr(inferred, "name", None) == "locals"
        ):
            if stmt.lineno < call.lineno:
                return True
    return False


MSGS = {
    "E0601": (
        "Using variable %r before assignment",
        "used-before-assignment",
        "Used when a local variable is accessed before its assignment.",
    ),
    "E0602": (
        "Undefined variable %r",
        "undefined-variable",
        "Used when an undefined variable is accessed.",
    ),
    "E0603": (
        "Undefined variable name %r in __all__",
        "undefined-all-variable",
        "Used when an undefined variable name is referenced in __all__.",
    ),
    "E0604": (
        "Invalid object %r in __all__, must contain only strings",
        "invalid-all-object",
        "Used when an invalid (non-string) object occurs in __all__.",
    ),
    "E0611": (
        "No name %r in module %r",
        "no-name-in-module",
        "Used when a name cannot be found in a module.",
    ),
    "W0601": (
        "Global variable %r undefined at the module level",
        "global-variable-undefined",
        'Used when a variable is defined through the "global" statement '
        "but the variable is not defined in the module scope.",
    ),
    "W0602": (
        "Using global for %r but no assignment is done",
        "global-variable-not-assigned",
        'Used when a variable is defined through the "global" statement '
        "but no assignment to this variable is done.",
    ),
    "W0603": (
        "Using the global statement",  # W0121
        "global-statement",
        'Used when you use the "global" statement to update a global '
        "variable. Pylint just try to discourage this "
        "usage. That doesn't mean you cannot use it !",
    ),
    "W0604": (
        "Using the global statement at the module level",  # W0103
        "global-at-module-level",
        'Used when you use the "global" statement at the module level '
        "since it has no effect",
    ),
    "W0611": (
        "Unused %s",
        "unused-import",
        "Used when an imported module or variable is not used.",
    ),
    "W0612": (
        "Unused variable %r",
        "unused-variable",
        "Used when a variable is defined but not used.",
    ),
    "W0613": (
        "Unused argument %r",
        "unused-argument",
        "Used when a function or method argument is not used.",
    ),
    "W0614": (
        "Unused import %s from wildcard import",
        "unused-wildcard-import",
        "Used when an imported module or variable is not used from a "
        "`'from X import *'` style import.",
    ),
    "W0621": (
        "Redefining name %r from outer scope (line %s)",
        "redefined-outer-name",
        "Used when a variable's name hides a name defined in the outer scope.",
    ),
    "W0622": (
        "Redefining built-in %r",
        "redefined-builtin",
        "Used when a variable or function override a built-in.",
    ),
    "W0623": (
        "Redefining name %r from %s in exception handler",
        "redefine-in-handler",
        "Used when an exception handler assigns the exception to an existing name",
    ),
    "W0631": (
        "Using possibly undefined loop variable %r",
        "undefined-loop-variable",
        "Used when a loop variable (i.e. defined by a for loop or "
        "a list comprehension or a generator expression) is used outside "
        "the loop.",
    ),
    "W0632": (
        "Possible unbalanced tuple unpacking with "
        "sequence%s: "
        "left side has %d label(s), right side has %d value(s)",
        "unbalanced-tuple-unpacking",
        "Used when there is an unbalanced tuple unpacking in assignment",
        {"old_names": [("E0632", "old-unbalanced-tuple-unpacking")]},
    ),
    "E0633": (
        "Attempting to unpack a non-sequence%s",
        "unpacking-non-sequence",
        "Used when something which is not "
        "a sequence is used in an unpack assignment",
        {"old_names": [("W0633", "old-unpacking-non-sequence")]},
    ),
    "W0640": (
        "Cell variable %s defined in loop",
        "cell-var-from-loop",
        "A variable used in a closure is defined in a loop. "
        "This will result in all closures using the same value for "
        "the closed-over variable.",
    ),
    "W0641": (
        "Possibly unused variable %r",
        "possibly-unused-variable",
        "Used when a variable is defined but might not be used. "
        "The possibility comes from the fact that locals() might be used, "
        "which could consume or not the said variable",
    ),
    "W0642": (
        "Invalid assignment to %s in method",
        "self-cls-assignment",
        "Invalid assignment to self or cls in instance or class method "
        "respectively.",
    ),
}


ScopeConsumer = collections.namedtuple(
    "ScopeConsumer", "to_consume consumed scope_type"
)


class NamesConsumer:
    """
    A simple class to handle consumed, to consume and scope type info of node locals
    """

    def __init__(self, node, scope_type):
        self._atomic = ScopeConsumer(copy.copy(node.locals), {}, scope_type)

    def __repr__(self):
        msg = "\nto_consume : {:s}\n".format(
            ", ".join(
                [
                    "{}->{}".format(key, val)
                    for key, val in self._atomic.to_consume.items()
                ]
            )
        )
        msg += "consumed : {:s}\n".format(
            ", ".join(
                [
                    "{}->{}".format(key, val)
                    for key, val in self._atomic.consumed.items()
                ]
            )
        )
        msg += "scope_type : {:s}\n".format(self._atomic.scope_type)
        return msg

    def __iter__(self):
        return iter(self._atomic)

    @property
    def to_consume(self):
        return self._atomic.to_consume

    @property
    def consumed(self):
        return self._atomic.consumed

    @property
    def scope_type(self):
        return self._atomic.scope_type

    def mark_as_consumed(self, name, new_node):
        """
        Mark the name as consumed and delete it from
        the to_consume dictionary
        """
        self.consumed[name] = new_node
        del self.to_consume[name]

    def get_next_to_consume(self, node):
        # mark the name as consumed if it's defined in this scope
        name = node.name
        parent_node = node.parent
        found_node = self.to_consume.get(name)
        if (
            found_node
            and isinstance(parent_node, astroid.Assign)
            and parent_node == found_node[0].parent
        ):
            lhs = found_node[0].parent.targets[0]
            if lhs.name == name:  # this name is defined in this very statement
                found_node = None
        return found_node


# pylint: disable=too-many-public-methods
class VariablesChecker(BaseChecker):
    """checks for
    * unused variables / imports
    * undefined variables
    * redefinition of variable from builtins or from an outer scope
    * use of variable before assignment
    * __all__ consistency
    * self/cls assignment
    """

    __implements__ = IAstroidChecker

    name = "variables"
    msgs = MSGS
    priority = -1
    options = (
        (
            "init-import",
            {
                "default": 0,
                "type": "yn",
                "metavar": "<y_or_n>",
                "help": "Tells whether we should check for unused import in "
                "__init__ files.",
            },
        ),
        (
            "dummy-variables-rgx",
            {
                "default": "_+$|(_[a-zA-Z0-9_]*[a-zA-Z0-9]+?$)|dummy|^ignored_|^unused_",
                "type": "regexp",
                "metavar": "<regexp>",
                "help": "A regular expression matching the name of dummy "
                "variables (i.e. expected to not be used).",
            },
        ),
        (
            "additional-builtins",
            {
                "default": (),
                "type": "csv",
                "metavar": "<comma separated list>",
                "help": "List of additional names supposed to be defined in "
                "builtins. Remember that you should avoid defining new builtins "
                "when possible.",
            },
        ),
        (
            "callbacks",
            {
                "default": ("cb_", "_cb"),
                "type": "csv",
                "metavar": "<callbacks>",
                "help": "List of strings which can identify a callback "
                "function by name. A callback name must start or "
                "end with one of those strings.",
            },
        ),
        (
            "redefining-builtins-modules",
            {
                "default": (
                    "six.moves",
                    "past.builtins",
                    "future.builtins",
                    "builtins",
                    "io",
                ),
                "type": "csv",
                "metavar": "<comma separated list>",
                "help": "List of qualified module names which can have objects "
                "that can redefine builtins.",
            },
        ),
        (
            "ignored-argument-names",
            {
                "default": IGNORED_ARGUMENT_NAMES,
                "type": "regexp",
                "metavar": "<regexp>",
                "help": "Argument names that match this expression will be "
                "ignored. Default to name with leading underscore.",
            },
        ),
        (
            "allow-global-unused-variables",
            {
                "default": True,
                "type": "yn",
                "metavar": "<y_or_n>",
                "help": "Tells whether unused global variables should be treated as a violation.",
            },
        ),
    )

    def __init__(self, linter=None):
        BaseChecker.__init__(self, linter)
        self._to_consume = (
            None
        )  # list of tuples: (to_consume:dict, consumed:dict, scope_type:str)
        self._checking_mod_attr = None
        self._loop_variables = []
        self._type_annotation_names = []
        self._postponed_evaluation_enabled = False

    @utils.check_messages("redefined-outer-name")
    def visit_for(self, node):
        assigned_to = [
            var.name for var in node.target.nodes_of_class(astroid.AssignName)
        ]

        # Only check variables that are used
        dummy_rgx = self.config.dummy_variables_rgx
        assigned_to = [var for var in assigned_to if not dummy_rgx.match(var)]

        for variable in assigned_to:
            for outer_for, outer_variables in self._loop_variables:
                if variable in outer_variables and not in_for_else_branch(
                    outer_for, node
                ):
                    self.add_message(
                        "redefined-outer-name",
                        args=(variable, outer_for.fromlineno),
                        node=node,
                    )
                    break

        self._loop_variables.append((node, assigned_to))

    @utils.check_messages("redefined-outer-name")
    def leave_for(self, node):
        self._loop_variables.pop()
        self._store_type_annotation_names(node)

    def visit_module(self, node):
        """visit module : update consumption analysis variable
        checks globals doesn't overrides builtins
        """
        self._to_consume = [NamesConsumer(node, "module")]
        self._postponed_evaluation_enabled = is_postponed_evaluation_enabled(node)

        for name, stmts in node.locals.items():
            if utils.is_builtin(name) and not utils.is_inside_except(stmts[0]):
                if self._should_ignore_redefined_builtin(stmts[0]) or name == "__doc__":
                    continue
                self.add_message("redefined-builtin", args=name, node=stmts[0])

    @utils.check_messages(
        "unused-import",
        "unused-wildcard-import",
        "redefined-builtin",
        "undefined-all-variable",
        "invalid-all-object",
        "unused-variable",
    )
    def leave_module(self, node):
        """leave module: check globals
        """
        assert len(self._to_consume) == 1

        self._check_metaclasses(node)
        not_consumed = self._to_consume.pop().to_consume
        # attempt to check for __all__ if defined
        if "__all__" in node.locals:
            self._check_all(node, not_consumed)

        # check for unused globals
        self._check_globals(not_consumed)

        # don't check unused imports in __init__ files
        if not self.config.init_import and node.package:
            return

        self._check_imports(not_consumed)

    def visit_classdef(self, node):
        """visit class: update consumption analysis variable
        """
        self._to_consume.append(NamesConsumer(node, "class"))

    def leave_classdef(self, _):
        """leave class: update consumption analysis variable
        """
        # do not check for not used locals here (no sense)
        self._to_consume.pop()

    def visit_lambda(self, node):
        """visit lambda: update consumption analysis variable
        """
        self._to_consume.append(NamesConsumer(node, "lambda"))

    def leave_lambda(self, _):
        """leave lambda: update consumption analysis variable
        """
        # do not check for not used locals here
        self._to_consume.pop()

    def visit_generatorexp(self, node):
        """visit genexpr: update consumption analysis variable
        """
        self._to_consume.append(NamesConsumer(node, "comprehension"))

    def leave_generatorexp(self, _):
        """leave genexpr: update consumption analysis variable
        """
        # do not check for not used locals here
        self._to_consume.pop()

    def visit_dictcomp(self, node):
        """visit dictcomp: update consumption analysis variable
        """
        self._to_consume.append(NamesConsumer(node, "comprehension"))

    def leave_dictcomp(self, _):
        """leave dictcomp: update consumption analysis variable
        """
        # do not check for not used locals here
        self._to_consume.pop()

    def visit_setcomp(self, node):
        """visit setcomp: update consumption analysis variable
        """
        self._to_consume.append(NamesConsumer(node, "comprehension"))

    def leave_setcomp(self, _):
        """leave setcomp: update consumption analysis variable
        """
        # do not check for not used locals here
        self._to_consume.pop()

    def visit_functiondef(self, node):
        """visit function: update consumption analysis variable and check locals
        """
        self._to_consume.append(NamesConsumer(node, "function"))
        if not (
            self.linter.is_message_enabled("redefined-outer-name")
            or self.linter.is_message_enabled("redefined-builtin")
        ):
            return
        globs = node.root().globals
        for name, stmt in node.items():
            if utils.is_inside_except(stmt):
                continue
            if name in globs and not isinstance(stmt, astroid.Global):
                definition = globs[name][0]
                if (
                    isinstance(definition, astroid.ImportFrom)
                    and definition.modname == FUTURE
                ):
                    # It is a __future__ directive, not a symbol.
                    continue

                # Do not take in account redefined names for the purpose
                # of type checking.:
                if any(
                    isinstance(definition.parent, astroid.If)
                    and definition.parent.test.as_string() in TYPING_TYPE_CHECKS_GUARDS
                    for definition in globs[name]
                ):
                    continue

                line = definition.fromlineno
                if not self._is_name_ignored(stmt, name):
                    self.add_message(
                        "redefined-outer-name", args=(name, line), node=stmt
                    )

            elif utils.is_builtin(name) and not self._should_ignore_redefined_builtin(
                stmt
            ):
                # do not print Redefining builtin for additional builtins
                self.add_message("redefined-builtin", args=name, node=stmt)

    def leave_functiondef(self, node):
        """leave function: check function's locals are consumed"""
        self._check_metaclasses(node)

        if node.type_comment_returns:
            self._store_type_annotation_node(node.type_comment_returns)
        if node.type_comment_args:
            for argument_annotation in node.type_comment_args:
                self._store_type_annotation_node(argument_annotation)

        not_consumed = self._to_consume.pop().to_consume
        if not (
            self.linter.is_message_enabled("unused-variable")
            or self.linter.is_message_enabled("possibly-unused-variable")
            or self.linter.is_message_enabled("unused-argument")
        ):
            return

        # Don't check arguments of function which are only raising an exception.
        if utils.is_error(node):
            return

        # Don't check arguments of abstract methods or within an interface.
        is_method = node.is_method()
        if is_method and node.is_abstract():
            return

        global_names = _flattened_scope_names(node.nodes_of_class(astroid.Global))
        nonlocal_names = _flattened_scope_names(node.nodes_of_class(astroid.Nonlocal))
        for name, stmts in not_consumed.items():
            self._check_is_unused(name, node, stmts[0], global_names, nonlocal_names)

    visit_asyncfunctiondef = visit_functiondef
    leave_asyncfunctiondef = leave_functiondef

    @utils.check_messages(
        "global-variable-undefined",
        "global-variable-not-assigned",
        "global-statement",
        "global-at-module-level",
        "redefined-builtin",
    )
    def visit_global(self, node):
        """check names imported exists in the global scope"""
        frame = node.frame()
        if isinstance(frame, astroid.Module):
            self.add_message("global-at-module-level", node=node)
            return

        module = frame.root()
        default_message = True
        locals_ = node.scope().locals
        for name in node.names:
            try:
                assign_nodes = module.getattr(name)
            except astroid.NotFoundError:
                # unassigned global, skip
                assign_nodes = []

            not_defined_locally_by_import = not any(
                isinstance(local, astroid.node_classes.Import)
                for local in locals_.get(name, ())
            )
            if not assign_nodes and not_defined_locally_by_import:
                self.add_message("global-variable-not-assigned", args=name, node=node)
                default_message = False
                continue

            for anode in assign_nodes:
                if (
                    isinstance(anode, astroid.AssignName)
                    and anode.name in module.special_attributes
                ):
                    self.add_message("redefined-builtin", args=name, node=node)
                    break
                if anode.frame() is module:
                    # module level assignment
                    break
            else:
                if not_defined_locally_by_import:
                    # global undefined at the module scope
                    self.add_message("global-variable-undefined", args=name, node=node)
                    default_message = False

        if default_message:
            self.add_message("global-statement", node=node)

    def visit_assignname(self, node):
        if isinstance(node.assign_type(), astroid.AugAssign):
            self.visit_name(node)

    def visit_delname(self, node):
        self.visit_name(node)

    @utils.check_messages(*MSGS)
    def visit_name(self, node):
        """check that a name is defined if the current scope and doesn't
        redefine a built-in
        """
        stmt = node.statement()
        if stmt.fromlineno is None:
            # name node from an astroid built from live code, skip
            assert not stmt.root().file.endswith(".py")
            return

        name = node.name
        frame = stmt.scope()
        # if the name node is used as a function default argument's value or as
        # a decorator, then start from the parent frame of the function instead
        # of the function frame - and thus open an inner class scope
        if (
            utils.is_default_argument(node)
            or utils.is_func_decorator(node)
            or utils.is_ancestor_name(frame, node)
        ):
            start_index = len(self._to_consume) - 2
        else:
            start_index = len(self._to_consume) - 1
        # iterates through parent scopes, from the inner to the outer
        base_scope_type = self._to_consume[start_index].scope_type
        # pylint: disable=too-many-nested-blocks; refactoring this block is a pain.
        for i in range(start_index, -1, -1):
            current_consumer = self._to_consume[i]
            # if the current scope is a class scope but it's not the inner
            # scope, ignore it. This prevents to access this scope instead of
            # the globals one in function members when there are some common
            # names. The only exception is when the starting scope is a
            # comprehension and its direct outer scope is a class
            if (
                current_consumer.scope_type == "class"
                and i != start_index
                and not (base_scope_type == "comprehension" and i == start_index - 1)
            ):
                if self._ignore_class_scope(node):
                    continue

            # the name has already been consumed, only check it's not a loop
            # variable used outside the loop
            # avoid the case where there are homonyms inside function scope and
            #  comprehension current scope (avoid bug #1731)
            if name in current_consumer.consumed and not (
                current_consumer.scope_type == "comprehension"
                and self._has_homonym_in_upper_function_scope(node, i)
            ):
                defnode = utils.assign_parent(current_consumer.consumed[name][0])
                self._check_late_binding_closure(node, defnode)
                self._loopvar_name(node, name)
                break

            found_node = current_consumer.get_next_to_consume(node)
            if found_node is None:
                continue

            # checks for use before assignment
            defnode = utils.assign_parent(current_consumer.to_consume[name][0])

            if defnode is not None:
                self._check_late_binding_closure(node, defnode)
                defstmt = defnode.statement()
                defframe = defstmt.frame()
                # The class reuses itself in the class scope.
                recursive_klass = (
                    frame is defframe
                    and defframe.parent_of(node)
                    and isinstance(defframe, astroid.ClassDef)
                    and node.name == defframe.name
                )

                if (
                    recursive_klass
                    and utils.is_inside_lambda(node)
                    and (
                        not utils.is_default_argument(node)
                        or node.scope().parent.scope() is not defframe
                    )
                ):
                    # Self-referential class references are fine in lambda's --
                    # As long as they are not part of the default argument directly
                    # under the scope of the parent self-referring class.
                    # Example of valid default argument:
                    # class MyName3:
                    #     myattr = 1
                    #     mylambda3 = lambda: lambda a=MyName3: a
                    # Example of invalid default argument:
                    # class MyName4:
                    #     myattr = 1
                    #     mylambda4 = lambda a=MyName4: lambda: a

                    # If the above conditional is True,
                    # there is no possibility of undefined-variable
                    # Also do not consume class name
                    # (since consuming blocks subsequent checks)
                    # -- quit
                    break

                maybee0601, annotation_return, use_outer_definition = self._is_variable_violation(
                    node,
                    name,
                    defnode,
                    stmt,
                    defstmt,
                    frame,
                    defframe,
                    base_scope_type,
                    recursive_klass,
                )

                if use_outer_definition:
                    continue

                if (
                    maybee0601
                    and not utils.is_defined_before(node)
                    and not astroid.are_exclusive(stmt, defstmt, ("NameError",))
                ):

                    # Used and defined in the same place, e.g `x += 1` and `del x`
                    defined_by_stmt = defstmt is stmt and isinstance(
                        node, (astroid.DelName, astroid.AssignName)
                    )
                    if (
                        recursive_klass
                        or defined_by_stmt
                        or annotation_return
                        or isinstance(defstmt, astroid.Delete)
                    ):
                        if not utils.node_ignores_exception(node, NameError):

                            # Handle postponed evaluation of annotations
                            if not (
                                self._postponed_evaluation_enabled
                                and isinstance(
                                    stmt,
                                    (
                                        astroid.AnnAssign,
                                        astroid.FunctionDef,
                                        astroid.Arguments,
                                    ),
                                )
                                and name in node.root().locals
                            ):
                                self.add_message(
                                    "undefined-variable", args=name, node=node
                                )
                    elif base_scope_type != "lambda":
                        # E0601 may *not* occurs in lambda scope.

                        # Handle postponed evaluation of annotations
                        if not (
                            self._postponed_evaluation_enabled
                            and isinstance(
                                stmt, (astroid.AnnAssign, astroid.FunctionDef)
                            )
                        ):
                            self.add_message(
                                "used-before-assignment", args=name, node=node
                            )
                    elif base_scope_type == "lambda":
                        # E0601 can occur in class-level scope in lambdas, as in
                        # the following example:
                        #   class A:
                        #      x = lambda attr: f + attr
                        #      f = 42
                        if isinstance(frame, astroid.ClassDef) and name in frame.locals:
                            if isinstance(node.parent, astroid.Arguments):
                                if stmt.fromlineno <= defstmt.fromlineno:
                                    # Doing the following is fine:
                                    #   class A:
                                    #      x = 42
                                    #      y = lambda attr=x: attr
                                    self.add_message(
                                        "used-before-assignment", args=name, node=node
                                    )
                            else:
                                self.add_message(
                                    "undefined-variable", args=name, node=node
                                )
                        elif current_consumer.scope_type == "lambda":
                            self.add_message("undefined-variable", node=node, args=name)

            current_consumer.mark_as_consumed(name, found_node)
            # check it's not a loop variable used outside the loop
            self._loopvar_name(node, name)
            break
        else:
            # we have not found the name, if it isn't a builtin, that's an
            # undefined name !
            if not (
                name in astroid.Module.scope_attrs
                or utils.is_builtin(name)
                or name in self.config.additional_builtins
            ):
                if not utils.node_ignores_exception(node, NameError):
                    self.add_message("undefined-variable", args=name, node=node)

    @utils.check_messages("no-name-in-module")
    def visit_import(self, node):
        """check modules attribute accesses"""
        if not self._analyse_fallback_blocks and utils.is_from_fallback_block(node):
            # No need to verify this, since ImportError is already
            # handled by the client code.
            return

        for name, _ in node.names:
            parts = name.split(".")
            try:
                module = next(_infer_name_module(node, parts[0]))
            except astroid.ResolveError:
                continue
            self._check_module_attrs(node, module, parts[1:])

    @utils.check_messages("no-name-in-module")
    def visit_importfrom(self, node):
        """check modules attribute accesses"""
        if not self._analyse_fallback_blocks and utils.is_from_fallback_block(node):
            # No need to verify this, since ImportError is already
            # handled by the client code.
            return

        name_parts = node.modname.split(".")
        try:
            module = node.do_import_module(name_parts[0])
        except astroid.AstroidBuildingException:
            return
        module = self._check_module_attrs(node, module, name_parts[1:])
        if not module:
            return
        for name, _ in node.names:
            if name == "*":
                continue
            self._check_module_attrs(node, module, name.split("."))

    @utils.check_messages(
        "unbalanced-tuple-unpacking", "unpacking-non-sequence", "self-cls-assignment"
    )
    def visit_assign(self, node):
        """Check unbalanced tuple unpacking for assignments
        and unpacking non-sequences as well as in case self/cls
        get assigned.
        """
        self._check_self_cls_assign(node)
        if not isinstance(node.targets[0], (astroid.Tuple, astroid.List)):
            return

        targets = node.targets[0].itered()
        try:
            inferred = utils.safe_infer(node.value)
            if inferred is not None:
                self._check_unpacking(inferred, node, targets)
        except astroid.InferenceError:
            return

    # listcomp have now also their scope
    def visit_listcomp(self, node):
        """visit dictcomp: update consumption analysis variable
        """
        self._to_consume.append(NamesConsumer(node, "comprehension"))

    def leave_listcomp(self, _):
        """leave dictcomp: update consumption analysis variable
        """
        # do not check for not used locals here
        self._to_consume.pop()

    def leave_assign(self, node):
        self._store_type_annotation_names(node)

    def leave_with(self, node):
        self._store_type_annotation_names(node)

    def visit_arguments(self, node):
        for annotation in node.type_comment_args:
            self._store_type_annotation_node(annotation)

    # Relying on other checker's options, which might not have been initialized yet.
    @decorators.cachedproperty
    def _analyse_fallback_blocks(self):
        return get_global_option(self, "analyse-fallback-blocks", default=False)

    @decorators.cachedproperty
    def _ignored_modules(self):
        return get_global_option(self, "ignored-modules", default=[])

    @decorators.cachedproperty
    def _allow_global_unused_variables(self):
        return get_global_option(self, "allow-global-unused-variables", default=True)

    @staticmethod
    def _defined_in_function_definition(node, frame):
        in_annotation_or_default = False
        if isinstance(frame, astroid.FunctionDef) and node.statement() is frame:
            in_annotation_or_default = (
                node in frame.args.annotations
                or node in frame.args.kwonlyargs_annotations
                or node is frame.args.varargannotation
                or node is frame.args.kwargannotation
            ) or frame.args.parent_of(node)
        return in_annotation_or_default

    @staticmethod
    def _is_variable_violation(
        node,
        name,
        defnode,
        stmt,
        defstmt,
        frame,
        defframe,
        base_scope_type,
        recursive_klass,
    ):
        # pylint: disable=too-many-nested-blocks
        # node: Node to check for violation
        # name: name of node to check violation for
        # frame: Scope of statement of node
        # base_scope_type: local scope type
        maybee0601 = True
        annotation_return = False
        use_outer_definition = False
        if frame is not defframe:
            maybee0601 = _detect_global_scope(node, frame, defframe)
        elif defframe.parent is None:
            # we are at the module level, check the name is not
            # defined in builtins
            if name in defframe.scope_attrs or astroid.builtin_lookup(name)[1]:
                maybee0601 = False
        else:
            # we are in a local scope, check the name is not
            # defined in global or builtin scope
            # skip this lookup if name is assigned later in function scope/lambda
            # Note: the node.frame() is not the same as the `frame` argument which is
            # equivalent to frame.statement().scope()
            forbid_lookup = (
                isinstance(frame, astroid.FunctionDef)
                or isinstance(node.frame(), astroid.Lambda)
            ) and _assigned_locally(node)
            if not forbid_lookup and defframe.root().lookup(name)[1]:
                maybee0601 = False
                use_outer_definition = stmt == defstmt and not isinstance(
                    defnode, astroid.node_classes.Comprehension
                )
            else:
                # check if we have a nonlocal
                if name in defframe.locals:
                    maybee0601 = not any(
                        isinstance(child, astroid.Nonlocal) and name in child.names
                        for child in defframe.get_children()
                    )

        if (
            base_scope_type == "lambda"
            and isinstance(frame, astroid.ClassDef)
            and name in frame.locals
        ):

            # This rule verifies that if the definition node of the
            # checked name is an Arguments node and if the name
            # is used a default value in the arguments defaults
            # and the actual definition of the variable label
            # is happening before the Arguments definition.
            #
            # bar = None
            # foo = lambda bar=bar: bar
            #
            # In this case, maybee0601 should be False, otherwise
            # it should be True.
            maybee0601 = not (
                isinstance(defnode, astroid.Arguments)
                and node in defnode.defaults
                and frame.locals[name][0].fromlineno < defstmt.fromlineno
            )
        elif isinstance(defframe, astroid.ClassDef) and isinstance(
            frame, astroid.FunctionDef
        ):
            # Special rule for function return annotations,
            # which uses the same name as the class where
            # the function lives.
            if node is frame.returns and defframe.parent_of(frame.returns):
                maybee0601 = annotation_return = True

            if (
                maybee0601
                and defframe.name in defframe.locals
                and defframe.locals[name][0].lineno < frame.lineno
            ):
                # Detect class assignments with the same
                # name as the class. In this case, no warning
                # should be raised.
                maybee0601 = False
            if isinstance(node.parent, astroid.Arguments):
                maybee0601 = stmt.fromlineno <= defstmt.fromlineno
        elif recursive_klass:
            maybee0601 = True
        else:
            maybee0601 = maybee0601 and stmt.fromlineno <= defstmt.fromlineno
            if maybee0601 and stmt.fromlineno == defstmt.fromlineno:
                if (
                    isinstance(defframe, astroid.FunctionDef)
                    and frame is defframe
                    and defframe.parent_of(node)
                    and stmt is not defstmt
                ):
                    # Single statement function, with the statement on the
                    # same line as the function definition
                    maybee0601 = False

            # Look for type checking definitions inside a type checking guard.
            if isinstance(defstmt, (astroid.Import, astroid.ImportFrom)):
                defstmt_parent = defstmt.parent

                if (
                    isinstance(defstmt_parent, astroid.If)
                    and defstmt_parent.test.as_string() in TYPING_TYPE_CHECKS_GUARDS
                ):
                    # Exempt those definitions that are used inside the type checking
                    # guard or that are defined in both type checking guard branches.
                    used_in_branch = defstmt_parent.parent_of(node)
                    defined_in_or_else = False

                    for definition in defstmt_parent.orelse:
                        if isinstance(definition, astroid.Assign):
                            defined_in_or_else = any(
                                target.name == name for target in definition.targets
                            )
                            if defined_in_or_else:
                                break

                    if not used_in_branch and not defined_in_or_else:
                        maybee0601 = True

        return maybee0601, annotation_return, use_outer_definition

    def _ignore_class_scope(self, node):
        """
        Return True if the node is in a local class scope, as an assignment.

        :param node: Node considered
        :type node: astroid.Node
        :return: True if the node is in a local class scope, as an assignment. False otherwise.
        :rtype: bool
        """
        # Detect if we are in a local class scope, as an assignment.
        # For example, the following is fair game.
        #
        # class A:
        #    b = 1
        #    c = lambda b=b: b * b
        #
        # class B:
        #    tp = 1
        #    def func(self, arg: tp):
        #        ...
        # class C:
        #    tp = 2
        #    def func(self, arg=tp):
        #        ...

        name = node.name
        frame = node.statement().scope()
        in_annotation_or_default = self._defined_in_function_definition(node, frame)
        if in_annotation_or_default:
            frame_locals = frame.parent.scope().locals
        else:
            frame_locals = frame.locals
        return not (
            (isinstance(frame, astroid.ClassDef) or in_annotation_or_default)
            and name in frame_locals
        )

    def _loopvar_name(self, node, name):
        # filter variables according to node's scope
        if not self.linter.is_message_enabled("undefined-loop-variable"):
            return
        astmts = [stmt for stmt in node.lookup(name)[1] if hasattr(stmt, "assign_type")]
        # If this variable usage exists inside a function definition
        # that exists in the same loop,
        # the usage is safe because the function will not be defined either if
        # the variable is not defined.
        scope = node.scope()
        if isinstance(scope, astroid.FunctionDef) and any(
            asmt.statement().parent_of(scope) for asmt in astmts
        ):
            return

        # filter variables according their respective scope test is_statement
        # and parent to avoid #74747. This is not a total fix, which would
        # introduce a mechanism similar to special attribute lookup in
        # modules. Also, in order to get correct inference in this case, the
        # scope lookup rules would need to be changed to return the initial
        # assignment (which does not exist in code per se) as well as any later
        # modifications.
        if (
            not astmts
            or (astmts[0].is_statement or astmts[0].parent)
            and astmts[0].statement().parent_of(node)
        ):
            _astmts = []
        else:
            _astmts = astmts[:1]
        for i, stmt in enumerate(astmts[1:]):
            if astmts[i].statement().parent_of(stmt) and not in_for_else_branch(
                astmts[i].statement(), stmt
            ):
                continue
            _astmts.append(stmt)
        astmts = _astmts
        if len(astmts) != 1:
            return

        assign = astmts[0].assign_type()
        if not (
            isinstance(
                assign, (astroid.For, astroid.Comprehension, astroid.GeneratorExp)
            )
            and assign.statement() is not node.statement()
        ):
            return

        # For functions we can do more by inferring the length of the itered object
        if not isinstance(assign, astroid.For):
            self.add_message("undefined-loop-variable", args=name, node=node)
            return

        try:
            inferred = next(assign.iter.infer())
        except astroid.InferenceError:
            self.add_message("undefined-loop-variable", args=name, node=node)
        else:
            if (
                isinstance(inferred, astroid.Instance)
                and inferred.qname() == BUILTIN_RANGE
            ):
                # Consider range() objects safe, even if they might not yield any results.
                return

            # Consider sequences.
            sequences = (
                astroid.List,
                astroid.Tuple,
                astroid.Dict,
                astroid.Set,
                objects.FrozenSet,
            )
            if not isinstance(inferred, sequences):
                self.add_message("undefined-loop-variable", args=name, node=node)
                return

            elements = getattr(inferred, "elts", getattr(inferred, "items", []))
            if not elements:
                self.add_message("undefined-loop-variable", args=name, node=node)

    def _check_is_unused(self, name, node, stmt, global_names, nonlocal_names):
        # pylint: disable=too-many-branches
        # Ignore some special names specified by user configuration.
        if self._is_name_ignored(stmt, name):
            return
        # Ignore names that were added dynamically to the Function scope
        if (
            isinstance(node, astroid.FunctionDef)
            and name == "__class__"
            and len(node.locals["__class__"]) == 1
            and isinstance(node.locals["__class__"][0], astroid.ClassDef)
        ):
            return

        # Ignore names imported by the global statement.
        if isinstance(stmt, (astroid.Global, astroid.Import, astroid.ImportFrom)):
            # Detect imports, assigned to global statements.
            if global_names and _import_name_is_global(stmt, global_names):
                return

        argnames = list(
            itertools.chain(node.argnames(), [arg.name for arg in node.args.kwonlyargs])
        )
        # Care about functions with unknown argument (builtins)
        if name in argnames:
            self._check_unused_arguments(name, node, stmt, argnames)
        else:
            if stmt.parent and isinstance(
                stmt.parent, (astroid.Assign, astroid.AnnAssign)
            ):
                if name in nonlocal_names:
                    return

            qname = asname = None
            if isinstance(stmt, (astroid.Import, astroid.ImportFrom)):
                # Need the complete name, which we don't have in .locals.
                if len(stmt.names) > 1:
                    import_names = next(
                        (names for names in stmt.names if name in names), None
                    )
                else:
                    import_names = stmt.names[0]
                if import_names:
                    qname, asname = import_names
                    name = asname or qname

            if _has_locals_call_after_node(stmt, node.scope()):
                message_name = "possibly-unused-variable"
            else:
                if isinstance(stmt, astroid.Import):
                    if asname is not None:
                        msg = "%s imported as %s" % (qname, asname)
                    else:
                        msg = "import %s" % name
                    self.add_message("unused-import", args=msg, node=stmt)
                    return
                if isinstance(stmt, astroid.ImportFrom):
                    if asname is not None:
                        msg = "%s imported from %s as %s" % (
                            qname,
                            stmt.modname,
                            asname,
                        )
                    else:
                        msg = "%s imported from %s" % (name, stmt.modname)
                    self.add_message("unused-import", args=msg, node=stmt)
                    return
                message_name = "unused-variable"

            # Don't check function stubs created only for type information
            if utils.is_overload_stub(node):
                return

            self.add_message(message_name, args=name, node=stmt)

    def _is_name_ignored(self, stmt, name):
        authorized_rgx = self.config.dummy_variables_rgx
        if (
            isinstance(stmt, astroid.AssignName)
            and isinstance(stmt.parent, astroid.Arguments)
            or isinstance(stmt, astroid.Arguments)
        ):
            regex = self.config.ignored_argument_names
        else:
            regex = authorized_rgx
        return regex and regex.match(name)

    def _check_unused_arguments(self, name, node, stmt, argnames):
        is_method = node.is_method()
        klass = node.parent.frame()
        if is_method and isinstance(klass, astroid.ClassDef):
            confidence = (
                INFERENCE if utils.has_known_bases(klass) else INFERENCE_FAILURE
            )
        else:
            confidence = HIGH

        if is_method:
            # Don't warn for the first argument of a (non static) method
            if node.type != "staticmethod" and name == argnames[0]:
                return
            # Don't warn for argument of an overridden method
            overridden = overridden_method(klass, node.name)
            if overridden is not None and name in overridden.argnames():
                return
            if node.name in utils.PYMETHODS and node.name not in (
                "__init__",
                "__new__",
            ):
                return
        # Don't check callback arguments
        if any(
            node.name.startswith(cb) or node.name.endswith(cb)
            for cb in self.config.callbacks
        ):
            return
        # Don't check arguments of singledispatch.register function.
        if utils.is_registered_in_singledispatch_function(node):
            return

        # Don't check function stubs created only for type information
        if utils.is_overload_stub(node):
            return

        # Don't check protocol classes
        if utils.is_protocol_class(klass):
            return

        self.add_message("unused-argument", args=name, node=stmt, confidence=confidence)

    def _check_late_binding_closure(self, node, assignment_node):
        def _is_direct_lambda_call():
            return (
                isinstance(node_scope.parent, astroid.Call)
                and node_scope.parent.func is node_scope
            )

        node_scope = node.scope()
        if not isinstance(node_scope, (astroid.Lambda, astroid.FunctionDef)):
            return
        if isinstance(node.parent, astroid.Arguments):
            return

        if isinstance(assignment_node, astroid.Comprehension):
            if assignment_node.parent.parent_of(node.scope()):
                self.add_message("cell-var-from-loop", node=node, args=node.name)
        else:
            assign_scope = assignment_node.scope()
            maybe_for = assignment_node
            while not isinstance(maybe_for, astroid.For):
                if maybe_for is assign_scope:
                    break
                maybe_for = maybe_for.parent
            else:
                if (
                    maybe_for.parent_of(node_scope)
                    and not _is_direct_lambda_call()
                    and not isinstance(node_scope.statement(), astroid.Return)
                ):
                    self.add_message("cell-var-from-loop", node=node, args=node.name)

    def _should_ignore_redefined_builtin(self, stmt):
        if not isinstance(stmt, astroid.ImportFrom):
            return False
        return stmt.modname in self.config.redefining_builtins_modules

    def _has_homonym_in_upper_function_scope(self, node, index):
        """
        Return True if there is a node with the same name in the to_consume dict of an upper scope
        and if that scope is a function

        :param node: node to check for
        :type node: astroid.Node
        :param index: index of the current consumer inside self._to_consume
        :type index: int
        :return: True if there is a node with the same name in the to_consume dict of an upper scope
                 and if that scope is a function
        :rtype: bool
        """
        for _consumer in self._to_consume[index - 1 :: -1]:
            if _consumer.scope_type == "function" and node.name in _consumer.to_consume:
                return True
        return False

    def _store_type_annotation_node(self, type_annotation):
        """Given a type annotation, store all the name nodes it refers to"""
        if isinstance(type_annotation, astroid.Name):
            self._type_annotation_names.append(type_annotation.name)
            return

        if not isinstance(type_annotation, astroid.Subscript):
            return

        if (
            isinstance(type_annotation.value, astroid.Attribute)
            and isinstance(type_annotation.value.expr, astroid.Name)
            and type_annotation.value.expr.name == TYPING_MODULE
        ):
            self._type_annotation_names.append(TYPING_MODULE)
            return

        self._type_annotation_names.extend(
            annotation.name
            for annotation in type_annotation.nodes_of_class(astroid.Name)
        )

    def _store_type_annotation_names(self, node):
        type_annotation = node.type_annotation
        if not type_annotation:
            return
        self._store_type_annotation_node(node.type_annotation)

    def _check_self_cls_assign(self, node):
        """Check that self/cls don't get assigned"""
        assign_names = {
            target.name
            for target in node.targets
            if isinstance(target, astroid.AssignName)
        }
        scope = node.scope()
        nonlocals_with_same_name = any(
            child
            for child in scope.body
            if isinstance(child, astroid.Nonlocal) and assign_names & set(child.names)
        )
        if nonlocals_with_same_name:
            scope = node.scope().parent.scope()

        if not (
            isinstance(scope, astroid.scoped_nodes.FunctionDef)
            and scope.is_method()
            and "builtins.staticmethod" not in scope.decoratornames()
        ):
            return
        argument_names = scope.argnames()
        if not argument_names:
            return
        self_cls_name = argument_names[0]
        target_assign_names = (
            target.name
            for target in node.targets
            if isinstance(target, astroid.node_classes.AssignName)
        )
        if self_cls_name in target_assign_names:
            self.add_message("self-cls-assignment", node=node, args=(self_cls_name))

    def _check_unpacking(self, inferred, node, targets):
        """ Check for unbalanced tuple unpacking
        and unpacking non sequences.
        """
        if utils.is_inside_abstract_class(node):
            return
        if utils.is_comprehension(node):
            return
        if inferred is astroid.Uninferable:
            return
        if (
            isinstance(inferred.parent, astroid.Arguments)
            and isinstance(node.value, astroid.Name)
            and node.value.name == inferred.parent.vararg
        ):
            # Variable-length argument, we can't determine the length.
            return
        if isinstance(inferred, (astroid.Tuple, astroid.List)):
            # attempt to check unpacking is properly balanced
            values = inferred.itered()
            if len(targets) != len(values):
                # Check if we have starred nodes.
                if any(isinstance(target, astroid.Starred) for target in targets):
                    return
                self.add_message(
                    "unbalanced-tuple-unpacking",
                    node=node,
                    args=(
                        _get_unpacking_extra_info(node, inferred),
                        len(targets),
                        len(values),
                    ),
                )
        # attempt to check unpacking may be possible (ie RHS is iterable)
        else:
            if not utils.is_iterable(inferred):
                self.add_message(
                    "unpacking-non-sequence",
                    node=node,
                    args=(_get_unpacking_extra_info(node, inferred),),
                )

    def _check_module_attrs(self, node, module, module_names):
        """check that module_names (list of string) are accessible through the
        given module
        if the latest access name corresponds to a module, return it
        """
        assert isinstance(module, astroid.Module), module
        while module_names:
            name = module_names.pop(0)
            if name == "__dict__":
                module = None
                break
            try:
                module = next(module.getattr(name)[0].infer())
                if module is astroid.Uninferable:
                    return None
            except astroid.NotFoundError:
                if module.name in self._ignored_modules:
                    return None
                self.add_message(
                    "no-name-in-module", args=(name, module.name), node=node
                )
                return None
            except astroid.InferenceError:
                return None
        if module_names:
            modname = module.name if module else "__dict__"
            self.add_message(
                "no-name-in-module", node=node, args=(".".join(module_names), modname)
            )
            return None
        if isinstance(module, astroid.Module):
            return module
        return None

    def _check_all(self, node, not_consumed):
        assigned = next(node.igetattr("__all__"))
        if assigned is astroid.Uninferable:
            return

        for elt in getattr(assigned, "elts", ()):
            try:
                elt_name = next(elt.infer())
            except astroid.InferenceError:
                continue
            if elt_name is astroid.Uninferable:
                continue
            if not elt_name.parent:
                continue

            if not isinstance(elt_name, astroid.Const) or not isinstance(
                elt_name.value, str
            ):
                self.add_message("invalid-all-object", args=elt.as_string(), node=elt)
                continue

            elt_name = elt_name.value
            # If elt is in not_consumed, remove it from not_consumed
            if elt_name in not_consumed:
                del not_consumed[elt_name]
                continue

            if elt_name not in node.locals:
                if not node.package:
                    self.add_message(
                        "undefined-all-variable", args=(elt_name,), node=elt
                    )
                else:
                    basename = os.path.splitext(node.file)[0]
                    if os.path.basename(basename) == "__init__":
                        name = node.name + "." + elt_name
                        try:
                            modutils.file_from_modpath(name.split("."))
                        except ImportError:
                            self.add_message(
                                "undefined-all-variable", args=(elt_name,), node=elt
                            )
                        except SyntaxError:
                            # don't yield a syntax-error warning,
                            # because it will be later yielded
                            # when the file will be checked
                            pass

    def _check_globals(self, not_consumed):
        if self._allow_global_unused_variables:
            return
        for name, nodes in not_consumed.items():
            for node in nodes:
                self.add_message("unused-variable", args=(name,), node=node)

    def _check_imports(self, not_consumed):
        local_names = _fix_dot_imports(not_consumed)
        checked = set()
        for name, stmt in local_names:
            for imports in stmt.names:
                real_name = imported_name = imports[0]
                if imported_name == "*":
                    real_name = name
                as_name = imports[1]
                if real_name in checked:
                    continue
                if name not in (real_name, as_name):
                    continue
                checked.add(real_name)

                if isinstance(stmt, astroid.Import) or (
                    isinstance(stmt, astroid.ImportFrom) and not stmt.modname
                ):
                    if isinstance(stmt, astroid.ImportFrom) and SPECIAL_OBJ.search(
                        imported_name
                    ):
                        # Filter special objects (__doc__, __all__) etc.,
                        # because they can be imported for exporting.
                        continue

                    if imported_name in self._type_annotation_names:
                        # Most likely a typing import if it wasn't used so far.
                        continue

                    if as_name == "_":
                        continue
                    if as_name is None:
                        msg = "import %s" % imported_name
                    else:
                        msg = "%s imported as %s" % (imported_name, as_name)
                    if not _is_type_checking_import(stmt):
                        self.add_message("unused-import", args=msg, node=stmt)
                elif isinstance(stmt, astroid.ImportFrom) and stmt.modname != FUTURE:
                    if SPECIAL_OBJ.search(imported_name):
                        # Filter special objects (__doc__, __all__) etc.,
                        # because they can be imported for exporting.
                        continue

                    if _is_from_future_import(stmt, name):
                        # Check if the name is in fact loaded from a
                        # __future__ import in another module.
                        continue

                    if imported_name in self._type_annotation_names:
                        # Most likely a typing import if it wasn't used so far.
                        continue

                    if imported_name == "*":
                        self.add_message("unused-wildcard-import", args=name, node=stmt)
                    else:
                        if as_name is None:
                            msg = "%s imported from %s" % (imported_name, stmt.modname)
                        else:
                            fields = (imported_name, stmt.modname, as_name)
                            msg = "%s imported from %s as %s" % fields
                        if not _is_type_checking_import(stmt):
                            self.add_message("unused-import", args=msg, node=stmt)
        del self._to_consume

    def _check_metaclasses(self, node):
        """ Update consumption analysis for metaclasses. """
        consumed = []  # [(scope_locals, consumed_key)]

        for child_node in node.get_children():
            if isinstance(child_node, astroid.ClassDef):
                consumed.extend(self._check_classdef_metaclasses(child_node, node))

        # Pop the consumed items, in order to avoid having
        # unused-import and unused-variable false positives
        for scope_locals, name in consumed:
            scope_locals.pop(name, None)

    def _check_classdef_metaclasses(self, klass, parent_node):
        if not klass._metaclass:
            # Skip if this class doesn't use explicitly a metaclass, but inherits it from ancestors
            return []

        consumed = []  # [(scope_locals, consumed_key)]
        metaclass = klass.metaclass()

        name = None
        if isinstance(klass._metaclass, astroid.Name):
            name = klass._metaclass.name
        elif metaclass:
            name = metaclass.root().name

        found = None
        name = METACLASS_NAME_TRANSFORMS.get(name, name)
        if name:
            # check enclosing scopes starting from most local
            for scope_locals, _, _ in self._to_consume[::-1]:
                found = scope_locals.get(name)
                if found:
                    consumed.append((scope_locals, name))
                    break

        if found is None and not metaclass:
            name = None
            if isinstance(klass._metaclass, astroid.Name):
                name = klass._metaclass.name
            elif isinstance(klass._metaclass, astroid.Attribute):
                name = klass._metaclass.as_string()

            if name is not None:
                if not (
                    name in astroid.Module.scope_attrs
                    or utils.is_builtin(name)
                    or name in self.config.additional_builtins
                    or name in parent_node.locals
                ):
                    self.add_message("undefined-variable", node=klass, args=(name,))

        return consumed


def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(VariablesChecker(linter))
