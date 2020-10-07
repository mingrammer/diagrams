# -*- coding: utf-8 -*-
# Copyright (c) 2016-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2016-2017 Łukasz Rogalski <rogalski.91@gmail.com>
# Copyright (c) 2016 Moises Lopez <moylop260@vauxoo.com>
# Copyright (c) 2016 Alexander Todorov <atodorov@otb.bg>
# Copyright (c) 2017-2018 hippo91 <guillaume.peillex@gmail.com>
# Copyright (c) 2017 Ville Skyttä <ville.skytta@iki.fi>
# Copyright (c) 2017-2018 Bryce Guinta <bryce.paul.guinta@gmail.com>
# Copyright (c) 2017 Hugo <hugovk@users.noreply.github.com>
# Copyright (c) 2017 Łukasz Sznuk <ls@rdprojekt.pl>
# Copyright (c) 2017 Alex Hearn <alex.d.hearn@gmail.com>
# Copyright (c) 2017 Antonio Ossa <aaossa@uc.cl>
# Copyright (c) 2018 Konstantin Manna <Konstantin@Manna.uno>
# Copyright (c) 2018 Konstantin <Github@pheanex.de>
# Copyright (c) 2018 Sushobhit <31987769+sushobhit27@users.noreply.github.com>
# Copyright (c) 2018 Matej Marušák <marusak.matej@gmail.com>
# Copyright (c) 2018 Ville Skyttä <ville.skytta@upcloud.com>
# Copyright (c) 2018 Mr. Senko <atodorov@mrsenko.com>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""Looks for code which can be refactored."""
import builtins
import collections
import itertools
import tokenize
from functools import reduce

import astroid
from astroid import decorators

from pylint import checkers, interfaces
from pylint import utils as lint_utils
from pylint.checkers import utils

KNOWN_INFINITE_ITERATORS = {"itertools.count"}
BUILTIN_EXIT_FUNCS = frozenset(("quit", "exit"))


def _if_statement_is_always_returning(if_node, returning_node_class):
    for node in if_node.body:
        if isinstance(node, returning_node_class):
            return True
    return False


def _is_len_call(node):
    """Checks if node is len(SOMETHING)."""
    return (
        isinstance(node, astroid.Call)
        and isinstance(node.func, astroid.Name)
        and node.func.name == "len"
    )


def _is_constant_zero(node):
    return isinstance(node, astroid.Const) and node.value == 0


def _node_is_test_condition(node):
    """ Checks if node is an if, while, assert or if expression statement."""
    return isinstance(node, (astroid.If, astroid.While, astroid.Assert, astroid.IfExp))


def _is_trailing_comma(tokens, index):
    """Check if the given token is a trailing comma

    :param tokens: Sequence of modules tokens
    :type tokens: list[tokenize.TokenInfo]
    :param int index: Index of token under check in tokens
    :returns: True if the token is a comma which trails an expression
    :rtype: bool
    """
    token = tokens[index]
    if token.exact_type != tokenize.COMMA:
        return False
    # Must have remaining tokens on the same line such as NEWLINE
    left_tokens = itertools.islice(tokens, index + 1, None)
    same_line_remaining_tokens = list(
        itertools.takewhile(
            lambda other_token, _token=token: other_token.start[0] == _token.start[0],
            left_tokens,
        )
    )
    # Note: If the newline is tokenize.NEWLINE and not tokenize.NL
    # then the newline denotes the end of expression
    is_last_element = all(
        other_token.type in (tokenize.NEWLINE, tokenize.COMMENT)
        for other_token in same_line_remaining_tokens
    )
    if not same_line_remaining_tokens or not is_last_element:
        return False

    def get_curline_index_start():
        """Get the index denoting the start of the current line"""
        for subindex, token in enumerate(reversed(tokens[:index])):
            # See Lib/tokenize.py and Lib/token.py in cpython for more info
            if token.type in (tokenize.NEWLINE, tokenize.NL):
                return index - subindex
        return 0

    curline_start = get_curline_index_start()
    expected_tokens = {"return", "yield"}
    for prevtoken in tokens[curline_start:index]:
        if "=" in prevtoken.string or prevtoken.string in expected_tokens:
            return True
    return False


class RefactoringChecker(checkers.BaseTokenChecker):
    """Looks for code which can be refactored

    This checker also mixes the astroid and the token approaches
    in order to create knowledge about whether an "else if" node
    is a true "else if" node, or an "elif" node.
    """

    __implements__ = (interfaces.ITokenChecker, interfaces.IAstroidChecker)

    name = "refactoring"

    msgs = {
        "R1701": (
            "Consider merging these isinstance calls to isinstance(%s, (%s))",
            "consider-merging-isinstance",
            "Used when multiple consecutive isinstance calls can be merged into one.",
        ),
        "R1706": (
            "Consider using ternary (%s)",
            "consider-using-ternary",
            "Used when one of known pre-python 2.5 ternary syntax is used.",
        ),
        "R1709": (
            "Boolean expression may be simplified to %s",
            "simplify-boolean-expression",
            "Emitted when redundant pre-python 2.5 ternary syntax is used.",
        ),
        "R1702": (
            "Too many nested blocks (%s/%s)",
            "too-many-nested-blocks",
            "Used when a function or a method has too many nested "
            "blocks. This makes the code less understandable and "
            "maintainable.",
            {"old_names": [("R0101", "old-too-many-nested-blocks")]},
        ),
        "R1703": (
            "The if statement can be replaced with %s",
            "simplifiable-if-statement",
            "Used when an if statement can be replaced with 'bool(test)'. ",
            {"old_names": [("R0102", "old-simplifiable-if-statement")]},
        ),
        "R1704": (
            "Redefining argument with the local name %r",
            "redefined-argument-from-local",
            "Used when a local name is redefining an argument, which might "
            "suggest a potential error. This is taken in account only for "
            "a handful of name binding operations, such as for iteration, "
            "with statement assignment and exception handler assignment.",
        ),
        "R1705": (
            'Unnecessary "%s" after "return"',
            "no-else-return",
            "Used in order to highlight an unnecessary block of "
            "code following an if containing a return statement. "
            "As such, it will warn when it encounters an else "
            "following a chain of ifs, all of them containing a "
            "return statement.",
        ),
        "R1707": (
            "Disallow trailing comma tuple",
            "trailing-comma-tuple",
            "In Python, a tuple is actually created by the comma symbol, "
            "not by the parentheses. Unfortunately, one can actually create a "
            "tuple by misplacing a trailing comma, which can lead to potential "
            "weird bugs in your code. You should always use parentheses "
            "explicitly for creating a tuple.",
        ),
        "R1708": (
            "Do not raise StopIteration in generator, use return statement instead",
            "stop-iteration-return",
            "According to PEP479, the raise of StopIteration to end the loop of "
            "a generator may lead to hard to find bugs. This PEP specify that "
            "raise StopIteration has to be replaced by a simple return statement",
        ),
        "R1710": (
            "Either all return statements in a function should return an expression, "
            "or none of them should.",
            "inconsistent-return-statements",
            "According to PEP8, if any return statement returns an expression, "
            "any return statements where no value is returned should explicitly "
            "state this as return None, and an explicit return statement "
            "should be present at the end of the function (if reachable)",
        ),
        "R1711": (
            "Useless return at end of function or method",
            "useless-return",
            'Emitted when a single "return" or "return None" statement is found '
            "at the end of function or method definition. This statement can safely be "
            "removed because Python will implicitly return None",
        ),
        "R1712": (
            "Consider using tuple unpacking for swapping variables",
            "consider-swap-variables",
            "You do not have to use a temporary variable in order to "
            'swap variables. Using "tuple unpacking" to directly swap '
            "variables makes the intention more clear.",
        ),
        "R1713": (
            "Consider using str.join(sequence) for concatenating "
            "strings from an iterable",
            "consider-using-join",
            "Using str.join(sequence) is faster, uses less memory "
            "and increases readability compared to for-loop iteration.",
        ),
        "R1714": (
            'Consider merging these comparisons with "in" to %r',
            "consider-using-in",
            "To check if a variable is equal to one of many values,"
            'combine the values into a tuple and check if the variable is contained "in" it '
            "instead of checking for equality against each of the values."
            "This is faster and less verbose.",
        ),
        "R1715": (
            "Consider using dict.get for getting values from a dict "
            "if a key is present or a default if not",
            "consider-using-get",
            "Using the builtin dict.get for getting a value from a dictionary "
            "if a key is present or a default if not, is simpler and considered "
            "more idiomatic, although sometimes a bit slower",
        ),
        "R1716": (
            "Simplify chained comparison between the operands",
            "chained-comparison",
            "This message is emitted when pylint encounters boolean operation like"
            '"a < b and b < c", suggesting instead to refactor it to "a < b < c"',
        ),
        "R1717": (
            "Consider using a dictionary comprehension",
            "consider-using-dict-comprehension",
            "Emitted when we detect the creation of a dictionary "
            "using the dict() callable and a transient list. "
            "Although there is nothing syntactically wrong with this code, "
            "it is hard to read and can be simplified to a dict comprehension."
            "Also it is faster since you don't need to create another "
            "transient list",
        ),
        "R1718": (
            "Consider using a set comprehension",
            "consider-using-set-comprehension",
            "Although there is nothing syntactically wrong with this code, "
            "it is hard to read and can be simplified to a set comprehension."
            "Also it is faster since you don't need to create another "
            "transient list",
        ),
        "R1719": (
            "The if expression can be replaced with %s",
            "simplifiable-if-expression",
            "Used when an if expression can be replaced with 'bool(test)'. ",
        ),
        "R1720": (
            'Unnecessary "%s" after "raise"',
            "no-else-raise",
            "Used in order to highlight an unnecessary block of "
            "code following an if containing a raise statement. "
            "As such, it will warn when it encounters an else "
            "following a chain of ifs, all of them containing a "
            "raise statement.",
        ),
        "R1721": (
            "Unnecessary use of a comprehension",
            "unnecessary-comprehension",
            "Instead of using an identitiy comprehension, "
            "consider using the list, dict or set constructor. "
            "It is faster and simpler.",
        ),
        "R1722": (
            "Consider using sys.exit()",
            "consider-using-sys-exit",
            "Instead of using exit() or quit(), consider using the sys.exit().",
        ),
        "R1723": (
            'Unnecessary "%s" after "break"',
            "no-else-break",
            "Used in order to highlight an unnecessary block of "
            "code following an if containing a break statement. "
            "As such, it will warn when it encounters an else "
            "following a chain of ifs, all of them containing a "
            "break statement.",
        ),
        "R1724": (
            'Unnecessary "%s" after "continue"',
            "no-else-continue",
            "Used in order to highlight an unnecessary block of "
            "code following an if containing a continue statement. "
            "As such, it will warn when it encounters an else "
            "following a chain of ifs, all of them containing a "
            "continue statement.",
        ),
    }
    options = (
        (
            "max-nested-blocks",
            {
                "default": 5,
                "type": "int",
                "metavar": "<int>",
                "help": "Maximum number of nested blocks for function / method body",
            },
        ),
        (
            "never-returning-functions",
            {
                "default": ("sys.exit",),
                "type": "csv",
                "help": "Complete name of functions that never returns. When checking "
                "for inconsistent-return-statements if a never returning function is "
                "called then it will be considered as an explicit return statement "
                "and no message will be printed.",
            },
        ),
    )

    priority = 0

    def __init__(self, linter=None):
        checkers.BaseTokenChecker.__init__(self, linter)
        self._return_nodes = {}
        self._init()
        self._never_returning_functions = None

    def _init(self):
        self._nested_blocks = []
        self._elifs = []
        self._nested_blocks_msg = None
        self._reported_swap_nodes = set()

    def open(self):
        # do this in open since config not fully initialized in __init__
        self._never_returning_functions = set(self.config.never_returning_functions)

    @decorators.cachedproperty
    def _dummy_rgx(self):
        return lint_utils.get_global_option(self, "dummy-variables-rgx", default=None)

    @staticmethod
    def _is_bool_const(node):
        return isinstance(node.value, astroid.Const) and isinstance(
            node.value.value, bool
        )

    def _is_actual_elif(self, node):
        """Check if the given node is an actual elif

        This is a problem we're having with the builtin ast module,
        which splits `elif` branches into a separate if statement.
        Unfortunately we need to know the exact type in certain
        cases.
        """
        if isinstance(node.parent, astroid.If):
            orelse = node.parent.orelse
            # current if node must directly follow an "else"
            if orelse and orelse == [node]:
                if (node.lineno, node.col_offset) in self._elifs:
                    return True
        return False

    def _check_simplifiable_if(self, node):
        """Check if the given if node can be simplified.

        The if statement can be reduced to a boolean expression
        in some cases. For instance, if there are two branches
        and both of them return a boolean value that depends on
        the result of the statement's test, then this can be reduced
        to `bool(test)` without losing any functionality.
        """

        if self._is_actual_elif(node):
            # Not interested in if statements with multiple branches.
            return
        if len(node.orelse) != 1 or len(node.body) != 1:
            return

        # Check if both branches can be reduced.
        first_branch = node.body[0]
        else_branch = node.orelse[0]
        if isinstance(first_branch, astroid.Return):
            if not isinstance(else_branch, astroid.Return):
                return
            first_branch_is_bool = self._is_bool_const(first_branch)
            else_branch_is_bool = self._is_bool_const(else_branch)
            reduced_to = "'return bool(test)'"
        elif isinstance(first_branch, astroid.Assign):
            if not isinstance(else_branch, astroid.Assign):
                return

            # Check if we assign to the same value
            first_branch_targets = [
                target.name
                for target in first_branch.targets
                if isinstance(target, astroid.AssignName)
            ]
            else_branch_targets = [
                target.name
                for target in else_branch.targets
                if isinstance(target, astroid.AssignName)
            ]
            if not first_branch_targets or not else_branch_targets:
                return
            if sorted(first_branch_targets) != sorted(else_branch_targets):
                return

            first_branch_is_bool = self._is_bool_const(first_branch)
            else_branch_is_bool = self._is_bool_const(else_branch)
            reduced_to = "'var = bool(test)'"
        else:
            return

        if not first_branch_is_bool or not else_branch_is_bool:
            return
        if not first_branch.value.value:
            # This is a case that can't be easily simplified and
            # if it can be simplified, it will usually result in a
            # code that's harder to understand and comprehend.
            # Let's take for instance `arg and arg <= 3`. This could theoretically be
            # reduced to `not arg or arg > 3`, but the net result is that now the
            # condition is harder to understand, because it requires understanding of
            # an extra clause:
            #   * first, there is the negation of truthness with `not arg`
            #   * the second clause is `arg > 3`, which occurs when arg has a
            #     a truth value, but it implies that `arg > 3` is equivalent
            #     with `arg and arg > 3`, which means that the user must
            #     think about this assumption when evaluating `arg > 3`.
            #     The original form is easier to grasp.
            return

        self.add_message("simplifiable-if-statement", node=node, args=(reduced_to,))

    def process_tokens(self, tokens):
        # Process tokens and look for 'if' or 'elif'
        for index, token in enumerate(tokens):
            token_string = token[1]
            if token_string == "elif":
                # AST exists by the time process_tokens is called, so
                # it's safe to assume tokens[index+1]
                # exists. tokens[index+1][2] is the elif's position as
                # reported by CPython and PyPy,
                # tokens[index][2] is the actual position and also is
                # reported by IronPython.
                self._elifs.extend([tokens[index][2], tokens[index + 1][2]])
            elif _is_trailing_comma(tokens, index):
                if self.linter.is_message_enabled("trailing-comma-tuple"):
                    self.add_message("trailing-comma-tuple", line=token.start[0])

    def leave_module(self, _):
        self._init()

    @utils.check_messages("too-many-nested-blocks")
    def visit_tryexcept(self, node):
        self._check_nested_blocks(node)

    visit_tryfinally = visit_tryexcept
    visit_while = visit_tryexcept

    def _check_redefined_argument_from_local(self, name_node):
        if self._dummy_rgx and self._dummy_rgx.match(name_node.name):
            return
        if not name_node.lineno:
            # Unknown position, maybe it is a manually built AST?
            return

        scope = name_node.scope()
        if not isinstance(scope, astroid.FunctionDef):
            return

        for defined_argument in scope.args.nodes_of_class(
            astroid.AssignName, skip_klass=(astroid.Lambda,)
        ):
            if defined_argument.name == name_node.name:
                self.add_message(
                    "redefined-argument-from-local",
                    node=name_node,
                    args=(name_node.name,),
                )

    @utils.check_messages("redefined-argument-from-local", "too-many-nested-blocks")
    def visit_for(self, node):
        self._check_nested_blocks(node)

        for name in node.target.nodes_of_class(astroid.AssignName):
            self._check_redefined_argument_from_local(name)

    @utils.check_messages("redefined-argument-from-local")
    def visit_excepthandler(self, node):
        if node.name and isinstance(node.name, astroid.AssignName):
            self._check_redefined_argument_from_local(node.name)

    @utils.check_messages("redefined-argument-from-local")
    def visit_with(self, node):
        for _, names in node.items:
            if not names:
                continue
            for name in names.nodes_of_class(astroid.AssignName):
                self._check_redefined_argument_from_local(name)

    def _check_superfluous_else(self, node, msg_id, returning_node_class):
        if not node.orelse:
            # Not interested in if statements without else.
            return

        if self._is_actual_elif(node):
            # Not interested in elif nodes; only if
            return

        if _if_statement_is_always_returning(node, returning_node_class):
            orelse = node.orelse[0]
            followed_by_elif = (orelse.lineno, orelse.col_offset) in self._elifs
            self.add_message(
                msg_id, node=node, args="elif" if followed_by_elif else "else"
            )

    def _check_superfluous_else_return(self, node):
        return self._check_superfluous_else(
            node, msg_id="no-else-return", returning_node_class=astroid.Return
        )

    def _check_superfluous_else_raise(self, node):
        return self._check_superfluous_else(
            node, msg_id="no-else-raise", returning_node_class=astroid.Raise
        )

    def _check_superfluous_else_break(self, node):
        return self._check_superfluous_else(
            node, msg_id="no-else-break", returning_node_class=astroid.Break
        )

    def _check_superfluous_else_continue(self, node):
        return self._check_superfluous_else(
            node, msg_id="no-else-continue", returning_node_class=astroid.Continue
        )

    def _check_consider_get(self, node):
        def type_and_name_are_equal(node_a, node_b):
            for _type in [astroid.Name, astroid.AssignName]:
                if all(isinstance(_node, _type) for _node in [node_a, node_b]):
                    return node_a.name == node_b.name
            if all(isinstance(_node, astroid.Const) for _node in [node_a, node_b]):
                return node_a.value == node_b.value
            return False

        if_block_ok = (
            isinstance(node.test, astroid.Compare)
            and len(node.body) == 1
            and isinstance(node.body[0], astroid.Assign)
            and isinstance(node.body[0].value, astroid.Subscript)
            and type_and_name_are_equal(node.body[0].value.value, node.test.ops[0][1])
            and isinstance(node.body[0].value.slice, astroid.Index)
            and type_and_name_are_equal(node.body[0].value.slice.value, node.test.left)
            and len(node.body[0].targets) == 1
            and isinstance(node.body[0].targets[0], astroid.AssignName)
            and isinstance(utils.safe_infer(node.test.ops[0][1]), astroid.Dict)
        )

        if if_block_ok and not node.orelse:
            self.add_message("consider-using-get", node=node)
        elif (
            if_block_ok
            and len(node.orelse) == 1
            and isinstance(node.orelse[0], astroid.Assign)
            and type_and_name_are_equal(
                node.orelse[0].targets[0], node.body[0].targets[0]
            )
            and len(node.orelse[0].targets) == 1
        ):
            self.add_message("consider-using-get", node=node)

    @utils.check_messages(
        "too-many-nested-blocks",
        "simplifiable-if-statement",
        "no-else-return",
        "no-else-raise",
        "no-else-break",
        "no-else-continue",
        "consider-using-get",
    )
    def visit_if(self, node):
        self._check_simplifiable_if(node)
        self._check_nested_blocks(node)
        self._check_superfluous_else_return(node)
        self._check_superfluous_else_raise(node)
        self._check_superfluous_else_break(node)
        self._check_superfluous_else_continue(node)
        self._check_consider_get(node)

    @utils.check_messages("simplifiable-if-expression")
    def visit_ifexp(self, node):
        self._check_simplifiable_ifexp(node)

    def _check_simplifiable_ifexp(self, node):
        if not isinstance(node.body, astroid.Const) or not isinstance(
            node.orelse, astroid.Const
        ):
            return

        if not isinstance(node.body.value, bool) or not isinstance(
            node.orelse.value, bool
        ):
            return

        if isinstance(node.test, astroid.Compare):
            test_reduced_to = "test"
        else:
            test_reduced_to = "bool(test)"

        if (node.body.value, node.orelse.value) == (True, False):
            reduced_to = "'{}'".format(test_reduced_to)
        elif (node.body.value, node.orelse.value) == (False, True):
            reduced_to = "'not test'"
        else:
            return

        self.add_message("simplifiable-if-expression", node=node, args=(reduced_to,))

    @utils.check_messages(
        "too-many-nested-blocks", "inconsistent-return-statements", "useless-return"
    )
    def leave_functiondef(self, node):
        # check left-over nested blocks stack
        self._emit_nested_blocks_message_if_needed(self._nested_blocks)
        # new scope = reinitialize the stack of nested blocks
        self._nested_blocks = []
        #  check consistent return statements
        self._check_consistent_returns(node)
        # check for single return or return None at the end
        self._check_return_at_the_end(node)
        self._return_nodes[node.name] = []

    @utils.check_messages("stop-iteration-return")
    def visit_raise(self, node):
        self._check_stop_iteration_inside_generator(node)

    def _check_stop_iteration_inside_generator(self, node):
        """Check if an exception of type StopIteration is raised inside a generator"""
        frame = node.frame()
        if not isinstance(frame, astroid.FunctionDef) or not frame.is_generator():
            return
        if utils.node_ignores_exception(node, StopIteration):
            return
        if not node.exc:
            return
        exc = utils.safe_infer(node.exc)
        if exc is None or exc is astroid.Uninferable:
            return
        if self._check_exception_inherit_from_stopiteration(exc):
            self.add_message("stop-iteration-return", node=node)

    @staticmethod
    def _check_exception_inherit_from_stopiteration(exc):
        """Return True if the exception node in argument inherit from StopIteration"""
        stopiteration_qname = "{}.StopIteration".format(utils.EXCEPTIONS_MODULE)
        return any(_class.qname() == stopiteration_qname for _class in exc.mro())

    def _check_consider_using_comprehension_constructor(self, node):
        if (
            isinstance(node.func, astroid.Name)
            and node.args
            and isinstance(node.args[0], astroid.ListComp)
        ):
            if node.func.name == "dict" and not isinstance(
                node.args[0].elt, astroid.Call
            ):
                message_name = "consider-using-dict-comprehension"
                self.add_message(message_name, node=node)
            elif node.func.name == "set":
                message_name = "consider-using-set-comprehension"
                self.add_message(message_name, node=node)

    @utils.check_messages(
        "stop-iteration-return",
        "consider-using-dict-comprehension",
        "consider-using-set-comprehension",
        "consider-using-sys-exit",
    )
    def visit_call(self, node):
        self._check_raising_stopiteration_in_generator_next_call(node)
        self._check_consider_using_comprehension_constructor(node)
        self._check_quit_exit_call(node)

    @staticmethod
    def _has_exit_in_scope(scope):
        exit_func = scope.locals.get("exit")
        return bool(
            exit_func and isinstance(exit_func[0], (astroid.ImportFrom, astroid.Import))
        )

    def _check_quit_exit_call(self, node):

        if isinstance(node.func, astroid.Name) and node.func.name in BUILTIN_EXIT_FUNCS:
            # If we have `exit` imported from `sys` in the current or global scope, exempt this instance.
            local_scope = node.scope()
            if self._has_exit_in_scope(local_scope) or self._has_exit_in_scope(
                node.root()
            ):
                return
            self.add_message("consider-using-sys-exit", node=node)

    def _check_raising_stopiteration_in_generator_next_call(self, node):
        """Check if a StopIteration exception is raised by the call to next function

        If the next value has a default value, then do not add message.

        :param node: Check to see if this Call node is a next function
        :type node: :class:`astroid.node_classes.Call`
        """

        def _looks_like_infinite_iterator(param):
            inferred = utils.safe_infer(param)
            if inferred:
                return inferred.qname() in KNOWN_INFINITE_ITERATORS
            return False

        if isinstance(node.func, astroid.Attribute):
            # A next() method, which is now what we want.
            return

        inferred = utils.safe_infer(node.func)
        if getattr(inferred, "name", "") == "next":
            frame = node.frame()
            # The next builtin can only have up to two
            # positional arguments and no keyword arguments
            has_sentinel_value = len(node.args) > 1
            if (
                isinstance(frame, astroid.FunctionDef)
                and frame.is_generator()
                and not has_sentinel_value
                and not utils.node_ignores_exception(node, StopIteration)
                and not _looks_like_infinite_iterator(node.args[0])
            ):
                self.add_message("stop-iteration-return", node=node)

    def _check_nested_blocks(self, node):
        """Update and check the number of nested blocks
        """
        # only check block levels inside functions or methods
        if not isinstance(node.scope(), astroid.FunctionDef):
            return
        # messages are triggered on leaving the nested block. Here we save the
        # stack in case the current node isn't nested in the previous one
        nested_blocks = self._nested_blocks[:]
        if node.parent == node.scope():
            self._nested_blocks = [node]
        else:
            # go through ancestors from the most nested to the less
            for ancestor_node in reversed(self._nested_blocks):
                if ancestor_node == node.parent:
                    break
                self._nested_blocks.pop()
            # if the node is an elif, this should not be another nesting level
            if isinstance(node, astroid.If) and self._is_actual_elif(node):
                if self._nested_blocks:
                    self._nested_blocks.pop()
            self._nested_blocks.append(node)

        # send message only once per group of nested blocks
        if len(nested_blocks) > len(self._nested_blocks):
            self._emit_nested_blocks_message_if_needed(nested_blocks)

    def _emit_nested_blocks_message_if_needed(self, nested_blocks):
        if len(nested_blocks) > self.config.max_nested_blocks:
            self.add_message(
                "too-many-nested-blocks",
                node=nested_blocks[0],
                args=(len(nested_blocks), self.config.max_nested_blocks),
            )

    @staticmethod
    def _duplicated_isinstance_types(node):
        """Get the duplicated types from the underlying isinstance calls.

        :param astroid.BoolOp node: Node which should contain a bunch of isinstance calls.
        :returns: Dictionary of the comparison objects from the isinstance calls,
                  to duplicate values from consecutive calls.
        :rtype: dict
        """
        duplicated_objects = set()
        all_types = collections.defaultdict(set)

        for call in node.values:
            if not isinstance(call, astroid.Call) or len(call.args) != 2:
                continue

            inferred = utils.safe_infer(call.func)
            if not inferred or not utils.is_builtin_object(inferred):
                continue

            if inferred.name != "isinstance":
                continue

            isinstance_object = call.args[0].as_string()
            isinstance_types = call.args[1]

            if isinstance_object in all_types:
                duplicated_objects.add(isinstance_object)

            if isinstance(isinstance_types, astroid.Tuple):
                elems = [
                    class_type.as_string() for class_type in isinstance_types.itered()
                ]
            else:
                elems = [isinstance_types.as_string()]
            all_types[isinstance_object].update(elems)

        # Remove all keys which not duplicated
        return {
            key: value for key, value in all_types.items() if key in duplicated_objects
        }

    def _check_consider_merging_isinstance(self, node):
        """Check isinstance calls which can be merged together."""
        if node.op != "or":
            return

        first_args = self._duplicated_isinstance_types(node)
        for duplicated_name, class_names in first_args.items():
            names = sorted(name for name in class_names)
            self.add_message(
                "consider-merging-isinstance",
                node=node,
                args=(duplicated_name, ", ".join(names)),
            )

    def _check_consider_using_in(self, node):
        allowed_ops = {"or": "==", "and": "!="}

        if node.op not in allowed_ops or len(node.values) < 2:
            return

        for value in node.values:
            if (
                not isinstance(value, astroid.Compare)
                or len(value.ops) != 1
                or value.ops[0][0] not in allowed_ops[node.op]
            ):
                return
            for comparable in value.left, value.ops[0][1]:
                if isinstance(comparable, astroid.Call):
                    return

        # Gather variables and values from comparisons
        variables, values = [], []
        for value in node.values:
            variable_set = set()
            for comparable in value.left, value.ops[0][1]:
                if isinstance(comparable, astroid.Name):
                    variable_set.add(comparable.as_string())
                values.append(comparable.as_string())
            variables.append(variable_set)

        # Look for (common-)variables that occur in all comparisons
        common_variables = reduce(lambda a, b: a.intersection(b), variables)

        if not common_variables:
            return

        # Gather information for the suggestion
        common_variable = sorted(list(common_variables))[0]
        comprehension = "in" if node.op == "or" else "not in"
        values = list(collections.OrderedDict.fromkeys(values))
        values.remove(common_variable)
        values_string = ", ".join(values) if len(values) != 1 else values[0] + ","
        suggestion = "%s %s (%s)" % (common_variable, comprehension, values_string)

        self.add_message("consider-using-in", node=node, args=(suggestion,))

    def _check_chained_comparison(self, node):
        """Check if there is any chained comparison in the expression.

        Add a refactoring message if a boolOp contains comparison like a < b and b < c,
        which can be chained as a < b < c.

        Care is taken to avoid simplifying a < b < c and b < d.
        """
        if node.op != "and" or len(node.values) < 2:
            return

        def _find_lower_upper_bounds(comparison_node, uses):
            left_operand = comparison_node.left
            for operator, right_operand in comparison_node.ops:
                for operand in (left_operand, right_operand):
                    value = None
                    if isinstance(operand, astroid.Name):
                        value = operand.name
                    elif isinstance(operand, astroid.Const):
                        value = operand.value

                    if value is None:
                        continue

                    if operator in ("<", "<="):
                        if operand is left_operand:
                            uses[value]["lower_bound"].add(comparison_node)
                        elif operand is right_operand:
                            uses[value]["upper_bound"].add(comparison_node)
                    elif operator in (">", ">="):
                        if operand is left_operand:
                            uses[value]["upper_bound"].add(comparison_node)
                        elif operand is right_operand:
                            uses[value]["lower_bound"].add(comparison_node)
                left_operand = right_operand

        uses = collections.defaultdict(
            lambda: {"lower_bound": set(), "upper_bound": set()}
        )
        for comparison_node in node.values:
            if isinstance(comparison_node, astroid.Compare):
                _find_lower_upper_bounds(comparison_node, uses)

        for _, bounds in uses.items():
            num_shared = len(bounds["lower_bound"].intersection(bounds["upper_bound"]))
            num_lower_bounds = len(bounds["lower_bound"])
            num_upper_bounds = len(bounds["upper_bound"])
            if num_shared < num_lower_bounds and num_shared < num_upper_bounds:
                self.add_message("chained-comparison", node=node)
                break

    @utils.check_messages(
        "consider-merging-isinstance", "consider-using-in", "chained-comparison"
    )
    def visit_boolop(self, node):
        self._check_consider_merging_isinstance(node)
        self._check_consider_using_in(node)
        self._check_chained_comparison(node)

    @staticmethod
    def _is_simple_assignment(node):
        return (
            isinstance(node, astroid.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], astroid.node_classes.AssignName)
            and isinstance(node.value, astroid.node_classes.Name)
        )

    def _check_swap_variables(self, node):
        if not node.next_sibling() or not node.next_sibling().next_sibling():
            return
        assignments = [node, node.next_sibling(), node.next_sibling().next_sibling()]
        if not all(self._is_simple_assignment(node) for node in assignments):
            return
        if any(node in self._reported_swap_nodes for node in assignments):
            return
        left = [node.targets[0].name for node in assignments]
        right = [node.value.name for node in assignments]
        if left[0] == right[-1] and left[1:] == right[:-1]:
            self._reported_swap_nodes.update(assignments)
            message = "consider-swap-variables"
            self.add_message(message, node=node)

    @utils.check_messages(
        "simplify-boolean-expression",
        "consider-using-ternary",
        "consider-swap-variables",
    )
    def visit_assign(self, node):
        self._check_swap_variables(node)
        if self._is_and_or_ternary(node.value):
            cond, truth_value, false_value = self._and_or_ternary_arguments(node.value)
        else:
            return

        if all(
            isinstance(value, astroid.Compare) for value in (truth_value, false_value)
        ):
            return

        inferred_truth_value = utils.safe_infer(truth_value)
        if inferred_truth_value in (None, astroid.Uninferable):
            truth_boolean_value = True
        else:
            truth_boolean_value = truth_value.bool_value()

        if truth_boolean_value is False:
            message = "simplify-boolean-expression"
            suggestion = false_value.as_string()
        else:
            message = "consider-using-ternary"
            suggestion = "{truth} if {cond} else {false}".format(
                truth=truth_value.as_string(),
                cond=cond.as_string(),
                false=false_value.as_string(),
            )
        self.add_message(message, node=node, args=(suggestion,))

    visit_return = visit_assign

    def _check_consider_using_join(self, aug_assign):
        """
        We start with the augmented assignment and work our way upwards.
        Names of variables for nodes if match successful:
        result = ''  # assign
        for number in ['1', '2', '3']  # for_loop
            result += number  # aug_assign
        """
        for_loop = aug_assign.parent
        if not isinstance(for_loop, astroid.For) or len(for_loop.body) > 1:
            return
        assign = for_loop.previous_sibling()
        if not isinstance(assign, astroid.Assign):
            return
        result_assign_names = {
            target.name
            for target in assign.targets
            if isinstance(target, astroid.AssignName)
        }

        is_concat_loop = (
            aug_assign.op == "+="
            and isinstance(aug_assign.target, astroid.AssignName)
            and len(for_loop.body) == 1
            and aug_assign.target.name in result_assign_names
            and isinstance(assign.value, astroid.Const)
            and isinstance(assign.value.value, str)
            and isinstance(aug_assign.value, astroid.Name)
            and aug_assign.value.name == for_loop.target.name
        )
        if is_concat_loop:
            self.add_message("consider-using-join", node=aug_assign)

    @utils.check_messages("consider-using-join")
    def visit_augassign(self, node):
        self._check_consider_using_join(node)

    @utils.check_messages("unnecessary-comprehension")
    def visit_comprehension(self, node):
        self._check_unnecessary_comprehension(node)

    def _check_unnecessary_comprehension(self, node):
        if (
            isinstance(node.parent, astroid.GeneratorExp)
            or len(node.ifs) != 0
            or len(node.parent.generators) != 1
            or node.is_async
        ):
            return

        if (
            isinstance(node.parent, astroid.DictComp)
            and isinstance(node.parent.key, astroid.Name)
            and isinstance(node.parent.value, astroid.Name)
            and isinstance(node.target, astroid.Tuple)
            and all(isinstance(elt, astroid.AssignName) for elt in node.target.elts)
        ):
            expr_list = [node.parent.key.name, node.parent.value.name]
            target_list = [elt.name for elt in node.target.elts]

        elif isinstance(node.parent, (astroid.ListComp, astroid.SetComp)):
            expr = node.parent.elt
            if isinstance(expr, astroid.Name):
                expr_list = expr.name
            elif isinstance(expr, astroid.Tuple):
                if any(not isinstance(elt, astroid.Name) for elt in expr.elts):
                    return
                expr_list = [elt.name for elt in expr.elts]
            else:
                expr_list = []
            target = node.parent.generators[0].target
            target_list = (
                target.name
                if isinstance(target, astroid.AssignName)
                else (
                    [
                        elt.name
                        for elt in target.elts
                        if isinstance(elt, astroid.AssignName)
                    ]
                    if isinstance(target, astroid.Tuple)
                    else []
                )
            )
        else:
            return
        if expr_list == target_list != []:
            self.add_message("unnecessary-comprehension", node=node)

    @staticmethod
    def _is_and_or_ternary(node):
        """
        Returns true if node is 'condition and true_value or false_value' form.

        All of: condition, true_value and false_value should not be a complex boolean expression
        """
        return (
            isinstance(node, astroid.BoolOp)
            and node.op == "or"
            and len(node.values) == 2
            and isinstance(node.values[0], astroid.BoolOp)
            and not isinstance(node.values[1], astroid.BoolOp)
            and node.values[0].op == "and"
            and not isinstance(node.values[0].values[1], astroid.BoolOp)
            and len(node.values[0].values) == 2
        )

    @staticmethod
    def _and_or_ternary_arguments(node):
        false_value = node.values[1]
        condition, true_value = node.values[0].values
        return condition, true_value, false_value

    def visit_functiondef(self, node):
        self._return_nodes[node.name] = list(
            node.nodes_of_class(astroid.Return, skip_klass=astroid.FunctionDef)
        )

    def _check_consistent_returns(self, node):
        """Check that all return statements inside a function are consistent.

        Return statements are consistent if:
            - all returns are explicit and if there is no implicit return;
            - all returns are empty and if there is, possibly, an implicit return.

        Args:
            node (astroid.FunctionDef): the function holding the return statements.

        """
        # explicit return statements are those with a not None value
        explicit_returns = [
            _node for _node in self._return_nodes[node.name] if _node.value is not None
        ]
        if not explicit_returns:
            return
        if len(explicit_returns) == len(
            self._return_nodes[node.name]
        ) and self._is_node_return_ended(node):
            return
        self.add_message("inconsistent-return-statements", node=node)

    def _is_node_return_ended(self, node):
        """Check if the node ends with an explicit return statement.

        Args:
            node (astroid.NodeNG): node to be checked.

        Returns:
            bool: True if the node ends with an explicit statement, False otherwise.

        """
        #  Recursion base case
        if isinstance(node, astroid.Return):
            return True
        if isinstance(node, astroid.Call):
            try:
                funcdef_node = node.func.inferred()[0]
                if self._is_function_def_never_returning(funcdef_node):
                    return True
            except astroid.InferenceError:
                pass
        # Avoid the check inside while loop as we don't know
        #  if they will be completed
        if isinstance(node, astroid.While):
            return True
        if isinstance(node, astroid.Raise):
            # a Raise statement doesn't need to end with a return statement
            # but if the exception raised is handled, then the handler has to
            # ends with a return statement
            if not node.exc:
                # Ignore bare raises
                return True
            if not utils.is_node_inside_try_except(node):
                # If the raise statement is not inside a try/except statement
                #  then the exception is raised and cannot be caught. No need
                #  to infer it.
                return True
            exc = utils.safe_infer(node.exc)
            if exc is None or exc is astroid.Uninferable:
                return False
            exc_name = exc.pytype().split(".")[-1]
            handlers = utils.get_exception_handlers(node, exc_name)
            handlers = list(handlers) if handlers is not None else []
            if handlers:
                # among all the handlers handling the exception at least one
                # must end with a return statement
                return any(
                    self._is_node_return_ended(_handler) for _handler in handlers
                )
            # if no handlers handle the exception then it's ok
            return True
        if isinstance(node, astroid.If):
            # if statement is returning if there are exactly two return statements in its
            #  children : one for the body part, the other for the orelse part
            # Do not check if inner function definition are return ended.
            is_orelse_returning = any(
                self._is_node_return_ended(_ore)
                for _ore in node.orelse
                if not isinstance(_ore, astroid.FunctionDef)
            )
            is_if_returning = any(
                self._is_node_return_ended(_ifn)
                for _ifn in node.body
                if not isinstance(_ifn, astroid.FunctionDef)
            )
            return is_if_returning and is_orelse_returning
        #  recurses on the children of the node except for those which are except handler
        # because one cannot be sure that the handler will really be used
        return any(
            self._is_node_return_ended(_child)
            for _child in node.get_children()
            if not isinstance(_child, astroid.ExceptHandler)
        )

    def _is_function_def_never_returning(self, node):
        """Return True if the function never returns. False otherwise.

        Args:
            node (astroid.FunctionDef): function definition node to be analyzed.

        Returns:
            bool: True if the function never returns, False otherwise.
        """
        try:
            return node.qname() in self._never_returning_functions
        except TypeError:
            return False

    def _check_return_at_the_end(self, node):
        """Check for presence of a *single* return statement at the end of a
        function. "return" or "return None" are useless because None is the
        default return type if they are missing.

        NOTE: produces a message only if there is a single return statement
        in the function body. Otherwise _check_consistent_returns() is called!
        Per its implementation and PEP8 we can have a "return None" at the end
        of the function body if there are other return statements before that!
        """
        if len(self._return_nodes[node.name]) > 1:
            return
        if len(node.body) <= 1:
            return

        last = node.body[-1]
        if isinstance(last, astroid.Return):
            # e.g. "return"
            if last.value is None:
                self.add_message("useless-return", node=node)
            # return None"
            elif isinstance(last.value, astroid.Const) and (last.value.value is None):
                self.add_message("useless-return", node=node)


class RecommandationChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)
    name = "refactoring"
    msgs = {
        "C0200": (
            "Consider using enumerate instead of iterating with range and len",
            "consider-using-enumerate",
            "Emitted when code that iterates with range and len is "
            "encountered. Such code can be simplified by using the "
            "enumerate builtin.",
        ),
        "C0201": (
            "Consider iterating the dictionary directly instead of calling .keys()",
            "consider-iterating-dictionary",
            "Emitted when the keys of a dictionary are iterated through the .keys() "
            "method. It is enough to just iterate through the dictionary itself, as "
            'in "for key in dictionary".',
        ),
    }

    @staticmethod
    def _is_builtin(node, function):
        inferred = utils.safe_infer(node)
        if not inferred:
            return False
        return utils.is_builtin_object(inferred) and inferred.name == function

    @utils.check_messages("consider-iterating-dictionary")
    def visit_call(self, node):
        if not isinstance(node.func, astroid.Attribute):
            return
        if node.func.attrname != "keys":
            return
        if not isinstance(node.parent, (astroid.For, astroid.Comprehension)):
            return

        inferred = utils.safe_infer(node.func)
        if not isinstance(inferred, astroid.BoundMethod) or not isinstance(
            inferred.bound, astroid.Dict
        ):
            return

        if isinstance(node.parent, (astroid.For, astroid.Comprehension)):
            self.add_message("consider-iterating-dictionary", node=node)

    @utils.check_messages("consider-using-enumerate")
    def visit_for(self, node):
        """Emit a convention whenever range and len are used for indexing."""
        # Verify that we have a `range([start], len(...), [stop])` call and
        # that the object which is iterated is used as a subscript in the
        # body of the for.

        # Is it a proper range call?
        if not isinstance(node.iter, astroid.Call):
            return
        if not self._is_builtin(node.iter.func, "range"):
            return
        if len(node.iter.args) == 2 and not _is_constant_zero(node.iter.args[0]):
            return
        if len(node.iter.args) > 2:
            return

        # Is it a proper len call?
        if not isinstance(node.iter.args[-1], astroid.Call):
            return
        second_func = node.iter.args[-1].func
        if not self._is_builtin(second_func, "len"):
            return
        len_args = node.iter.args[-1].args
        if not len_args or len(len_args) != 1:
            return
        iterating_object = len_args[0]
        if not isinstance(iterating_object, astroid.Name):
            return
        # If we're defining __iter__ on self, enumerate won't work
        scope = node.scope()
        if iterating_object.name == "self" and scope.name == "__iter__":
            return

        # Verify that the body of the for loop uses a subscript
        # with the object that was iterated. This uses some heuristics
        # in order to make sure that the same object is used in the
        # for body.
        for child in node.body:
            for subscript in child.nodes_of_class(astroid.Subscript):
                if not isinstance(subscript.value, astroid.Name):
                    continue
                if not isinstance(subscript.slice, astroid.Index):
                    continue
                if not isinstance(subscript.slice.value, astroid.Name):
                    continue
                if subscript.slice.value.name != node.target.name:
                    continue
                if iterating_object.name != subscript.value.name:
                    continue
                if subscript.value.scope() != node.scope():
                    # Ignore this subscript if it's not in the same
                    # scope. This means that in the body of the for
                    # loop, another scope was created, where the same
                    # name for the iterating object was used.
                    continue
                self.add_message("consider-using-enumerate", node=node)
                return


class NotChecker(checkers.BaseChecker):
    """checks for too many not in comparison expressions

    - "not not" should trigger a warning
    - "not" followed by a comparison should trigger a warning
    """

    __implements__ = (interfaces.IAstroidChecker,)
    msgs = {
        "C0113": (
            'Consider changing "%s" to "%s"',
            "unneeded-not",
            "Used when a boolean expression contains an unneeded negation.",
        )
    }
    name = "refactoring"
    reverse_op = {
        "<": ">=",
        "<=": ">",
        ">": "<=",
        ">=": "<",
        "==": "!=",
        "!=": "==",
        "in": "not in",
        "is": "is not",
    }
    # sets are not ordered, so for example "not set(LEFT_VALS) <= set(RIGHT_VALS)" is
    # not equivalent to "set(LEFT_VALS) > set(RIGHT_VALS)"
    skipped_nodes = (astroid.Set,)
    # 'builtins' py3, '__builtin__' py2
    skipped_classnames = [
        "%s.%s" % (builtins.__name__, qname) for qname in ("set", "frozenset")
    ]

    @utils.check_messages("unneeded-not")
    def visit_unaryop(self, node):
        if node.op != "not":
            return
        operand = node.operand

        if isinstance(operand, astroid.UnaryOp) and operand.op == "not":
            self.add_message(
                "unneeded-not",
                node=node,
                args=(node.as_string(), operand.operand.as_string()),
            )
        elif isinstance(operand, astroid.Compare):
            left = operand.left
            # ignore multiple comparisons
            if len(operand.ops) > 1:
                return
            operator, right = operand.ops[0]
            if operator not in self.reverse_op:
                return
            # Ignore __ne__ as function of __eq__
            frame = node.frame()
            if frame.name == "__ne__" and operator == "==":
                return
            for _type in (utils.node_type(left), utils.node_type(right)):
                if not _type:
                    return
                if isinstance(_type, self.skipped_nodes):
                    return
                if (
                    isinstance(_type, astroid.Instance)
                    and _type.qname() in self.skipped_classnames
                ):
                    return
            suggestion = "%s %s %s" % (
                left.as_string(),
                self.reverse_op[operator],
                right.as_string(),
            )
            self.add_message(
                "unneeded-not", node=node, args=(node.as_string(), suggestion)
            )


class LenChecker(checkers.BaseChecker):
    """Checks for incorrect usage of len() inside conditions.
    Pep8 states:
    For sequences, (strings, lists, tuples), use the fact that empty sequences are false.

        Yes: if not seq:
             if seq:

        No: if len(seq):
            if not len(seq):

    Problems detected:
    * if len(sequence):
    * if not len(sequence):
    * elif len(sequence):
    * elif not len(sequence):
    * while len(sequence):
    * while not len(sequence):
    * assert len(sequence):
    * assert not len(sequence):
    """

    __implements__ = (interfaces.IAstroidChecker,)

    # configuration section name
    name = "refactoring"
    msgs = {
        "C1801": (
            "Do not use `len(SEQUENCE)` without comparison to determine if a sequence is empty",
            "len-as-condition",
            "Used when Pylint detects that len(sequence) is being used "
            "without explicit comparison inside a condition to determine if a sequence is empty. "
            "Instead of coercing the length to a boolean, either "
            "rely on the fact that empty sequences are false or "
            "compare the length against a scalar.",
        )
    }

    priority = -2
    options = ()

    @utils.check_messages("len-as-condition")
    def visit_call(self, node):
        # a len(S) call is used inside a test condition
        # could be if, while, assert or if expression statement
        # e.g. `if len(S):`
        if _is_len_call(node):
            # the len() call could also be nested together with other
            # boolean operations, e.g. `if z or len(x):`
            parent = node.parent
            while isinstance(parent, astroid.BoolOp):
                parent = parent.parent

            # we're finally out of any nested boolean operations so check if
            # this len() call is part of a test condition
            if not _node_is_test_condition(parent):
                return
            if not (node is parent.test or parent.test.parent_of(node)):
                return
            self.add_message("len-as-condition", node=node)

    @utils.check_messages("len-as-condition")
    def visit_unaryop(self, node):
        """`not len(S)` must become `not S` regardless if the parent block
        is a test condition or something else (boolean expression)
        e.g. `if not len(S):`"""
        if (
            isinstance(node, astroid.UnaryOp)
            and node.op == "not"
            and _is_len_call(node.operand)
        ):
            self.add_message("len-as-condition", node=node)


def register(linter):
    """Required method to auto register this checker."""
    linter.register_checker(RefactoringChecker(linter))
    linter.register_checker(NotChecker(linter))
    linter.register_checker(RecommandationChecker(linter))
    linter.register_checker(LenChecker(linter))
