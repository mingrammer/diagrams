"""Create DOT code with method-calls."""

import contextlib
import typing

from . import _tools
from . import base
from . import quoting

__all__ = ['GraphSyntax', 'DigraphSyntax', 'Dot']


def comment(line: str) -> str:
    """Return comment header line."""
    return f'// {line}\n'


def graph_head(name: str) -> str:
    """Return DOT graph head line."""
    return f'graph {name}{{\n'


def digraph_head(name: str) -> str:
    """Return DOT digraph head line."""
    return f'digraph {name}{{\n'


def graph_edge(*, tail: str, head: str, attr: str) -> str:
    """Return DOT graph edge statement line."""
    return f'\t{tail} -- {head}{attr}\n'


def digraph_edge(*, tail: str, head: str, attr: str) -> str:
    """Return DOT digraph edge statement line."""
    return f'\t{tail} -> {head}{attr}\n'


class GraphSyntax:
    """DOT graph head and edge syntax."""

    _head = staticmethod(graph_head)

    _edge = staticmethod(graph_edge)


class DigraphSyntax:
    """DOT digraph head and edge syntax."""

    _head = staticmethod(digraph_head)

    _edge = staticmethod(digraph_edge)


def subgraph(name: str) -> str:
    """Return DOT subgraph head line."""
    return f'subgraph {name}{{\n'


def subgraph_plain(name: str) -> str:
    """Return plain DOT subgraph head line."""
    return f'{name}{{\n'


def node(left: str, right: str) -> str:
    """Return DOT node statement line."""
    return f'\t{left}{right}\n'


class Dot(quoting.Quote, base.Base):
    """Assemble DOT source code."""

    directed: bool

    _comment = staticmethod(comment)

    @staticmethod
    def _head(name: str) -> str:  # pragma: no cover
        """Return DOT head line."""
        raise NotImplementedError('must be implemented by concrete subclasses')

    @classmethod
    def _head_strict(cls, name: str) -> str:
        """Return DOT strict head line."""
        return f'strict {cls._head(name)}'

    _tail = '}\n'

    _subgraph = staticmethod(subgraph)

    _subgraph_plain = staticmethod(subgraph_plain)

    _node = _attr = staticmethod(node)

    @classmethod
    def _attr_plain(cls, left: str) -> str:
        return cls._attr(left, '')

    @staticmethod
    def _edge(*, tail: str, head: str, attr: str) -> str:  # pragma: no cover
        """Return DOT edge statement line."""
        raise NotImplementedError('must be implemented by concrete subclasses')

    @classmethod
    def _edge_plain(cls, *, tail: str, head: str) -> str:
        """Return plain DOT edge statement line."""
        return cls._edge(tail=tail, head=head, attr='')

    def __init__(self, *,
                 name: typing.Optional[str] = None,
                 comment: typing.Optional[str] = None,
                 graph_attr=None, node_attr=None, edge_attr=None, body=None,
                 strict: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)

        self.name = name
        """str: DOT source identifier for the ``graph`` or ``digraph`` statement."""

        self.comment = comment
        """str: DOT source comment for the first source line."""

        self.graph_attr = dict(graph_attr) if graph_attr is not None else {}
        """~typing.Dict[str, str]: Attribute-value pairs applying to the graph."""

        self.node_attr = dict(node_attr) if node_attr is not None else {}
        """~typing.Dict[str, str]: Attribute-value pairs applying to all nodes."""

        self.edge_attr = dict(edge_attr) if edge_attr is not None else {}
        """~typing.Dict[str, str]: Attribute-value pairs applying to all edges."""

        self.body = list(body) if body is not None else []
        """~typing.List[str]: Verbatim DOT source lines including final newline."""

        self.strict = strict
        """bool: Rendering should merge multi-edges."""

    def _copy_kwargs(self, **kwargs):
        """Return the kwargs to create a copy of the instance."""
        return super()._copy_kwargs(name=self.name,
                                    comment=self.comment,
                                    graph_attr=dict(self.graph_attr),
                                    node_attr=dict(self.node_attr),
                                    edge_attr=dict(self.edge_attr),
                                    body=list(self.body),
                                    strict=self.strict)

    @_tools.deprecate_positional_args(supported_number=1)
    def clear(self, keep_attrs: bool = False) -> None:
        """Reset content to an empty body, clear graph/node/egde_attr mappings.

        Args:
            keep_attrs (bool): preserve graph/node/egde_attr mappings
        """
        if not keep_attrs:
            for a in (self.graph_attr, self.node_attr, self.edge_attr):
                a.clear()
        self.body.clear()

    @_tools.deprecate_positional_args(supported_number=1)
    def __iter__(self, subgraph: bool = False) -> typing.Iterator[str]:
        r"""Yield the DOT source code line by line (as graph or subgraph).

        Yields: Line ending with a newline (``'\n'``).
        """
        if self.comment:
            yield self._comment(self.comment)

        if subgraph:
            if self.strict:
                raise ValueError('subgraphs cannot be strict')
            head = self._subgraph if self.name else self._subgraph_plain
        else:
            head = self._head_strict if self.strict else self._head
        yield head(self._quote(self.name) + ' ' if self.name else '')

        for kw in ('graph', 'node', 'edge'):
            attrs = getattr(self, f'{kw}_attr')
            if attrs:
                yield self._attr(kw, self._attr_list(None, kwargs=attrs))

        yield from self.body

        yield self._tail

    @_tools.deprecate_positional_args(supported_number=3)
    def node(self, name: str,
             label: typing.Optional[str] = None,
             _attributes=None, **attrs) -> None:
        """Create a node.

        Args:
            name: Unique identifier for the node inside the source.
            label: Caption to be displayed (defaults to the node ``name``).
            attrs: Any additional node attributes (must be strings).

        Attention:
            When rendering ``label``, backslash-escapes
            and strings of the form ``<...>`` have a special meaning.
            See the sections :ref:`backslash-escapes` and
            :ref:`quoting-and-html-like-labels` in the user guide for details.
        """
        name = self._quote(name)
        attr_list = self._attr_list(label, kwargs=attrs, attributes=_attributes)
        line = self._node(name, attr_list)
        self.body.append(line)

    @_tools.deprecate_positional_args(supported_number=4)
    def edge(self, tail_name: str, head_name: str,
             label: typing.Optional[str] = None,
             _attributes=None, **attrs) -> None:
        """Create an edge between two nodes.

        Args:
            tail_name: Start node identifier
                (format: ``node[:port[:compass]]``).
            head_name: End node identifier
                (format: ``node[:port[:compass]]``).
            label: Caption to be displayed near the edge.
            attrs: Any additional edge attributes (must be strings).

        Note:
            The ``tail_name`` and ``head_name`` strings are separated
            by (optional) colon(s) into ``node`` name, ``port`` name,
            and ``compass`` (e.g. ``sw``).
            See :ref:`details in the User Guide <node-ports-compass>`.

        Attention:
            When rendering ``label``, backslash-escapes
            and strings of the form ``<...>`` have a special meaning.
            See the sections :ref:`backslash-escapes` and
            :ref:`quoting-and-html-like-labels` in the user guide for details.
        """
        tail_name = self._quote_edge(tail_name)
        head_name = self._quote_edge(head_name)
        attr_list = self._attr_list(label, kwargs=attrs, attributes=_attributes)
        line = self._edge(tail=tail_name, head=head_name, attr=attr_list)
        self.body.append(line)

    def edges(self, tail_head_iter) -> None:
        """Create a bunch of edges.

        Args:
            tail_head_iter: Iterable of ``(tail_name, head_name)`` pairs
                (format:``node[:port[:compass]]``).


        Note:
            The ``tail_name`` and ``head_name`` strings are separated
            by (optional) colon(s) into ``node`` name, ``port`` name,
            and ``compass`` (e.g. ``sw``).
            See :ref:`details in the User Guide <node-ports-compass>`.
        """
        edge = self._edge_plain
        quote = self._quote_edge
        self.body += [edge(tail=quote(t), head=quote(h))
                      for t, h in tail_head_iter]

    @_tools.deprecate_positional_args(supported_number=2)
    def attr(self, kw: typing.Optional[str] = None,
             _attributes=None, **attrs) -> None:
        """Add a general or graph/node/edge attribute statement.

        Args:
            kw: Attributes target
                (``None`` or ``'graph'``, ``'node'``, ``'edge'``).
            attrs: Attributes to be set (must be strings, may be empty).

        See the :ref:`usage examples in the User Guide <attributes>`.
        """
        if kw is not None and kw.lower() not in ('graph', 'node', 'edge'):
            raise ValueError('attr statement must target graph, node, or edge:'
                             f' {kw!r}')
        if attrs or _attributes:
            if kw is None:
                a_list = self._a_list(None, kwargs=attrs, attributes=_attributes)
                line = self._attr_plain(a_list)
            else:
                attr_list = self._attr_list(None, kwargs=attrs, attributes=_attributes)
                line = self._attr(kw, attr_list)
            self.body.append(line)

    @_tools.deprecate_positional_args(supported_number=2)
    def subgraph(self, graph=None,
                 name: typing.Optional[str] = None,
                 comment: typing.Optional[str] = None,
                 graph_attr=None, node_attr=None, edge_attr=None,
                 body=None):
        """Add the current content of the given sole ``graph`` argument
            as subgraph or return a context manager
            returning a new graph instance
            created with the given (``name``, ``comment``, etc.) arguments
            whose content is added as subgraph
            when leaving the context manager's ``with``-block.

        Args:
            graph: An instance of the same kind
                (:class:`.Graph`, :class:`.Digraph`) as the current graph
                (sole argument in non-with-block use).
            name: Subgraph name (``with``-block use).
            comment: Subgraph comment (``with``-block use).
            graph_attr: Subgraph-level attribute-value mapping
                (``with``-block use).
            node_attr: Node-level attribute-value mapping
                (``with``-block use).
            edge_attr: Edge-level attribute-value mapping
                (``with``-block use).
            body: Verbatim lines to add to the subgraph ``body``
                (``with``-block use).

        See the :ref:`usage examples in the User Guide <subgraphs-clusters>`.

        When used as a context manager, the returned new graph instance
        uses ``strict=None`` and the parent graph's values
        for ``directory``, ``format``, ``engine``, and ``encoding`` by default.

        Note:
            If the ``name`` of the subgraph begins with
            ``'cluster'`` (all lowercase)
            the layout engine will treat it as a special cluster subgraph.
        """
        if graph is None:
            kwargs = self._copy_kwargs()
            kwargs.pop('filename', None)
            kwargs.update(name=name, comment=comment,
                          graph_attr=graph_attr, node_attr=node_attr, edge_attr=edge_attr,
                          body=body, strict=None)
            subgraph = self.__class__(**kwargs)

            @contextlib.contextmanager
            def subgraph_contextmanager(*, parent):
                """Return subgraph and add to parent on exit."""
                yield subgraph
                parent.subgraph(subgraph)

            return subgraph_contextmanager(parent=self)

        args = [name, comment, graph_attr, node_attr, edge_attr, body]
        if not all(a is None for a in args):
            raise ValueError('graph must be sole argument of subgraph()')

        if graph.directed != self.directed:
            raise ValueError(f'{self!r} cannot add subgraph of different kind:'
                             f' {graph!r}')

        self.body += [f'\t{line}' for line in graph.__iter__(subgraph=True)]
