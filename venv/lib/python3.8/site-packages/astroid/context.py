# Copyright (c) 2015-2016, 2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>
# Copyright (c) 2018 Nick Drozd <nicholasdrozd@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

"""Various context related utilities, including inference and call contexts."""
import contextlib
import pprint
from typing import Optional


class InferenceContext:
    """Provide context for inference

    Store already inferred nodes to save time
    Account for already visited nodes to infinite stop infinite recursion
    """

    __slots__ = (
        "path",
        "lookupname",
        "callcontext",
        "boundnode",
        "inferred",
        "extra_context",
    )

    def __init__(self, path=None, inferred=None):
        self.path = path or set()
        """
        :type: set(tuple(NodeNG, optional(str)))

        Path of visited nodes and their lookupname

        Currently this key is ``(node, context.lookupname)``
        """
        self.lookupname = None
        """
        :type: optional[str]

        The original name of the node

        e.g.
        foo = 1
        The inference of 'foo' is nodes.Const(1) but the lookup name is 'foo'
        """
        self.callcontext = None
        """
        :type: optional[CallContext]

        The call arguments and keywords for the given context
        """
        self.boundnode = None
        """
        :type: optional[NodeNG]

        The bound node of the given context

        e.g. the bound node of object.__new__(cls) is the object node
        """
        self.inferred = inferred or {}
        """
        :type: dict(seq, seq)

        Inferred node contexts to their mapped results
        Currently the key is ``(node, lookupname, callcontext, boundnode)``
        and the value is tuple of the inferred results
        """
        self.extra_context = {}
        """
        :type: dict(NodeNG, Context)

        Context that needs to be passed down through call stacks
        for call arguments
        """

    def push(self, node):
        """Push node into inference path

        :return: True if node is already in context path else False
        :rtype: bool

        Allows one to see if the given node has already
        been looked at for this inference context"""
        name = self.lookupname
        if (node, name) in self.path:
            return True

        self.path.add((node, name))
        return False

    def clone(self):
        """Clone inference path

        For example, each side of a binary operation (BinOp)
        starts with the same context but diverge as each side is inferred
        so the InferenceContext will need be cloned"""
        # XXX copy lookupname/callcontext ?
        clone = InferenceContext(self.path, inferred=self.inferred)
        clone.callcontext = self.callcontext
        clone.boundnode = self.boundnode
        clone.extra_context = self.extra_context
        return clone

    def cache_generator(self, key, generator):
        """Cache result of generator into dictionary

        Used to cache inference results"""
        results = []
        for result in generator:
            results.append(result)
            yield result

        self.inferred[key] = tuple(results)

    @contextlib.contextmanager
    def restore_path(self):
        path = set(self.path)
        yield
        self.path = path

    def __str__(self):
        state = (
            "%s=%s"
            % (field, pprint.pformat(getattr(self, field), width=80 - len(field)))
            for field in self.__slots__
        )
        return "%s(%s)" % (type(self).__name__, ",\n    ".join(state))


class CallContext:
    """Holds information for a call site."""

    __slots__ = ("args", "keywords")

    def __init__(self, args, keywords=None):
        """
        :param List[NodeNG] args: Call positional arguments
        :param Union[List[nodes.Keyword], None] keywords: Call keywords
        """
        self.args = args
        if keywords:
            keywords = [(arg.arg, arg.value) for arg in keywords]
        else:
            keywords = []
        self.keywords = keywords


def copy_context(context: Optional[InferenceContext]) -> InferenceContext:
    """Clone a context if given, or return a fresh contexxt"""
    if context is not None:
        return context.clone()

    return InferenceContext()


def bind_context_to_node(context, node):
    """Give a context a boundnode
    to retrieve the correct function name or attribute value
    with from further inference.

    Do not use an existing context since the boundnode could then
    be incorrectly propagated higher up in the call stack.

    :param context: Context to use
    :type context: Optional(context)

    :param node: Node to do name lookups from
    :type node NodeNG:

    :returns: A new context
    :rtype: InferenceContext
    """
    context = copy_context(context)
    context.boundnode = node
    return context
