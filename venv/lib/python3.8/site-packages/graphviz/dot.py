# dot.py - create dot code

r"""Assemble DOT source code objects.

>>> dot = Graph(comment=u'M\xf8nti Pyth\xf8n ik den H\xf8lie Grailen')

>>> dot.node(u'M\xf8\xf8se')
>>> dot.node('trained_by', u'trained by')
>>> dot.node('tutte', u'TUTTE HERMSGERVORDENBROTBORDA')

>>> dot.edge(u'M\xf8\xf8se', 'trained_by')
>>> dot.edge('trained_by', 'tutte')

>>> dot.node_attr['shape'] = 'rectangle'

>>> print(dot.source.replace(u'\xf8', '0'))  #doctest: +NORMALIZE_WHITESPACE
// M0nti Pyth0n ik den H0lie Grailen
graph {
    node [shape=rectangle]
    "M00se"
    trained_by [label="trained by"]
    tutte [label="TUTTE HERMSGERVORDENBROTBORDA"]
    "M00se" -- trained_by
    trained_by -- tutte
}

>>> dot.view('test-output/m00se.gv')  # doctest: +SKIP
'test-output/m00se.gv.pdf'
"""

from . import lang
from . import files

__all__ = ['Graph', 'Digraph']


class Dot(files.File):
    """Assemble, save, and render DOT source code, open result in viewer."""

    _comment = '// %s'
    _subgraph = 'subgraph %s{'
    _subgraph_plain = '%s{'
    _node = _attr = '\t%s%s'
    _attr_plain = _attr % ('%s', '')
    _tail = '}'

    _quote = staticmethod(lang.quote)
    _quote_edge = staticmethod(lang.quote_edge)

    _a_list = staticmethod(lang.a_list)
    _attr_list = staticmethod(lang.attr_list)

    def __init__(self, name=None, comment=None,
                 filename=None, directory=None,
                 format=None, engine=None, encoding=files.ENCODING,
                 graph_attr=None, node_attr=None, edge_attr=None, body=None,
                 strict=False):
        self.name = name
        self.comment = comment

        super(Dot, self).__init__(filename, directory, format, engine, encoding)

        self.graph_attr = dict(graph_attr) if graph_attr is not None else {}
        self.node_attr = dict(node_attr) if node_attr is not None else {}
        self.edge_attr = dict(edge_attr) if edge_attr is not None else {}

        self.body = list(body) if body is not None else []

        self.strict = strict

    def _kwargs(self):
        result = super(Dot, self)._kwargs()
        result.update(name=self.name,
                      comment=self.comment,
                      graph_attr=dict(self.graph_attr),
                      node_attr=dict(self.node_attr),
                      edge_attr=dict(self.edge_attr),
                      body=list(self.body),
                      strict=self.strict)
        return result

    def clear(self, keep_attrs=False):
        """Reset content to an empty body, clear graph/node/egde_attr mappings.

        Args:
            keep_attrs (bool): preserve graph/node/egde_attr mappings
        """
        if not keep_attrs:
            for a in (self.graph_attr, self.node_attr, self.edge_attr):
                a.clear()
        del self.body[:]

    def __iter__(self, subgraph=False):
        """Yield the DOT source code line by line (as graph or subgraph)."""
        if self.comment:
            yield self._comment % self.comment

        if subgraph:
            if self.strict:
                raise ValueError('subgraphs cannot be strict')
            head = self._subgraph if self.name else self._subgraph_plain
        else:
            head = self._head_strict if self.strict else self._head
        yield head % (self._quote(self.name) + ' ' if self.name else '')

        for kw in ('graph', 'node', 'edge'):
            attrs = getattr(self, '%s_attr' % kw)
            if attrs:
                yield self._attr % (kw, self._attr_list(None, attrs))

        for line in self.body:
            yield line

        yield self._tail

    def __str__(self):
        """The DOT source code as string."""
        return '\n'.join(self)

    source = property(__str__, doc=__str__.__doc__)

    def node(self, name, label=None, _attributes=None, **attrs):
        """Create a node.

        Args:
            name: Unique identifier for the node inside the source.
            label: Caption to be displayed (defaults to the node ``name``).
            attrs: Any additional node attributes (must be strings).
        """
        name = self._quote(name)
        attr_list = self._attr_list(label, attrs, _attributes)
        line = self._node % (name, attr_list)
        self.body.append(line)

    def edge(self, tail_name, head_name, label=None, _attributes=None, **attrs):
        """Create an edge between two nodes.

        Args:
            tail_name: Start node identifier.
            head_name: End node identifier.
            label: Caption to be displayed near the edge.
            attrs: Any additional edge attributes (must be strings).
        """
        tail_name = self._quote_edge(tail_name)
        head_name = self._quote_edge(head_name)
        attr_list = self._attr_list(label, attrs, _attributes)
        line = self._edge % (tail_name, head_name, attr_list)
        self.body.append(line)

    def edges(self, tail_head_iter):
        """Create a bunch of edges.

        Args:
            tail_head_iter: Iterable of ``(tail_name, head_name)`` pairs.
        """
        edge = self._edge_plain
        quote = self._quote_edge
        lines = (edge % (quote(t), quote(h)) for t, h in tail_head_iter)
        self.body.extend(lines)

    def attr(self, kw=None, _attributes=None, **attrs):
        """Add a general or graph/node/edge attribute statement.

        Args:
            kw: Attributes target (``None`` or ``'graph'``, ``'node'``, ``'edge'``).
            attrs: Attributes to be set (must be strings, may be empty).

        See the :ref:`usage examples in the User Guide <attributes>`.
        """
        if kw is not None and kw.lower() not in ('graph', 'node', 'edge'):
            raise ValueError('attr statement must target graph, node, or edge: '
                '%r' % kw)
        if attrs or _attributes:
            if kw is None:
                a_list = self._a_list(None, attrs, _attributes)
                line = self._attr_plain % a_list
            else:
                attr_list = self._attr_list(None, attrs, _attributes)
                line = self._attr % (kw, attr_list)
            self.body.append(line)

    def subgraph(self, graph=None, name=None, comment=None,
                 graph_attr=None, node_attr=None, edge_attr=None, body=None):
        """Add the current content of the given sole ``graph`` argument as subgraph \
           or return a context manager returning a new graph instance created \
           with the given (``name``, ``comment``, etc.) arguments whose content is \
           added as subgraph when leaving the context manager's ``with``-block.

        Args:
            graph: An instance of the same kind (:class:`.Graph`, :class:`.Digraph`)
                   as the current graph (sole argument in non-with-block use).
            name: Subgraph name (``with``-block use).
            comment: Subgraph comment (``with``-block use).
            graph_attr: Subgraph-level attribute-value mapping (``with``-block use).
            node_attr: Node-level attribute-value mapping (``with``-block use).
            edge_attr: Edge-level attribute-value mapping (``with``-block use).
            body: Verbatim lines to add to the subgraph ``body`` (``with``-block use).

        See the :ref:`usage examples in the User Guide <subgraphs>`.

        .. note::
            If the ``name`` of the subgraph begins with ``'cluster'`` (all lowercase)
            the layout engine will treat it as a special cluster subgraph.
        """
        if graph is None:
            return SubgraphContext(self, {'name': name,
                                          'comment': comment,
                                          'graph_attr': graph_attr,
                                          'node_attr': node_attr,
                                          'edge_attr': edge_attr,
                                          'body': body})

        args = [name, comment, graph_attr, node_attr, edge_attr, body]
        if not all(a is None for a in args):
            raise ValueError('graph must be sole argument of subgraph()')

        if graph.directed != self.directed:
            raise ValueError('%r cannot add subgraph of different kind:'
                             ' %r' % (self, graph))

        lines = ['\t' + line for line in graph.__iter__(subgraph=True)]
        self.body.extend(lines)


class SubgraphContext(object):
    """Return a blank instance of the parent and add as subgraph on exit."""

    def __init__(self, parent, kwargs):
        self.parent = parent
        self.graph = parent.__class__(**kwargs)

    def __enter__(self):
        return self.graph

    def __exit__(self, type_, value, traceback):
        if type_ is None:
            self.parent.subgraph(self.graph)


class Graph(Dot):
    """Graph source code in the DOT language.

    Args:
        name: Graph name used in the source code.
        comment: Comment added to the first line of the source.
        filename: Filename for saving the source (defaults to ``name`` + ``'.gv'``).
        directory: (Sub)directory for source saving and rendering.
        format: Rendering output format (``'pdf'``, ``'png'``, ...).
        engine: Layout command used (``'dot'``, ``'neato'``, ...).
        encoding: Encoding for saving the source.
        graph_attr: Mapping of ``(attribute, value)`` pairs for the graph.
        node_attr: Mapping of ``(attribute, value)`` pairs set for all nodes.
        edge_attr: Mapping of ``(attribute, value)`` pairs set for all edges.
        body: Iterable of verbatim lines to add to the graph ``body``.
        strict (bool): Rendering should merge multi-edges.

    Note:
        All parameters are optional and can be changed under their
        corresponding attribute name after instance creation.
    """

    _head = 'graph %s{'
    _head_strict = 'strict %s' % _head
    _edge = '\t%s -- %s%s'
    _edge_plain = _edge % ('%s', '%s', '')

    @property
    def directed(self):
        """``False``"""
        return False


class Digraph(Dot):
    """Directed graph source code in the DOT language."""

    if Graph.__doc__ is not None:
        __doc__ += Graph.__doc__.partition('.')[2]

    _head = 'digraph %s{'
    _head_strict = 'strict %s' % _head
    _edge = '\t%s -> %s%s'
    _edge_plain = _edge % ('%s', '%s', '')

    @property
    def directed(self):
        """``True``"""
        return True
