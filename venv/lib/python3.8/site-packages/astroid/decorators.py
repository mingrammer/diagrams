# Copyright (c) 2015-2016, 2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2015 Florian Bruhin <me@the-compiler.org>
# Copyright (c) 2016 Derek Gustafson <degustaf@gmail.com>
# Copyright (c) 2018 Nick Drozd <nicholasdrozd@gmail.com>
# Copyright (c) 2018 Ashley Whetter <ashley@awhetter.co.uk>
# Copyright (c) 2018 HoverHell <hoverhell@gmail.com>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

""" A few useful function/method decorators."""

import functools

import wrapt

from astroid import context as contextmod
from astroid import exceptions
from astroid import util


@wrapt.decorator
def cached(func, instance, args, kwargs):
    """Simple decorator to cache result of method calls without args."""
    cache = getattr(instance, "__cache", None)
    if cache is None:
        instance.__cache = cache = {}
    try:
        return cache[func]
    except KeyError:
        cache[func] = result = func(*args, **kwargs)
        return result


class cachedproperty:
    """ Provides a cached property equivalent to the stacking of
    @cached and @property, but more efficient.

    After first usage, the <property_name> becomes part of the object's
    __dict__. Doing:

      del obj.<property_name> empties the cache.

    Idea taken from the pyramid_ framework and the mercurial_ project.

    .. _pyramid: http://pypi.python.org/pypi/pyramid
    .. _mercurial: http://pypi.python.org/pypi/Mercurial
    """

    __slots__ = ("wrapped",)

    def __init__(self, wrapped):
        try:
            wrapped.__name__
        except AttributeError as exc:
            raise TypeError("%s must have a __name__ attribute" % wrapped) from exc
        self.wrapped = wrapped

    @property
    def __doc__(self):
        doc = getattr(self.wrapped, "__doc__", None)
        return "<wrapped by the cachedproperty decorator>%s" % (
            "\n%s" % doc if doc else ""
        )

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


def path_wrapper(func):
    """return the given infer function wrapped to handle the path

    Used to stop inference if the node has already been looked
    at for a given `InferenceContext` to prevent infinite recursion
    """

    @functools.wraps(func)
    def wrapped(node, context=None, _func=func, **kwargs):
        """wrapper function handling context"""
        if context is None:
            context = contextmod.InferenceContext()
        if context.push(node):
            return None

        yielded = set()
        generator = _func(node, context, **kwargs)
        try:
            while True:
                res = next(generator)
                # unproxy only true instance, not const, tuple, dict...
                if res.__class__.__name__ == "Instance":
                    ares = res._proxied
                else:
                    ares = res
                if ares not in yielded:
                    yield res
                    yielded.add(ares)
        except StopIteration as error:
            if error.args:
                return error.args[0]
            return None

    return wrapped


@wrapt.decorator
def yes_if_nothing_inferred(func, instance, args, kwargs):
    generator = func(*args, **kwargs)

    try:
        yield next(generator)
    except StopIteration:
        # generator is empty
        yield util.Uninferable
        return

    yield from generator


@wrapt.decorator
def raise_if_nothing_inferred(func, instance, args, kwargs):
    generator = func(*args, **kwargs)

    try:
        yield next(generator)
    except StopIteration as error:
        # generator is empty
        if error.args:
            # pylint: disable=not-a-mapping
            raise exceptions.InferenceError(**error.args[0])
        raise exceptions.InferenceError(
            "StopIteration raised without any error information."
        )

    yield from generator
