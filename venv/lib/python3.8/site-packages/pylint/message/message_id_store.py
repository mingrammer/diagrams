# -*- coding: utf-8 -*-

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from typing import List

from pylint.exceptions import InvalidMessageError, UnknownMessageError


class MessageIdStore:

    """The MessageIdStore store MessageId and make sure that there is a 1-1 relation between msgid and symbol."""

    def __init__(self):
        self.__msgid_to_symbol = {}
        self.__symbol_to_msgid = {}
        self.__old_names = {}

    def __len__(self):
        return len(self.__msgid_to_symbol)

    def __repr__(self):
        result = "MessageIdStore: [\n"
        for msgid, symbol in self.__msgid_to_symbol.items():
            result += "  - {msgid} ({symbol})\n".format(msgid=msgid, symbol=symbol)
        result += "]"
        return result

    def get_symbol(self, msgid: str) -> str:
        return self.__msgid_to_symbol[msgid]

    def get_msgid(self, symbol: str) -> str:
        return self.__symbol_to_msgid[symbol]

    def register_message_definition(self, message_definition):
        self.check_msgid_and_symbol(message_definition.msgid, message_definition.symbol)
        self.add_msgid_and_symbol(message_definition.msgid, message_definition.symbol)
        for old_msgid, old_symbol in message_definition.old_names:
            self.check_msgid_and_symbol(old_msgid, old_symbol)
            self.add_legacy_msgid_and_symbol(
                old_msgid, old_symbol, message_definition.msgid
            )

    def add_msgid_and_symbol(self, msgid: str, symbol: str) -> None:
        """Add valid message id.

        There is a little duplication with add_legacy_msgid_and_symbol to avoid a function call,
        this is called a lot at initialization."""
        self.__msgid_to_symbol[msgid] = symbol
        self.__symbol_to_msgid[symbol] = msgid

    def add_legacy_msgid_and_symbol(self, msgid: str, symbol: str, new_msgid: str):
        """Add valid legacy message id.

        There is a little duplication with add_msgid_and_symbol to avoid a function call,
        this is called a lot at initialization."""
        self.__msgid_to_symbol[msgid] = symbol
        self.__symbol_to_msgid[symbol] = msgid
        existing_old_names = self.__old_names.get(msgid, [])
        existing_old_names.append(new_msgid)
        self.__old_names[msgid] = existing_old_names

    def check_msgid_and_symbol(self, msgid: str, symbol: str) -> None:
        existing_msgid = self.__symbol_to_msgid.get(symbol)
        existing_symbol = self.__msgid_to_symbol.get(msgid)
        if existing_symbol is None and existing_msgid is None:
            return
        if existing_msgid is not None:
            if existing_msgid != msgid:
                self._raise_duplicate_msgid(symbol, msgid, existing_msgid)
        if existing_symbol != symbol:
            self._raise_duplicate_symbol(msgid, symbol, existing_symbol)

    @staticmethod
    def _raise_duplicate_symbol(msgid, symbol, other_symbol):
        """Raise an error when a symbol is duplicated.

        :param str msgid: The msgid corresponding to the symbols
        :param str symbol: Offending symbol
        :param str other_symbol: Other offending symbol
        :raises InvalidMessageError:"""
        symbols = [symbol, other_symbol]
        symbols.sort()
        error_message = "Message id '{msgid}' cannot have both ".format(msgid=msgid)
        error_message += "'{other_symbol}' and '{symbol}' as symbolic name.".format(
            other_symbol=symbols[0], symbol=symbols[1]
        )
        raise InvalidMessageError(error_message)

    @staticmethod
    def _raise_duplicate_msgid(symbol, msgid, other_msgid):
        """Raise an error when a msgid is duplicated.

        :param str symbol: The symbol corresponding to the msgids
        :param str msgid: Offending msgid
        :param str other_msgid: Other offending msgid
        :raises InvalidMessageError:"""
        msgids = [msgid, other_msgid]
        msgids.sort()
        error_message = (
            "Message symbol '{symbol}' cannot be used for "
            "'{other_msgid}' and '{msgid}' at the same time."
            " If you're creating an 'old_names' use 'old-{symbol}' as the old symbol."
        ).format(symbol=symbol, other_msgid=msgids[0], msgid=msgids[1])
        raise InvalidMessageError(error_message)

    def get_active_msgids(self, msgid_or_symbol: str) -> List[str]:
        """Return msgids but the input can be a symbol."""
        # Only msgid can have a digit as second letter
        is_msgid = msgid_or_symbol[1:].isdigit()
        if is_msgid:
            msgid = msgid_or_symbol.upper()
            symbol = self.__msgid_to_symbol.get(msgid)
        else:
            msgid = self.__symbol_to_msgid.get(msgid_or_symbol)
            symbol = msgid_or_symbol
        if not msgid or not symbol:
            error_msg = "No such message id or symbol '{msgid_or_symbol}'.".format(
                msgid_or_symbol=msgid_or_symbol
            )
            raise UnknownMessageError(error_msg)
        # logging.debug(
        #    "Return for {} and msgid {} is {}".format(
        #        msgid_or_symbol, msgid, self.__old_names.get(msgid, [msgid])
        #    )
        # )
        return self.__old_names.get(msgid, [msgid])
