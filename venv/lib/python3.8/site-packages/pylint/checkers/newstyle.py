# Copyright (c) 2006, 2008-2011, 2013-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2012-2014 Google, Inc.
# Copyright (c) 2013-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Michal Nowikowski <godfryd@gmail.com>
# Copyright (c) 2014 Brett Cannon <brett@python.org>
# Copyright (c) 2014 Arun Persaud <arun@nubati.net>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2016 Alexander Todorov <atodorov@otb.bg>
# Copyright (c) 2016 Jakub Wilk <jwilk@jwilk.net>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""check for new / old style related problems
"""
import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages, has_known_bases, node_frame_class
from pylint.interfaces import IAstroidChecker

MSGS = {
    "E1003": (
        "Bad first argument %r given to super()",
        "bad-super-call",
        "Used when another argument than the current class is given as "
        "first argument of the super builtin.",
    )
}


class NewStyleConflictChecker(BaseChecker):
    """checks for usage of new style capabilities on old style classes and
    other new/old styles conflicts problems
    * use of property, __slots__, super
    * "super" usage
    """

    __implements__ = (IAstroidChecker,)

    # configuration section name
    name = "newstyle"
    # messages
    msgs = MSGS
    priority = -2
    # configuration options
    options = ()

    @check_messages("bad-super-call")
    def visit_functiondef(self, node):
        """check use of super"""
        # ignore actual functions or method within a new style class
        if not node.is_method():
            return
        klass = node.parent.frame()
        for stmt in node.nodes_of_class(astroid.Call):
            if node_frame_class(stmt) != node_frame_class(node):
                # Don't look down in other scopes.
                continue

            expr = stmt.func
            if not isinstance(expr, astroid.Attribute):
                continue

            call = expr.expr
            # skip the test if using super
            if not (
                isinstance(call, astroid.Call)
                and isinstance(call.func, astroid.Name)
                and call.func.name == "super"
            ):
                continue

            # super should not be used on an old style class
            if klass.newstyle or not has_known_bases(klass):
                # super first arg should not be the class
                if not call.args:
                    continue

                # calling super(type(self), self) can lead to recursion loop
                # in derived classes
                arg0 = call.args[0]
                if (
                    isinstance(arg0, astroid.Call)
                    and isinstance(arg0.func, astroid.Name)
                    and arg0.func.name == "type"
                ):
                    self.add_message("bad-super-call", node=call, args=("type",))
                    continue

                # calling super(self.__class__, self) can lead to recursion loop
                # in derived classes
                if (
                    len(call.args) >= 2
                    and isinstance(call.args[1], astroid.Name)
                    and call.args[1].name == "self"
                    and isinstance(arg0, astroid.Attribute)
                    and arg0.attrname == "__class__"
                ):
                    self.add_message(
                        "bad-super-call", node=call, args=("self.__class__",)
                    )
                    continue

                try:
                    supcls = call.args and next(call.args[0].infer(), None)
                except astroid.InferenceError:
                    continue

                if klass is not supcls:
                    name = None
                    # if supcls is not Uninferable, then supcls was inferred
                    # and use its name. Otherwise, try to look
                    # for call.args[0].name
                    if supcls:
                        name = supcls.name
                    elif call.args and hasattr(call.args[0], "name"):
                        name = call.args[0].name
                    if name:
                        self.add_message("bad-super-call", node=call, args=(name,))

    visit_asyncfunctiondef = visit_functiondef


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(NewStyleConflictChecker(linter))
