# -*- coding: utf-8 -*-

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING


import collections

from pylint.constants import MSG_TYPES

_MsgBase = collections.namedtuple(
    "_MsgBase",
    [
        "msg_id",
        "symbol",
        "msg",
        "C",
        "category",
        "confidence",
        "abspath",
        "path",
        "module",
        "obj",
        "line",
        "column",
    ],
)


class Message(_MsgBase):
    """This class represent a message to be issued by the reporters"""

    def __new__(cls, msg_id, symbol, location, msg, confidence):
        return _MsgBase.__new__(
            cls,
            msg_id,
            symbol,
            msg,
            msg_id[0],
            MSG_TYPES[msg_id[0]],
            confidence,
            *location
        )

    def format(self, template):
        """Format the message according to the given template.

        The template format is the one of the format method :
        cf. http://docs.python.org/2/library/string.html#formatstrings
        """
        # For some reason, _asdict on derived namedtuples does not work with
        # Python 3.4. Needs some investigation.
        return template.format(**dict(zip(self._fields, self)))
