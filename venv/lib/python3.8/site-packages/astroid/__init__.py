# Copyright (c) 2006-2013, 2015 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2014 Google, Inc.
# Copyright (c) 2014 Eevee (Alex Munroe) <amunroe@yelp.com>
# Copyright (c) 2015-2016, 2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2016 Derek Gustafson <degustaf@gmail.com>
# Copyright (c) 2016 Moises Lopez <moylop260@vauxoo.com>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

"""Python Abstract Syntax Tree New Generation

The aim of this module is to provide a common base representation of
python source code for projects such as pychecker, pyreverse,
pylint... Well, actually the development of this library is essentially
governed by pylint's needs.

It extends class defined in the python's _ast module with some
additional methods and attributes. Instance attributes are added by a
builder object, which can either generate extended ast (let's call
them astroid ;) by visiting an existent ast tree or by inspecting living
object. Methods are added by monkey patching ast classes.

Main modules are:

* nodes and scoped_nodes for more information about methods and
  attributes added to different node classes

* the manager contains a high level object to get astroid trees from
  source files and living objects. It maintains a cache of previously
  constructed tree for quick access

* builder contains the class responsible to build astroid trees
"""

import enum
import itertools
import os
import sys

import wrapt


_Context = enum.Enum("Context", "Load Store Del")
Load = _Context.Load
Store = _Context.Store
Del = _Context.Del
del _Context


from .__pkginfo__ import version as __version__

# WARNING: internal imports order matters !

# pylint: disable=redefined-builtin

# make all exception classes accessible from astroid package
from astroid.exceptions import *

# make all node classes accessible from astroid package
from astroid.nodes import *

# trigger extra monkey-patching
from astroid import inference

# more stuff available
from astroid import raw_building
from astroid.bases import BaseInstance, Instance, BoundMethod, UnboundMethod
from astroid.node_classes import are_exclusive, unpack_infer
from astroid.scoped_nodes import builtin_lookup
from astroid.builder import parse, extract_node
from astroid.util import Uninferable

# make a manager instance (borg) accessible from astroid package
from astroid.manager import AstroidManager

MANAGER = AstroidManager()
del AstroidManager

# transform utilities (filters and decorator)


# pylint: disable=dangerous-default-value
@wrapt.decorator
def _inference_tip_cached(func, instance, args, kwargs, _cache={}):
    """Cache decorator used for inference tips"""
    node = args[0]
    try:
        return iter(_cache[func, node])
    except KeyError:
        result = func(*args, **kwargs)
        # Need to keep an iterator around
        original, copy = itertools.tee(result)
        _cache[func, node] = list(copy)
        return original


# pylint: enable=dangerous-default-value


def inference_tip(infer_function, raise_on_overwrite=False):
    """Given an instance specific inference function, return a function to be
    given to MANAGER.register_transform to set this inference function.

    :param bool raise_on_overwrite: Raise an `InferenceOverwriteError`
        if the inference tip will overwrite another. Used for debugging

    Typical usage

    .. sourcecode:: python

       MANAGER.register_transform(Call, inference_tip(infer_named_tuple),
                                  predicate)

    .. Note::

        Using an inference tip will override
        any previously set inference tip for the given
        node. Use a predicate in the transform to prevent
        excess overwrites.
    """

    def transform(node, infer_function=infer_function):
        if (
            raise_on_overwrite
            and node._explicit_inference is not None
            and node._explicit_inference is not infer_function
        ):
            raise InferenceOverwriteError(
                "Inference already set to {existing_inference}. "
                "Trying to overwrite with {new_inference} for {node}".format(
                    existing_inference=infer_function,
                    new_inference=node._explicit_inference,
                    node=node,
                )
            )
        # pylint: disable=no-value-for-parameter
        node._explicit_inference = _inference_tip_cached(infer_function)
        return node

    return transform


def register_module_extender(manager, module_name, get_extension_mod):
    def transform(node):
        extension_module = get_extension_mod()
        for name, objs in extension_module.locals.items():
            node.locals[name] = objs
            for obj in objs:
                if obj.parent is extension_module:
                    obj.parent = node

    manager.register_transform(Module, transform, lambda n: n.name == module_name)


# load brain plugins
BRAIN_MODULES_DIR = os.path.join(os.path.dirname(__file__), "brain")
if BRAIN_MODULES_DIR not in sys.path:
    # add it to the end of the list so user path take precedence
    sys.path.append(BRAIN_MODULES_DIR)
# load modules in this directory
for module in os.listdir(BRAIN_MODULES_DIR):
    if module.endswith(".py"):
        __import__(module[:-3])
