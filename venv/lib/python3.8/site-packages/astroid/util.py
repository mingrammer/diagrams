# Copyright (c) 2015-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>
# Copyright (c) 2018 Nick Drozd <nicholasdrozd@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

import warnings
from itertools import islice

import importlib
import lazy_object_proxy


def lazy_descriptor(obj):
    class DescriptorProxy(lazy_object_proxy.Proxy):
        def __get__(self, instance, owner=None):
            return self.__class__.__get__(self, instance)

    return DescriptorProxy(obj)


def lazy_import(module_name):
    return lazy_object_proxy.Proxy(
        lambda: importlib.import_module("." + module_name, "astroid")
    )


@object.__new__
class Uninferable:
    """Special inference object, which is returned when inference fails."""

    def __repr__(self):
        return "Uninferable"

    __str__ = __repr__

    def __getattribute__(self, name):
        if name == "next":
            raise AttributeError("next method should not be called")
        if name.startswith("__") and name.endswith("__"):
            return object.__getattribute__(self, name)
        if name == "accept":
            return object.__getattribute__(self, name)
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def accept(self, visitor):
        func = getattr(visitor, "visit_uninferable")
        return func(self)


class BadOperationMessage:
    """Object which describes a TypeError occurred somewhere in the inference chain

    This is not an exception, but a container object which holds the types and
    the error which occurred.
    """


class BadUnaryOperationMessage(BadOperationMessage):
    """Object which describes operational failures on UnaryOps."""

    def __init__(self, operand, op, error):
        self.operand = operand
        self.op = op
        self.error = error

    @property
    def _object_type_helper(self):
        helpers = lazy_import("helpers")
        return helpers.object_type

    def _object_type(self, obj):
        # pylint: disable=not-callable; can't infer lazy_import
        objtype = self._object_type_helper(obj)
        if objtype is Uninferable:
            return None

        return objtype

    def __str__(self):
        if hasattr(self.operand, "name"):
            operand_type = self.operand.name
        else:
            object_type = self._object_type(self.operand)
            if hasattr(object_type, "name"):
                operand_type = object_type.name
            else:
                # Just fallback to as_string
                operand_type = object_type.as_string()

        msg = "bad operand type for unary {}: {}"
        return msg.format(self.op, operand_type)


class BadBinaryOperationMessage(BadOperationMessage):
    """Object which describes type errors for BinOps."""

    def __init__(self, left_type, op, right_type):
        self.left_type = left_type
        self.right_type = right_type
        self.op = op

    def __str__(self):
        msg = "unsupported operand type(s) for {}: {!r} and {!r}"
        return msg.format(self.op, self.left_type.name, self.right_type.name)


def _instancecheck(cls, other):
    wrapped = cls.__wrapped__
    other_cls = other.__class__
    is_instance_of = wrapped is other_cls or issubclass(other_cls, wrapped)
    warnings.warn(
        "%r is deprecated and slated for removal in astroid "
        "2.0, use %r instead" % (cls.__class__.__name__, wrapped.__name__),
        PendingDeprecationWarning,
        stacklevel=2,
    )
    return is_instance_of


def proxy_alias(alias_name, node_type):
    """Get a Proxy from the given name to the given node type."""
    proxy = type(
        alias_name,
        (lazy_object_proxy.Proxy,),
        {
            "__class__": object.__dict__["__class__"],
            "__instancecheck__": _instancecheck,
        },
    )
    return proxy(lambda: node_type)


def limit_inference(iterator, size):
    """Limit inference amount.

    Limit inference amount to help with performance issues with
    exponentially exploding possible results.

    :param iterator: Inference generator to limit
    :type iterator: Iterator(NodeNG)

    :param size: Maximum mount of nodes yielded plus an
        Uninferable at the end if limit reached
    :type size: int

    :yields: A possibly modified generator
    :rtype param: Iterable
    """
    yield from islice(iterator, size)
    has_more = next(iterator, False)
    if has_more is not False:
        yield Uninferable
        return
