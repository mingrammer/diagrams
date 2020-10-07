# -*- coding: utf-8 -*-
# Copyright (c) 2019 Tyler N. Thieding <python@thieding.com>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""Looks for try/except statements with too much code in the try clause."""

from pylint import checkers, interfaces


class BroadTryClauseChecker(checkers.BaseChecker):
    """Checks for try clauses with too many lines.

    According to PEP 8, ``try`` clauses shall contain the absolute minimum
    amount of code. This checker enforces a maximum number of statements within
    ``try`` clauses.

    """

    __implements__ = interfaces.IAstroidChecker

    # configuration section name
    name = "broad_try_clause"
    msgs = {
        "W0717": (
            "%s",
            "too-many-try-statements",
            "Try clause contains too many statements.",
        )
    }

    priority = -2
    options = (
        (
            "max-try-statements",
            {
                "default": 1,
                "type": "int",
                "metavar": "<int>",
                "help": "Maximum number of statements allowed in a try clause",
            },
        ),
    )

    def visit_tryexcept(self, node):
        try_clause_statements = len(node.body)
        if try_clause_statements > self.config.max_try_statements:
            msg = "try clause contains {0} statements, expected at most {1}".format(
                try_clause_statements, self.config.max_try_statements
            )
            self.add_message(
                "too-many-try-statements", node.lineno, node=node, args=msg
            )


def register(linter):
    """Required method to auto register this checker."""
    linter.register_checker(BroadTryClauseChecker(linter))
