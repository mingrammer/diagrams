# Copyright (c) 2014 Vlad Temian <vladtemian@gmail.com>
# Copyright (c) 2015-2017 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2017 guillaume2 <guillaume.peillex@gmail.col>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""JSON reporter"""
import html
import json
import sys

from pylint.interfaces import IReporter
from pylint.reporters.base_reporter import BaseReporter


class JSONReporter(BaseReporter):
    """Report messages and layouts in JSON."""

    __implements__ = IReporter
    name = "json"
    extension = "json"

    def __init__(self, output=sys.stdout):
        BaseReporter.__init__(self, output)
        self.messages = []

    def handle_message(self, msg):
        """Manage message of different type and in the context of path."""
        self.messages.append(
            {
                "type": msg.category,
                "module": msg.module,
                "obj": msg.obj,
                "line": msg.line,
                "column": msg.column,
                "path": msg.path,
                "symbol": msg.symbol,
                "message": html.escape(msg.msg or "", quote=False),
                "message-id": msg.msg_id,
            }
        )

    def display_messages(self, layout):
        """Launch layouts display"""
        print(json.dumps(self.messages, indent=4), file=self.out)

    def display_reports(self, layout):
        """Don't do nothing in this reporter."""

    def _display(self, layout):
        """Do nothing."""


def register(linter):
    """Register the reporter classes with the linter."""
    linter.register_reporter(JSONReporter)
