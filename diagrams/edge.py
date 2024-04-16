from . import node
from typing import List, Union, Dict

class Edge:
    """Edge represents an edge between two nodes."""

    _default_edge_attrs = {
        "fontcolor": "#2D3436",
        "fontname": "Sans-Serif",
        "fontsize": "13",
    }

    def __init__(
        self,
        n: "node.Node" = None,
        forward: bool = False,
        reverse: bool = False,
        label: str = "",
        color: str = "",
        style: str = "",
        **attrs: Dict,
    ):
        """Edge represents an edge between two nodes.

        :param n: Parent node.
        :param forward: Points forward.
        :param reverse: Points backward.
        :param label: Edge label.
        :param color: Edge color.
        :param style: Edge style.
        :param attrs: Other edge attributes
        """
        if n is not None:
            assert isinstance(n, node.Node)

        self.node = n
        self.forward = forward
        self.reverse = reverse

        self._attrs = {}

        # Set attributes.
        for k, v in self._default_edge_attrs.items():
            self._attrs[k] = v

        if label:
            # Graphviz complaining about using label for edges, so replace it with xlabel.
            # Update: xlabel option causes the misaligned label position: https://github.com/mingrammer/diagrams/issues/83
            self._attrs["label"] = label
        if color:
            self._attrs["color"] = color
        if style:
            self._attrs["style"] = style
        self._attrs.update(attrs)

    def __sub__(self, other: Union["node.Node", "Edge", List["node.Node"]]):
        """Implement Self - Node or Edge and Self - [Nodes]"""
        return self.connect(other)

    def __rsub__(self, other: Union[List["node.Node"], List["Edge"]]) -> List["Edge"]:
        """Called for [Nodes] or [Edges] - Self because list don't have __sub__ operators."""
        return self.append(other)

    def __rshift__(self, other: Union["node.Node", "Edge", List["node.Node"]]):
        """Implements Self >> Node or Edge and Self >> [Nodes]."""
        self.forward = True
        return self.connect(other)

    def __lshift__(self, other: Union["node.Node", "Edge", List["node.Node"]]):
        """Implements Self << Node or Edge and Self << [Nodes]."""
        self.reverse = True
        return self.connect(other)

    def __rrshift__(self, other: Union[List["node.Node"], List["Edge"]]) -> List["Edge"]:
        """Called for [Nodes] or [Edges] >> Self because list of Edges don't have __rshift__ operators."""
        return self.append(other, forward=True)

    def __rlshift__(self, other: Union[List["node.Node"], List["Edge"]]) -> List["Edge"]:
        """Called for [Nodes] or [Edges] << Self because list of Edges don't have __lshift__ operators."""
        return self.append(other, reverse=True)

    def append(self, other: Union[List["node.Node"], List["Edge"]], forward=None, reverse=None) -> List["Edge"]:
        result = []
        for o in other:
            if isinstance(o, Edge):
                o.forward = forward if forward else o.forward
                o.reverse = forward if forward else o.reverse
                self._attrs = o.attrs.copy()
                result.append(o)
            else:
                result.append(Edge(o, forward=forward, reverse=reverse, **self._attrs))
        return result

    def connect(self, other: Union["node.Node", "Edge", List["node.Node"]]):
        if isinstance(other, list):
            for n in other:
                self.node.connect(n, self)
            return other
        elif isinstance(other, Edge):
            self._attrs = other._attrs.copy()
            return self
        else:
            if self.node is not None:
                return self.node.connect(other, self)
            else:
                self.node = other
                return self

    @property
    def attrs(self) -> Dict:
        if self.forward and self.reverse:
            direction = "both"
        elif self.forward:
            direction = "forward"
        elif self.reverse:
            direction = "back"
        else:
            direction = "none"
        return {**self._attrs, "dir": direction}