# Copyright (c) 2014-2016, 2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER


"""Astroid hooks for six module."""

from textwrap import dedent

from astroid import MANAGER, register_module_extender
from astroid.builder import AstroidBuilder
from astroid.exceptions import (
    AstroidBuildingError,
    InferenceError,
    AttributeInferenceError,
)
from astroid import nodes


SIX_ADD_METACLASS = "six.add_metaclass"


def _indent(text, prefix, predicate=None):
    """Adds 'prefix' to the beginning of selected lines in 'text'.

    If 'predicate' is provided, 'prefix' will only be added to the lines
    where 'predicate(line)' is True. If 'predicate' is not provided,
    it will default to adding 'prefix' to all non-empty lines that do not
    consist solely of whitespace characters.
    """
    if predicate is None:
        predicate = lambda line: line.strip()

    def prefixed_lines():
        for line in text.splitlines(True):
            yield prefix + line if predicate(line) else line

    return "".join(prefixed_lines())


_IMPORTS = """
import _io
cStringIO = _io.StringIO
filter = filter
from itertools import filterfalse
input = input
from sys import intern
map = map
range = range
from imp import reload as reload_module
from functools import reduce
from shlex import quote as shlex_quote
from io import StringIO
from collections import UserDict, UserList, UserString
xrange = range
zip = zip
from itertools import zip_longest
import builtins
import configparser
import copyreg
import _dummy_thread
import http.cookiejar as http_cookiejar
import http.cookies as http_cookies
import html.entities as html_entities
import html.parser as html_parser
import http.client as http_client
import http.server as http_server
BaseHTTPServer = CGIHTTPServer = SimpleHTTPServer = http.server
import pickle as cPickle
import queue
import reprlib
import socketserver
import _thread
import winreg
import xmlrpc.server as xmlrpc_server
import xmlrpc.client as xmlrpc_client
import urllib.robotparser as urllib_robotparser
import email.mime.multipart as email_mime_multipart
import email.mime.nonmultipart as email_mime_nonmultipart
import email.mime.text as email_mime_text
import email.mime.base as email_mime_base
import urllib.parse as urllib_parse
import urllib.error as urllib_error
import tkinter
import tkinter.dialog as tkinter_dialog
import tkinter.filedialog as tkinter_filedialog
import tkinter.scrolledtext as tkinter_scrolledtext
import tkinter.simpledialog as tkinder_simpledialog
import tkinter.tix as tkinter_tix
import tkinter.ttk as tkinter_ttk
import tkinter.constants as tkinter_constants
import tkinter.dnd as tkinter_dnd
import tkinter.colorchooser as tkinter_colorchooser
import tkinter.commondialog as tkinter_commondialog
import tkinter.filedialog as tkinter_tkfiledialog
import tkinter.font as tkinter_font
import tkinter.messagebox as tkinter_messagebox
import urllib
import urllib.request as urllib_request
import urllib.robotparser as urllib_robotparser
import urllib.parse as urllib_parse
import urllib.error as urllib_error
"""


def six_moves_transform():
    code = dedent(
        """
    class Moves(object):
    {}
    moves = Moves()
    """
    ).format(_indent(_IMPORTS, "    "))
    module = AstroidBuilder(MANAGER).string_build(code)
    module.name = "six.moves"
    return module


def _six_fail_hook(modname):
    """Fix six.moves imports due to the dynamic nature of this
    class.

    Construct a pseudo-module which contains all the necessary imports
    for six

    :param modname: Name of failed module
    :type modname: str

    :return: An astroid module
    :rtype: nodes.Module
    """

    attribute_of = modname != "six.moves" and modname.startswith("six.moves")
    if modname != "six.moves" and not attribute_of:
        raise AstroidBuildingError(modname=modname)
    module = AstroidBuilder(MANAGER).string_build(_IMPORTS)
    module.name = "six.moves"
    if attribute_of:
        # Facilitate import of submodules in Moves
        start_index = len(module.name)
        attribute = modname[start_index:].lstrip(".").replace(".", "_")
        try:
            import_attr = module.getattr(attribute)[0]
        except AttributeInferenceError:
            raise AstroidBuildingError(modname=modname)
        if isinstance(import_attr, nodes.Import):
            submodule = MANAGER.ast_from_module_name(import_attr.names[0][0])
            return submodule
    # Let dummy submodule imports pass through
    # This will cause an Uninferable result, which is okay
    return module


def _looks_like_decorated_with_six_add_metaclass(node):
    if not node.decorators:
        return False

    for decorator in node.decorators.nodes:
        if not isinstance(decorator, nodes.Call):
            continue
        if decorator.func.as_string() == SIX_ADD_METACLASS:
            return True
    return False


def transform_six_add_metaclass(node):
    """Check if the given class node is decorated with *six.add_metaclass*

    If so, inject its argument as the metaclass of the underlying class.
    """
    if not node.decorators:
        return

    for decorator in node.decorators.nodes:
        if not isinstance(decorator, nodes.Call):
            continue

        try:
            func = next(decorator.func.infer())
        except InferenceError:
            continue
        if func.qname() == SIX_ADD_METACLASS and decorator.args:
            metaclass = decorator.args[0]
            node._metaclass = metaclass
            return node


register_module_extender(MANAGER, "six", six_moves_transform)
register_module_extender(
    MANAGER, "requests.packages.urllib3.packages.six", six_moves_transform
)
MANAGER.register_failed_import_hook(_six_fail_hook)
MANAGER.register_transform(
    nodes.ClassDef,
    transform_six_add_metaclass,
    _looks_like_decorated_with_six_add_metaclass,
)
