# -*- coding: utf-8 -*-
# Copyright (c) 2006, 2009-2013 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2012-2014 Google, Inc.
# Copyright (c) 2014-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Brett Cannon <brett@python.org>
# Copyright (c) 2014 Alexandru Coman <fcoman@bitdefender.com>
# Copyright (c) 2014 Arun Persaud <arun@nubati.net>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2016 Łukasz Rogalski <rogalski.91@gmail.com>
# Copyright (c) 2016 glegoux <gilles.legoux@gmail.com>
# Copyright (c) 2017-2018 hippo91 <guillaume.peillex@gmail.com>
# Copyright (c) 2017 Mikhail Fesenko <proggga@gmail.com>
# Copyright (c) 2018 Ville Skyttä <ville.skytta@iki.fi>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING


"""Check source code is ascii only or has an encoding declaration (PEP 263)"""

import re
import tokenize

from pylint.checkers import BaseChecker
from pylint.constants import OPTION_RGX
from pylint.interfaces import IRawChecker, ITokenChecker
from pylint.message import MessagesHandlerMixIn


class ByIdManagedMessagesChecker(BaseChecker):

    """checks for messages that are enabled or disabled by id instead of symbol."""

    __implements__ = IRawChecker

    # configuration section name
    name = "miscellaneous"
    msgs = {
        "I0023": (
            "%s",
            "use-symbolic-message-instead",
            "Used when a message is enabled or disabled by id.",
        )
    }

    options = ()

    def process_module(self, module):
        """inspect the source file to find messages activated or deactivated by id."""
        managed_msgs = MessagesHandlerMixIn.get_by_id_managed_msgs()
        for (mod_name, msg_id, msg_symbol, lineno, is_disabled) in managed_msgs:
            if mod_name == module.name:
                if is_disabled:
                    txt = "Id '{ident}' is used to disable '{symbol}' message emission".format(
                        ident=msg_id, symbol=msg_symbol
                    )
                else:
                    txt = "Id '{ident}' is used to enable '{symbol}' message emission".format(
                        ident=msg_id, symbol=msg_symbol
                    )
                self.add_message("use-symbolic-message-instead", line=lineno, args=txt)
        MessagesHandlerMixIn.clear_by_id_managed_msgs()


class EncodingChecker(BaseChecker):

    """checks for:
    * warning notes in the code like FIXME, XXX
    * encoding issues.
    """

    __implements__ = (IRawChecker, ITokenChecker)

    # configuration section name
    name = "miscellaneous"
    msgs = {
        "W0511": (
            "%s",
            "fixme",
            "Used when a warning note as FIXME or XXX is detected.",
        )
    }

    options = (
        (
            "notes",
            {
                "type": "csv",
                "metavar": "<comma separated values>",
                "default": ("FIXME", "XXX", "TODO"),
                "help": (
                    "List of note tags to take in consideration, "
                    "separated by a comma."
                ),
            },
        ),
    )

    def open(self):
        super().open()
        self._fixme_pattern = re.compile(
            r"#\s*(%s)\b" % "|".join(map(re.escape, self.config.notes)), re.I
        )

    def _check_encoding(self, lineno, line, file_encoding):
        try:
            return line.decode(file_encoding)
        except UnicodeDecodeError:
            pass
        except LookupError:
            if line.startswith("#") and "coding" in line and file_encoding in line:
                self.add_message(
                    "syntax-error",
                    line=lineno,
                    args='Cannot decode using encoding "{}",'
                    " bad encoding".format(file_encoding),
                )

    def process_module(self, module):
        """inspect the source file to find encoding problem"""
        if module.file_encoding:
            encoding = module.file_encoding
        else:
            encoding = "ascii"

        with module.stream() as stream:
            for lineno, line in enumerate(stream):
                self._check_encoding(lineno + 1, line, encoding)

    def process_tokens(self, tokens):
        """inspect the source to find fixme problems"""
        if not self.config.notes:
            return
        comments = (
            token_info for token_info in tokens if token_info.type == tokenize.COMMENT
        )
        for comment in comments:
            comment_text = comment.string[1:].lstrip()  # trim '#' and whitespaces

            # handle pylint disable clauses
            disable_option_match = OPTION_RGX.search(comment_text)
            if disable_option_match:
                try:
                    _, value = disable_option_match.group(1).split("=", 1)
                    values = [_val.strip().upper() for _val in value.split(",")]
                    if set(values) & set(self.config.notes):
                        continue
                except ValueError:
                    self.add_message(
                        "bad-inline-option",
                        args=disable_option_match.group(1).strip(),
                        line=comment.start[0],
                    )
                    continue

            # emit warnings if necessary
            match = self._fixme_pattern.search("#" + comment_text.lower())
            if match:
                note = match.group(1)
                self.add_message(
                    "fixme",
                    col_offset=comment.string.lower().index(note.lower()),
                    args=comment_text,
                    line=comment.start[0],
                )


def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(EncodingChecker(linter))
    linter.register_checker(ByIdManagedMessagesChecker(linter))
