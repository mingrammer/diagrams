# -*- coding: utf-8 -*-

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import collections

from astroid import nodes


class ASTWalker:
    def __init__(self, linter):
        # callbacks per node types
        self.nbstatements = 0
        self.visit_events = collections.defaultdict(list)
        self.leave_events = collections.defaultdict(list)
        self.linter = linter

    def _is_method_enabled(self, method):
        if not hasattr(method, "checks_msgs"):
            return True
        for msg_desc in method.checks_msgs:
            if self.linter.is_message_enabled(msg_desc):
                return True
        return False

    def add_checker(self, checker):
        """walk to the checker's dir and collect visit and leave methods"""
        vcids = set()
        lcids = set()
        visits = self.visit_events
        leaves = self.leave_events
        for member in dir(checker):
            cid = member[6:]
            if cid == "default":
                continue
            if member.startswith("visit_"):
                v_meth = getattr(checker, member)
                # don't use visit_methods with no activated message:
                if self._is_method_enabled(v_meth):
                    visits[cid].append(v_meth)
                    vcids.add(cid)
            elif member.startswith("leave_"):
                l_meth = getattr(checker, member)
                # don't use leave_methods with no activated message:
                if self._is_method_enabled(l_meth):
                    leaves[cid].append(l_meth)
                    lcids.add(cid)
        visit_default = getattr(checker, "visit_default", None)
        if visit_default:
            for cls in nodes.ALL_NODE_CLASSES:
                cid = cls.__name__.lower()
                if cid not in vcids:
                    visits[cid].append(visit_default)
        # for now we have no "leave_default" method in Pylint

    def walk(self, astroid):
        """call visit events of astroid checkers for the given node, recurse on
        its children, then leave events.
        """
        cid = astroid.__class__.__name__.lower()

        # Detect if the node is a new name for a deprecated alias.
        # In this case, favour the methods for the deprecated
        # alias if any,  in order to maintain backwards
        # compatibility.
        visit_events = self.visit_events.get(cid, ())
        leave_events = self.leave_events.get(cid, ())

        if astroid.is_statement:
            self.nbstatements += 1
        # generate events for this node on each checker
        for callback in visit_events or ():
            callback(astroid)
        # recurse on children
        for child in astroid.get_children():
            self.walk(child)
        for callback in leave_events or ():
            callback(astroid)
