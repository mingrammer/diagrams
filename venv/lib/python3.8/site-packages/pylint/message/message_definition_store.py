# -*- coding: utf-8 -*-

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import collections

from pylint.exceptions import UnknownMessageError
from pylint.message.message_id_store import MessageIdStore


class MessageDefinitionStore:

    """The messages store knows information about every possible message definition but has
    no particular state during analysis.
    """

    def __init__(self):
        self.message_id_store = MessageIdStore()
        # Primary registry for all active messages definitions.
        # It contains the 1:1 mapping from msgid to MessageDefinition.
        # Keys are msgid, values are MessageDefinition
        self._messages_definitions = {}
        # MessageDefinition kept by category
        self._msgs_by_category = collections.defaultdict(list)

    @property
    def messages(self) -> list:
        """The list of all active messages."""
        return self._messages_definitions.values()

    def register_messages_from_checker(self, checker):
        """Register all messages definitions from a checker.

        :param BaseChecker checker:
        """
        checker.check_consistency()
        for message in checker.messages:
            self.register_message(message)

    def register_message(self, message):
        """Register a MessageDefinition with consistency in mind.

        :param MessageDefinition message: The message definition being added.
        """
        self.message_id_store.register_message_definition(message)
        self._messages_definitions[message.msgid] = message
        self._msgs_by_category[message.msgid[0]].append(message.msgid)

    def get_message_definitions(self, msgid_or_symbol: str) -> list:
        """Returns the Message object for this message.
        :param str msgid_or_symbol: msgid_or_symbol may be either a numeric or symbolic id.
        :raises UnknownMessageError: if the message id is not defined.
        :rtype: List of MessageDefinition
        :return: A message definition corresponding to msgid_or_symbol
        """
        return [
            self._messages_definitions[m]
            for m in self.message_id_store.get_active_msgids(msgid_or_symbol)
        ]

    def get_msg_display_string(self, msgid_or_symbol: str):
        """Generates a user-consumable representation of a message. """
        message_definitions = self.get_message_definitions(msgid_or_symbol)
        if len(message_definitions) == 1:
            return repr(message_definitions[0].symbol)
        return repr([md.symbol for md in message_definitions])

    def help_message(self, msgids_or_symbols: list):
        """Display help messages for the given message identifiers"""
        for msgids_or_symbol in msgids_or_symbols:
            try:
                for message_definition in self.get_message_definitions(
                    msgids_or_symbol
                ):
                    print(message_definition.format_help(checkerref=True))
                    print("")
            except UnknownMessageError as ex:
                print(ex)
                print("")
                continue

    def list_messages(self):
        """Output full messages list documentation in ReST format. """
        messages = sorted(self._messages_definitions.values(), key=lambda m: m.msgid)
        for message in messages:
            if not message.may_be_emitted():
                continue
            print(message.format_help(checkerref=False))
        print("")
