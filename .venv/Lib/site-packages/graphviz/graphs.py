r"""Assemble DOT source code objects.

Example:
    >>> doctest_mark_exe()

    >>> import graphviz
    >>> dot = graphviz.Graph(comment='Mønti Pythøn ik den Hølie Grailen')

    >>> dot.node('Møøse')
    >>> dot.node('trained_by', 'trained by')
    >>> dot.node('tutte', 'TUTTE HERMSGERVORDENBROTBORDA')

    >>> dot.edge('Møøse', 'trained_by')
    >>> dot.edge('trained_by', 'tutte')

    >>> dot.node_attr['shape'] = 'rectangle'

    >>> print(dot.source)  #doctest: +NORMALIZE_WHITESPACE
    // Mønti Pythøn ik den Hølie Grailen
    graph {
        node [shape=rectangle]
        "Møøse"
        trained_by [label="trained by"]
        tutte [label="TUTTE HERMSGERVORDENBROTBORDA"]
        "Møøse" -- trained_by
        trained_by -- tutte
    }

    >>> dot.render('doctest-output/m00se.gv').replace('\\', '/')
    'doctest-output/m00se.gv.pdf'
"""

import typing

from .encoding import DEFAULT_ENCODING
from . import _tools
from . import dot
from . import jupyter_integration
from . import piping
from . import rendering
from . import unflattening

__all__ = ['Graph', 'Digraph']


class BaseGraph(dot.Dot,
                rendering.Render,
                jupyter_integration.JupyterIntegration, piping.Pipe,
                unflattening.Unflatten):
    """Dot language creation and source code rendering."""

    @_tools.deprecate_positional_args(supported_number=2)
    def __init__(self, name: typing.Optional[str] = None,
                 comment: typing.Optional[str] = None,
                 filename=None, directory=None,
                 format: typing.Optional[str] = None,
                 engine: typing.Optional[str] = None,
                 encoding: typing.Optional[str] = DEFAULT_ENCODING,
                 graph_attr=None, node_attr=None, edge_attr=None,
                 body=None,
                 strict: bool = False, *,
                 renderer: typing.Optional[str] = None,
                 formatter: typing.Optional[str] = None) -> None:
        if filename is None and name is not None:
            filename = f'{name}.{self._default_extension}'

        super().__init__(name=name, comment=comment,
                         graph_attr=graph_attr,
                         node_attr=node_attr, edge_attr=edge_attr,
                         body=body, strict=strict,
                         filename=filename, directory=directory,
                         encoding=encoding,
                         format=format, engine=engine,
                         renderer=renderer, formatter=formatter)

    @property
    def source(self) -> str:
        """The generated DOT source code as string."""
        return ''.join(self)


class Graph(dot.GraphSyntax, BaseGraph):
    """Graph source code in the DOT language.

    Args:
        name: Graph name used in the source code.
        comment: Comment added to the first line of the source.
        filename: Filename for saving the source
            (defaults to ``name`` + ``'.gv'``).
        directory: (Sub)directory for source saving and rendering.
        format: Rendering output format (``'pdf'``, ``'png'``, ...).
        engine: Layout command used (``'dot'``, ``'neato'``, ...).
        renderer: Output renderer used (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter used (``'cairo'``, ``'gd'``, ...).
        encoding: Encoding for saving the source.
        graph_attr: Mapping of ``(attribute, value)`` pairs for the graph.
        node_attr: Mapping of ``(attribute, value)`` pairs set for all nodes.
        edge_attr: Mapping of ``(attribute, value)`` pairs set for all edges.
        body: Iterable of verbatim lines (including their final newline)
            to add to the graph ``body``.
        strict (bool): Rendering should merge multi-edges.

    Note:
        All parameters are `optional` and can be changed under their
        corresponding attribute name after instance creation.
    """

    @property
    def directed(self) -> bool:
        """``False``"""
        return False


class Digraph(dot.DigraphSyntax, BaseGraph):
    """Directed graph source code in the DOT language."""

    if Graph.__doc__ is not None:
        __doc__ += Graph.__doc__.partition('.')[2]

    @property
    def directed(self) -> bool:
        """``True``"""
        return True
