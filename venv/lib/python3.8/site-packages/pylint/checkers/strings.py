# -*- coding: utf-8 -*-
# Copyright (c) 2009 Charles Hebert <charles.hebert@logilab.fr>
# Copyright (c) 2010-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2010 Daniel Harding <dharding@gmail.com>
# Copyright (c) 2012-2014 Google, Inc.
# Copyright (c) 2013-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Brett Cannon <brett@python.org>
# Copyright (c) 2014 Arun Persaud <arun@nubati.net>
# Copyright (c) 2015 Rene Zhang <rz99@cornell.edu>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2016, 2018 Jakub Wilk <jwilk@jwilk.net>
# Copyright (c) 2016 Peter Dawyndt <Peter.Dawyndt@UGent.be>
# Copyright (c) 2017 Łukasz Rogalski <rogalski.91@gmail.com>
# Copyright (c) 2017 Ville Skyttä <ville.skytta@iki.fi>
# Copyright (c) 2018 Nick Drozd <nicholasdrozd@gmail.com>
# Copyright (c) 2018 Anthony Sottile <asottile@umich.edu>


# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""Checker for string formatting operations.
"""

import builtins
import numbers
import tokenize
from collections import Counter

import astroid
from astroid.arguments import CallSite
from astroid.node_classes import Const

from pylint.checkers import BaseChecker, BaseTokenChecker, utils
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker, IRawChecker, ITokenChecker

_AST_NODE_STR_TYPES = ("__builtin__.unicode", "__builtin__.str", "builtins.str")

MSGS = {
    "E1300": (
        "Unsupported format character %r (%#02x) at index %d",
        "bad-format-character",
        "Used when an unsupported format character is used in a format string.",
    ),
    "E1301": (
        "Format string ends in middle of conversion specifier",
        "truncated-format-string",
        "Used when a format string terminates before the end of a "
        "conversion specifier.",
    ),
    "E1302": (
        "Mixing named and unnamed conversion specifiers in format string",
        "mixed-format-string",
        "Used when a format string contains both named (e.g. '%(foo)d') "
        "and unnamed (e.g. '%d') conversion specifiers.  This is also "
        "used when a named conversion specifier contains * for the "
        "minimum field width and/or precision.",
    ),
    "E1303": (
        "Expected mapping for format string, not %s",
        "format-needs-mapping",
        "Used when a format string that uses named conversion specifiers "
        "is used with an argument that is not a mapping.",
    ),
    "W1300": (
        "Format string dictionary key should be a string, not %s",
        "bad-format-string-key",
        "Used when a format string that uses named conversion specifiers "
        "is used with a dictionary whose keys are not all strings.",
    ),
    "W1301": (
        "Unused key %r in format string dictionary",
        "unused-format-string-key",
        "Used when a format string that uses named conversion specifiers "
        "is used with a dictionary that contains keys not required by the "
        "format string.",
    ),
    "E1304": (
        "Missing key %r in format string dictionary",
        "missing-format-string-key",
        "Used when a format string that uses named conversion specifiers "
        "is used with a dictionary that doesn't contain all the keys "
        "required by the format string.",
    ),
    "E1305": (
        "Too many arguments for format string",
        "too-many-format-args",
        "Used when a format string that uses unnamed conversion "
        "specifiers is given too many arguments.",
    ),
    "E1306": (
        "Not enough arguments for format string",
        "too-few-format-args",
        "Used when a format string that uses unnamed conversion "
        "specifiers is given too few arguments",
    ),
    "E1307": (
        "Argument %r does not match format type %r",
        "bad-string-format-type",
        "Used when a type required by format string "
        "is not suitable for actual argument type",
    ),
    "E1310": (
        "Suspicious argument in %s.%s call",
        "bad-str-strip-call",
        "The argument to a str.{l,r,}strip call contains a duplicate character, ",
    ),
    "W1302": (
        "Invalid format string",
        "bad-format-string",
        "Used when a PEP 3101 format string is invalid.",
    ),
    "W1303": (
        "Missing keyword argument %r for format string",
        "missing-format-argument-key",
        "Used when a PEP 3101 format string that uses named fields "
        "doesn't receive one or more required keywords.",
    ),
    "W1304": (
        "Unused format argument %r",
        "unused-format-string-argument",
        "Used when a PEP 3101 format string that uses named "
        "fields is used with an argument that "
        "is not required by the format string.",
    ),
    "W1305": (
        "Format string contains both automatic field numbering "
        "and manual field specification",
        "format-combined-specification",
        "Used when a PEP 3101 format string contains both automatic "
        "field numbering (e.g. '{}') and manual field "
        "specification (e.g. '{0}').",
    ),
    "W1306": (
        "Missing format attribute %r in format specifier %r",
        "missing-format-attribute",
        "Used when a PEP 3101 format string uses an "
        "attribute specifier ({0.length}), but the argument "
        "passed for formatting doesn't have that attribute.",
    ),
    "W1307": (
        "Using invalid lookup key %r in format specifier %r",
        "invalid-format-index",
        "Used when a PEP 3101 format string uses a lookup specifier "
        "({a[1]}), but the argument passed for formatting "
        "doesn't contain or doesn't have that key as an attribute.",
    ),
    "W1308": (
        "Duplicate string formatting argument %r, consider passing as named argument",
        "duplicate-string-formatting-argument",
        "Used when we detect that a string formatting is "
        "repeating an argument instead of using named string arguments",
    ),
}

OTHER_NODES = (
    astroid.Const,
    astroid.List,
    astroid.Lambda,
    astroid.FunctionDef,
    astroid.ListComp,
    astroid.SetComp,
    astroid.GeneratorExp,
)

BUILTINS_STR = builtins.__name__ + ".str"
BUILTINS_FLOAT = builtins.__name__ + ".float"
BUILTINS_INT = builtins.__name__ + ".int"


def get_access_path(key, parts):
    """ Given a list of format specifiers, returns
    the final access path (e.g. a.b.c[0][1]).
    """
    path = []
    for is_attribute, specifier in parts:
        if is_attribute:
            path.append(".{}".format(specifier))
        else:
            path.append("[{!r}]".format(specifier))
    return str(key) + "".join(path)


def arg_matches_format_type(arg_type, format_type):
    if format_type in "sr":
        # All types can be printed with %s and %r
        return True
    if isinstance(arg_type, astroid.Instance):
        arg_type = arg_type.pytype()
        if arg_type == BUILTINS_STR:
            return format_type == "c"
        if arg_type == BUILTINS_FLOAT:
            return format_type in "deEfFgGn%"
        if arg_type == BUILTINS_INT:
            # Integers allow all types
            return True
        return False
    return True


class StringFormatChecker(BaseChecker):
    """Checks string formatting operations to ensure that the format string
    is valid and the arguments match the format string.
    """

    __implements__ = (IAstroidChecker,)
    name = "string"
    msgs = MSGS

    # pylint: disable=too-many-branches
    @check_messages(*MSGS)
    def visit_binop(self, node):
        if node.op != "%":
            return
        left = node.left
        args = node.right

        if not (isinstance(left, astroid.Const) and isinstance(left.value, str)):
            return
        format_string = left.value
        try:
            required_keys, required_num_args, required_key_types, required_arg_types = utils.parse_format_string(
                format_string
            )
        except utils.UnsupportedFormatCharacter as exc:
            formatted = format_string[exc.index]
            self.add_message(
                "bad-format-character",
                node=node,
                args=(formatted, ord(formatted), exc.index),
            )
            return
        except utils.IncompleteFormatString:
            self.add_message("truncated-format-string", node=node)
            return
        if required_keys and required_num_args:
            # The format string uses both named and unnamed format
            # specifiers.
            self.add_message("mixed-format-string", node=node)
        elif required_keys:
            # The format string uses only named format specifiers.
            # Check that the RHS of the % operator is a mapping object
            # that contains precisely the set of keys required by the
            # format string.
            if isinstance(args, astroid.Dict):
                keys = set()
                unknown_keys = False
                for k, _ in args.items:
                    if isinstance(k, astroid.Const):
                        key = k.value
                        if isinstance(key, str):
                            keys.add(key)
                        else:
                            self.add_message(
                                "bad-format-string-key", node=node, args=key
                            )
                    else:
                        # One of the keys was something other than a
                        # constant.  Since we can't tell what it is,
                        # suppress checks for missing keys in the
                        # dictionary.
                        unknown_keys = True
                if not unknown_keys:
                    for key in required_keys:
                        if key not in keys:
                            self.add_message(
                                "missing-format-string-key", node=node, args=key
                            )
                for key in keys:
                    if key not in required_keys:
                        self.add_message(
                            "unused-format-string-key", node=node, args=key
                        )
                for key, arg in args.items:
                    if not isinstance(key, astroid.Const):
                        continue
                    format_type = required_key_types.get(key.value, None)
                    arg_type = utils.safe_infer(arg)
                    if (
                        format_type is not None
                        and arg_type not in (None, astroid.Uninferable)
                        and not arg_matches_format_type(arg_type, format_type)
                    ):
                        self.add_message(
                            "bad-string-format-type",
                            node=node,
                            args=(arg_type.pytype(), format_type),
                        )
            elif isinstance(args, (OTHER_NODES, astroid.Tuple)):
                type_name = type(args).__name__
                self.add_message("format-needs-mapping", node=node, args=type_name)
            # else:
            # The RHS of the format specifier is a name or
            # expression.  It may be a mapping object, so
            # there's nothing we can check.
        else:
            # The format string uses only unnamed format specifiers.
            # Check that the number of arguments passed to the RHS of
            # the % operator matches the number required by the format
            # string.
            args_elts = ()
            if isinstance(args, astroid.Tuple):
                rhs_tuple = utils.safe_infer(args)
                num_args = None
                if hasattr(rhs_tuple, "elts"):
                    args_elts = rhs_tuple.elts
                    num_args = len(args_elts)
            elif isinstance(args, (OTHER_NODES, (astroid.Dict, astroid.DictComp))):
                args_elts = [args]
                num_args = 1
            else:
                # The RHS of the format specifier is a name or
                # expression.  It could be a tuple of unknown size, so
                # there's nothing we can check.
                num_args = None
            if num_args is not None:
                if num_args > required_num_args:
                    self.add_message("too-many-format-args", node=node)
                elif num_args < required_num_args:
                    self.add_message("too-few-format-args", node=node)
                for arg, format_type in zip(args_elts, required_arg_types):
                    if not arg:
                        continue
                    arg_type = utils.safe_infer(arg)
                    if arg_type not in (
                        None,
                        astroid.Uninferable,
                    ) and not arg_matches_format_type(arg_type, format_type):
                        self.add_message(
                            "bad-string-format-type",
                            node=node,
                            args=(arg_type.pytype(), format_type),
                        )

    @check_messages(*MSGS)
    def visit_call(self, node):
        func = utils.safe_infer(node.func)
        if (
            isinstance(func, astroid.BoundMethod)
            and isinstance(func.bound, astroid.Instance)
            and func.bound.name in ("str", "unicode", "bytes")
        ):
            if func.name in ("strip", "lstrip", "rstrip") and node.args:
                arg = utils.safe_infer(node.args[0])
                if not isinstance(arg, astroid.Const) or not isinstance(arg.value, str):
                    return
                if len(arg.value) != len(set(arg.value)):
                    self.add_message(
                        "bad-str-strip-call",
                        node=node,
                        args=(func.bound.name, func.name),
                    )
            elif func.name == "format":
                self._check_new_format(node, func)

    def _detect_vacuous_formatting(self, node, positional_arguments):
        counter = Counter(
            arg.name for arg in positional_arguments if isinstance(arg, astroid.Name)
        )
        for name, count in counter.items():
            if count == 1:
                continue
            self.add_message(
                "duplicate-string-formatting-argument", node=node, args=(name,)
            )

    def _check_new_format(self, node, func):
        """Check the new string formatting. """
        # Skip ormat nodes which don't have an explicit string on the
        # left side of the format operation.
        # We do this because our inference engine can't properly handle
        # redefinitions of the original string.
        # Note that there may not be any left side at all, if the format method
        # has been assigned to another variable. See issue 351. For example:
        #
        #    fmt = 'some string {}'.format
        #    fmt('arg')
        if isinstance(node.func, astroid.Attribute) and not isinstance(
            node.func.expr, astroid.Const
        ):
            return
        if node.starargs or node.kwargs:
            return
        try:
            strnode = next(func.bound.infer())
        except astroid.InferenceError:
            return
        if not (isinstance(strnode, astroid.Const) and isinstance(strnode.value, str)):
            return
        try:
            call_site = CallSite.from_call(node)
        except astroid.InferenceError:
            return

        try:
            fields, num_args, manual_pos = utils.parse_format_method_string(
                strnode.value
            )
        except utils.IncompleteFormatString:
            self.add_message("bad-format-string", node=node)
            return

        positional_arguments = call_site.positional_arguments
        named_arguments = call_site.keyword_arguments
        named_fields = {field[0] for field in fields if isinstance(field[0], str)}
        if num_args and manual_pos:
            self.add_message("format-combined-specification", node=node)
            return

        check_args = False
        # Consider "{[0]} {[1]}" as num_args.
        num_args += sum(1 for field in named_fields if field == "")
        if named_fields:
            for field in named_fields:
                if field and field not in named_arguments:
                    self.add_message(
                        "missing-format-argument-key", node=node, args=(field,)
                    )
            for field in named_arguments:
                if field not in named_fields:
                    self.add_message(
                        "unused-format-string-argument", node=node, args=(field,)
                    )
            # num_args can be 0 if manual_pos is not.
            num_args = num_args or manual_pos
            if positional_arguments or num_args:
                empty = any(True for field in named_fields if field == "")
                if named_arguments or empty:
                    # Verify the required number of positional arguments
                    # only if the .format got at least one keyword argument.
                    # This means that the format strings accepts both
                    # positional and named fields and we should warn
                    # when one of the them is missing or is extra.
                    check_args = True
        else:
            check_args = True
        if check_args:
            # num_args can be 0 if manual_pos is not.
            num_args = num_args or manual_pos
            if len(positional_arguments) > num_args:
                self.add_message("too-many-format-args", node=node)
            elif len(positional_arguments) < num_args:
                self.add_message("too-few-format-args", node=node)

        self._detect_vacuous_formatting(node, positional_arguments)
        self._check_new_format_specifiers(node, fields, named_arguments)

    def _check_new_format_specifiers(self, node, fields, named):
        """
        Check attribute and index access in the format
        string ("{0.a}" and "{0[a]}").
        """
        for key, specifiers in fields:
            # Obtain the argument. If it can't be obtained
            # or inferred, skip this check.
            if key == "":
                # {[0]} will have an unnamed argument, defaulting
                # to 0. It will not be present in `named`, so use the value
                # 0 for it.
                key = 0
            if isinstance(key, numbers.Number):
                try:
                    argname = utils.get_argument_from_call(node, key)
                except utils.NoSuchArgumentError:
                    continue
            else:
                if key not in named:
                    continue
                argname = named[key]
            if argname in (astroid.Uninferable, None):
                continue
            try:
                argument = utils.safe_infer(argname)
            except astroid.InferenceError:
                continue
            if not specifiers or not argument:
                # No need to check this key if it doesn't
                # use attribute / item access
                continue
            if argument.parent and isinstance(argument.parent, astroid.Arguments):
                # Ignore any object coming from an argument,
                # because we can't infer its value properly.
                continue
            previous = argument
            parsed = []
            for is_attribute, specifier in specifiers:
                if previous is astroid.Uninferable:
                    break
                parsed.append((is_attribute, specifier))
                if is_attribute:
                    try:
                        previous = previous.getattr(specifier)[0]
                    except astroid.NotFoundError:
                        if (
                            hasattr(previous, "has_dynamic_getattr")
                            and previous.has_dynamic_getattr()
                        ):
                            # Don't warn if the object has a custom __getattr__
                            break
                        path = get_access_path(key, parsed)
                        self.add_message(
                            "missing-format-attribute",
                            args=(specifier, path),
                            node=node,
                        )
                        break
                else:
                    warn_error = False
                    if hasattr(previous, "getitem"):
                        try:
                            previous = previous.getitem(astroid.Const(specifier))
                        except (
                            astroid.AstroidIndexError,
                            astroid.AstroidTypeError,
                            astroid.AttributeInferenceError,
                        ):
                            warn_error = True
                        except astroid.InferenceError:
                            break
                        if previous is astroid.Uninferable:
                            break
                    else:
                        try:
                            # Lookup __getitem__ in the current node,
                            # but skip further checks, because we can't
                            # retrieve the looked object
                            previous.getattr("__getitem__")
                            break
                        except astroid.NotFoundError:
                            warn_error = True
                    if warn_error:
                        path = get_access_path(key, parsed)
                        self.add_message(
                            "invalid-format-index", args=(specifier, path), node=node
                        )
                        break

                try:
                    previous = next(previous.infer())
                except astroid.InferenceError:
                    # can't check further if we can't infer it
                    break


class StringConstantChecker(BaseTokenChecker):
    """Check string literals"""

    __implements__ = (IAstroidChecker, ITokenChecker, IRawChecker)
    name = "string"
    msgs = {
        "W1401": (
            "Anomalous backslash in string: '%s'. "
            "String constant might be missing an r prefix.",
            "anomalous-backslash-in-string",
            "Used when a backslash is in a literal string but not as an escape.",
        ),
        "W1402": (
            "Anomalous Unicode escape in byte string: '%s'. "
            "String constant might be missing an r or u prefix.",
            "anomalous-unicode-escape-in-string",
            "Used when an escape like \\u is encountered in a byte "
            "string where it has no effect.",
        ),
        "W1403": (
            "Implicit string concatenation found in %s",
            "implicit-str-concat-in-sequence",
            "String literals are implicitly concatenated in a "
            "literal iterable definition : "
            "maybe a comma is missing ?",
        ),
    }
    options = (
        (
            "check-str-concat-over-line-jumps",
            {
                "default": False,
                "type": "yn",
                "metavar": "<y_or_n>",
                "help": "This flag controls whether the "
                "implicit-str-concat-in-sequence should generate a warning "
                "on implicit string concatenation in sequences defined over "
                "several lines.",
            },
        ),
    )

    # Characters that have a special meaning after a backslash in either
    # Unicode or byte strings.
    ESCAPE_CHARACTERS = "abfnrtvx\n\r\t\\'\"01234567"

    # Characters that have a special meaning after a backslash but only in
    # Unicode strings.
    UNICODE_ESCAPE_CHARACTERS = "uUN"

    def __init__(self, *args, **kwargs):
        super(StringConstantChecker, self).__init__(*args, **kwargs)
        self.string_tokens = {}  # token position -> (token value, next token)

    def process_module(self, module):
        self._unicode_literals = "unicode_literals" in module.future_imports

    def process_tokens(self, tokens):
        encoding = "ascii"
        for i, (tok_type, token, start, _, line) in enumerate(tokens):
            if tok_type == tokenize.ENCODING:
                # this is always the first token processed
                encoding = token
            elif tok_type == tokenize.STRING:
                # 'token' is the whole un-parsed token; we can look at the start
                # of it to see whether it's a raw or unicode string etc.
                self.process_string_token(token, start[0])
                # We figure the next token, ignoring comments & newlines:
                j = i + 1
                while j < len(tokens) and tokens[j].type in (
                    tokenize.NEWLINE,
                    tokenize.NL,
                    tokenize.COMMENT,
                ):
                    j += 1
                next_token = tokens[j] if j < len(tokens) else None
                if encoding != "ascii":
                    # We convert `tokenize` character count into a byte count,
                    # to match with astroid `.col_offset`
                    start = (start[0], len(line[: start[1]].encode(encoding)))
                self.string_tokens[start] = (str_eval(token), next_token)

    @check_messages(*(msgs.keys()))
    def visit_list(self, node):
        self.check_for_concatenated_strings(node, "list")

    @check_messages(*(msgs.keys()))
    def visit_set(self, node):
        self.check_for_concatenated_strings(node, "set")

    @check_messages(*(msgs.keys()))
    def visit_tuple(self, node):
        self.check_for_concatenated_strings(node, "tuple")

    def check_for_concatenated_strings(self, iterable_node, iterable_type):
        for elt in iterable_node.elts:
            if isinstance(elt, Const) and elt.pytype() in _AST_NODE_STR_TYPES:
                if elt.col_offset < 0:
                    # This can happen in case of escaped newlines
                    continue
                if (elt.lineno, elt.col_offset) not in self.string_tokens:
                    # This may happen with Latin1 encoding
                    # cf. https://github.com/PyCQA/pylint/issues/2610
                    continue
                matching_token, next_token = self.string_tokens[
                    (elt.lineno, elt.col_offset)
                ]
                # We detect string concatenation: the AST Const is the
                # combination of 2 string tokens
                if matching_token != elt.value and next_token is not None:
                    if next_token.type == tokenize.STRING and (
                        next_token.start[0] == elt.lineno
                        or self.config.check_str_concat_over_line_jumps
                    ):
                        self.add_message(
                            "implicit-str-concat-in-sequence",
                            line=elt.lineno,
                            args=(iterable_type,),
                        )

    def process_string_token(self, token, start_row):
        quote_char = None
        index = None
        for index, char in enumerate(token):
            if char in "'\"":
                quote_char = char
                break
        if quote_char is None:
            return

        prefix = token[:index].lower()  # markers like u, b, r.
        after_prefix = token[index:]
        if after_prefix[:3] == after_prefix[-3:] == 3 * quote_char:
            string_body = after_prefix[3:-3]
        else:
            string_body = after_prefix[1:-1]  # Chop off quotes
        # No special checks on raw strings at the moment.
        if "r" not in prefix:
            self.process_non_raw_string_token(prefix, string_body, start_row)

    def process_non_raw_string_token(self, prefix, string_body, start_row):
        """check for bad escapes in a non-raw string.

        prefix: lowercase string of eg 'ur' string prefix markers.
        string_body: the un-parsed body of the string, not including the quote
        marks.
        start_row: integer line number in the source.
        """
        # Walk through the string; if we see a backslash then escape the next
        # character, and skip over it.  If we see a non-escaped character,
        # alert, and continue.
        #
        # Accept a backslash when it escapes a backslash, or a quote, or
        # end-of-line, or one of the letters that introduce a special escape
        # sequence <http://docs.python.org/reference/lexical_analysis.html>
        #
        index = 0
        while True:
            index = string_body.find("\\", index)
            if index == -1:
                break
            # There must be a next character; having a backslash at the end
            # of the string would be a SyntaxError.
            next_char = string_body[index + 1]
            match = string_body[index : index + 2]
            if next_char in self.UNICODE_ESCAPE_CHARACTERS:
                if "u" in prefix:
                    pass
                elif "b" not in prefix:
                    pass  # unicode by default
                else:
                    self.add_message(
                        "anomalous-unicode-escape-in-string",
                        line=start_row,
                        args=(match,),
                        col_offset=index,
                    )
            elif next_char not in self.ESCAPE_CHARACTERS:
                self.add_message(
                    "anomalous-backslash-in-string",
                    line=start_row,
                    args=(match,),
                    col_offset=index,
                )
            # Whether it was a valid escape or not, backslash followed by
            # another character can always be consumed whole: the second
            # character can never be the start of a new backslash escape.
            index += 2


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(StringFormatChecker(linter))
    linter.register_checker(StringConstantChecker(linter))


def str_eval(token):
    """
    Mostly replicate `ast.literal_eval(token)` manually to avoid any performance hit.
    This supports f-strings, contrary to `ast.literal_eval`.
    We have to support all string literal notations:
    https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals
    """
    if token[0:2].lower() in ("fr", "rf"):
        token = token[2:]
    elif token[0].lower() in ("r", "u", "f"):
        token = token[1:]
    if token[0:3] in ('"""', "'''"):
        return token[3:-3]
    return token[1:-1]
