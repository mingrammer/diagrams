# Copyright (c) 2006-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2013-2014 Google, Inc.
# Copyright (c) 2013 buck@yelp.com <buck@yelp.com>
# Copyright (c) 2014-2017 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Brett Cannon <brett@python.org>
# Copyright (c) 2014 Arun Persaud <arun@nubati.net>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2016 Moises Lopez <moylop260@vauxoo.com>
# Copyright (c) 2017-2018 Bryce Guinta <bryce.paul.guinta@gmail.com>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from inspect import cleandoc
from typing import Any

from pylint.config import OptionsProviderMixIn
from pylint.constants import _MSG_ORDER, WarningScope
from pylint.exceptions import InvalidMessageError
from pylint.interfaces import UNDEFINED, IRawChecker, ITokenChecker, implements
from pylint.message.message_definition import MessageDefinition
from pylint.utils import get_rst_section, get_rst_title


class BaseChecker(OptionsProviderMixIn):

    # checker name (you may reuse an existing one)
    name = None  # type: str
    # options level (0 will be displaying in --help, 1 in --long-help)
    level = 1
    # ordered list of options to control the checker behaviour
    options = ()  # type: Any
    # messages issued by this checker
    msgs = {}  # type: Any
    # reports issued by this checker
    reports = ()  # type: Any
    # mark this checker as enabled or not.
    enabled = True

    def __init__(self, linter=None):
        """checker instances should have the linter as argument

        :param ILinter linter: is an object implementing ILinter."""
        if self.name is not None:
            self.name = self.name.lower()
        OptionsProviderMixIn.__init__(self)
        self.linter = linter

    def __gt__(self, other):
        """Permit to sort a list of Checker by name."""
        return "{}{}".format(self.name, self.msgs).__gt__(
            "{}{}".format(other.name, other.msgs)
        )

    def __repr__(self):
        status = "Checker" if self.enabled else "Disabled checker"
        return "{} '{}' (responsible for '{}')".format(
            status, self.name, "', '".join(self.msgs.keys())
        )

    def __str__(self):
        """This might be incomplete because multiple class inheriting BaseChecker
        can have the same name. Cf MessageHandlerMixIn.get_full_documentation()"""
        return self.get_full_documentation(
            msgs=self.msgs, options=self.options_and_values(), reports=self.reports
        )

    def get_full_documentation(self, msgs, options, reports, doc=None, module=None):
        result = ""
        checker_title = "%s checker" % (self.name.replace("_", " ").title())
        if module:
            # Provide anchor to link against
            result += ".. _%s:\n\n" % module
        result += "%s\n" % get_rst_title(checker_title, "~")
        if module:
            result += "This checker is provided by ``%s``.\n" % module
        result += "Verbatim name of the checker is ``%s``.\n\n" % self.name
        if doc:
            # Provide anchor to link against
            result += get_rst_title("{} Documentation".format(checker_title), "^")
            result += "%s\n\n" % cleandoc(doc)
        # options might be an empty generator and not be False when casted to boolean
        options = list(options)
        if options:
            result += get_rst_title("{} Options".format(checker_title), "^")
            result += "%s\n" % get_rst_section(None, options)
        if msgs:
            result += get_rst_title("{} Messages".format(checker_title), "^")
            for msgid, msg in sorted(
                msgs.items(), key=lambda kv: (_MSG_ORDER.index(kv[0][0]), kv[1])
            ):
                msg = self.create_message_definition_from_tuple(msgid, msg)
                result += "%s\n" % msg.format_help(checkerref=False)
            result += "\n"
        if reports:
            result += get_rst_title("{} Reports".format(checker_title), "^")
            for report in reports:
                result += ":%s: %s\n" % report[:2]
            result += "\n"
        result += "\n"
        return result

    def add_message(
        self, msgid, line=None, node=None, args=None, confidence=None, col_offset=None
    ):
        if not confidence:
            confidence = UNDEFINED
        self.linter.add_message(msgid, line, node, args, confidence, col_offset)

    def check_consistency(self):
        """Check the consistency of msgid.

        msg ids for a checker should be a string of len 4, where the two first
        characters are the checker id and the two last the msg id in this
        checker.

        :raises InvalidMessageError: If the checker id in the messages are not
        always the same. """
        checker_id = None
        existing_ids = []
        for message in self.messages:
            if checker_id is not None and checker_id != message.msgid[1:3]:
                error_msg = "Inconsistent checker part in message id "
                error_msg += "'{}' (expected 'x{checker_id}xx' ".format(
                    message.msgid, checker_id=checker_id
                )
                error_msg += "because we already had {existing_ids}).".format(
                    existing_ids=existing_ids
                )
                raise InvalidMessageError(error_msg)
            checker_id = message.msgid[1:3]
            existing_ids.append(message.msgid)

    def create_message_definition_from_tuple(self, msgid, msg_tuple):
        if implements(self, (IRawChecker, ITokenChecker)):
            default_scope = WarningScope.LINE
        else:
            default_scope = WarningScope.NODE
        options = {}
        if len(msg_tuple) > 3:
            (msg, symbol, descr, options) = msg_tuple
        elif len(msg_tuple) > 2:
            (msg, symbol, descr) = msg_tuple
        else:
            error_msg = """Messages should have a msgid and a symbol. Something like this :

"W1234": (
    "message",
    "message-symbol",
    "Message description with detail.",
    ...
),
"""
            raise InvalidMessageError(error_msg)
        options.setdefault("scope", default_scope)
        return MessageDefinition(self, msgid, msg, descr, symbol, **options)

    @property
    def messages(self) -> list:
        return [
            self.create_message_definition_from_tuple(msgid, msg_tuple)
            for msgid, msg_tuple in sorted(self.msgs.items())
        ]

    # dummy methods implementing the IChecker interface

    def get_message_definition(self, msgid):
        for message_definition in self.messages:
            if message_definition.msgid == msgid:
                return message_definition
        error_msg = "MessageDefinition for '{}' does not exists. ".format(msgid)
        error_msg += "Choose from {}.".format([m.msgid for m in self.messages])
        raise InvalidMessageError(error_msg)

    def open(self):
        """called before visiting project (i.e set of modules)"""

    def close(self):
        """called after visiting project (i.e set of modules)"""


class BaseTokenChecker(BaseChecker):
    """Base class for checkers that want to have access to the token stream."""

    def process_tokens(self, tokens):
        """Should be overridden by subclasses."""
        raise NotImplementedError()
