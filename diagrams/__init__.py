import contextvars
import os
from hashlib import md5
from pathlib import Path
from random import getrandbits
from typing import List, Union

from graphviz import Digraph

__version__ = "0.1.0"

# Global context for a diagrams and a cluster.
#
# Theses global contexts are for letting the clusters and nodes know
# where context they are belong to. So the all clusters and nodes does
# not need to specify the current diagrams or cluster via parameters.
__diagram = contextvars.ContextVar("diagrams")
__cluster = contextvars.ContextVar("cluster")


def getdiagram():
    try:
        return __diagram.get()
    except LookupError:
        return None


def setdiagram(diagram):
    __diagram.set(diagram)


def getcluster():
    try:
        return __cluster.get()
    except LookupError:
        return None


def setcluster(cluster):
    __cluster.set(cluster)


class Diagram:
    __directions = ("TB", "BT", "LR", "RL")
    __outformats = ("png", "jpg", "svg", "pdf")

    # fmt: off
    _default_graph_attrs = {
        "pad": "2.0",
        "splines": "ortho",
        "nodesep": "0.60",
        "ranksep": "0.75",
        "fontname": "Sans-Serif",
        "fontsize": "15",
        "fontcolor": "#2D3436",
    }
    _default_node_attrs = {
        "shape": "box",
        "style": "rounded",
        "fixedsize": "true",
        "width": "1.4",
        "height": "1.4",
        "labelloc": "b",
        # imagepos attribute is not backward compatible
        # "imagepos": "tc",
        "imagescale": "true",
        "fontname": "Sans-Serif",
        "fontsize": "13",
        "fontcolor": "#2D3436",
    }
    _default_edge_attrs = {
        "color": "#7B8894",
    }

    # fmt: on

    # TODO: Label position option
    # TODO: Save directory option (filename + directory?)
    def __init__(self, name: str = "", direction: str = "LR", outformat: str = "png", show: bool = True):
        """Diagram represents a global diagrams context.

        :param name: Diagram name. It will be used for output filename.
        :param direction: Data flow direction. Default is 'left to right'.
        :param outformat: Output file format. Default is 'png'.
        :param show: Open generated image after save if true, just only save otherwise.
        """
        self.name = name

        self.filename = "_".join(self.name.split()).lower()
        self.dot = Digraph(self.name, filename=self.filename)

        # Set attributes.
        for k, v in self._default_graph_attrs.items():
            self.dot.graph_attr[k] = v
        self.dot.graph_attr["label"] = self.name
        for k, v in self._default_node_attrs.items():
            self.dot.node_attr[k] = v
        for k, v in self._default_edge_attrs.items():
            self.dot.edge_attr[k] = v

        if not self._validate_direction(direction):
            raise ValueError(f'"{direction}" is not a valid direction')
        self.dot.graph_attr["rankdir"] = direction

        if not self._validate_outformat(outformat):
            raise ValueError(f'"{outformat}" is not a valid output format')
        self.outformat = outformat

        self.show = show

    def __enter__(self):
        setdiagram(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.render()
        # Remove the graphviz file leaving only the image.
        os.remove(self.filename)
        setdiagram(None)

    def _validate_direction(self, direction: str) -> bool:
        direction = direction.upper()
        for v in self.__directions:
            if v == direction:
                return True
        return False

    def _validate_outformat(self, outformat: str) -> bool:
        outformat = outformat.lower()
        for v in self.__outformats:
            if v == outformat:
                return True
        return False

    def node(self, hashid: str, label: str, **attrs) -> None:
        """Create a new node."""
        self.dot.node(hashid, label=label, **attrs)

    def connect(self, node: "Node", node2: "Node", directed=True) -> None:
        """Connect the two Nodes."""
        attrs = {"dir": "none"} if not directed else {}
        self.dot.edge(node.hashid, node2.hashid, **attrs)

    def reverse(self, node: "Node", node2: "Node", directed=True) -> None:
        """Connect the two Nodes in reverse direction."""
        attrs = {"dir": "none"} if not directed else {"dir": "back"}
        self.dot.edge(node.hashid, node2.hashid, **attrs)

    def subgraph(self, dot: Digraph) -> None:
        """Create a subgraph for clustering"""
        self.dot.subgraph(dot)

    def render(self) -> None:
        self.dot.render(format=self.outformat, view=self.show)


class Cluster:
    __directions = ("TB", "BT", "LR", "RL")
    __bgcolors = ("#E5F5FD", "#EBF3E7", "#ECE8F6", "#FDF7E3")

    # fmt: off
    _default_graph_attrs = {
        "shape": "box",
        "style": "rounded",
        "labeljust": "l",
        "pencolor": "#AEB6BE",
        "fontname": "Sans-Serif",
        "fontsize": "12",
    }

    # fmt: on

    # FIXME:
    #  Cluster direction does not work now. Graphviz couldn't render
    #  correctly for a subgraph that has a different rank direction.
    def __init__(self, label: str = "cluster", direction: str = "LR"):
        """Cluster represents a cluster context.

        :param label: Cluster label.
        :param direction: Data flow direction. Default is 'left to right'.
        """
        self.label = label
        self.name = "cluster_" + self.label

        self.dot = Digraph(self.name)

        # Set attributes.
        for k, v in self._default_graph_attrs.items():
            self.dot.graph_attr[k] = v
        self.dot.graph_attr["label"] = self.label

        if not self._validate_direction(direction):
            raise ValueError(f'"{direction}" is not a valid direction')
        self.dot.graph_attr["rankdir"] = direction

        # Node must be belong to a diagrams.
        self._diagram = getdiagram()
        if self._diagram is None:
            raise EnvironmentError("Global diagrams context not set up")
        self._parent = getcluster()

        # Set cluster depth for distinguishing the background color
        self.depth = self._parent.depth + 1 if self._parent else 0
        coloridx = self.depth % len(self.__bgcolors)
        self.dot.graph_attr["bgcolor"] = self.__bgcolors[coloridx]

    def __enter__(self):
        setcluster(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._parent:
            self._parent.subgraph(self.dot)
        else:
            self._diagram.subgraph(self.dot)
        setcluster(self._parent)

    def _validate_direction(self, direction: str):
        direction = direction.upper()
        for v in self.__directions:
            if v == direction:
                return True
        return False

    def node(self, hashid: str, label: str, **attrs) -> None:
        """Create a new node in the cluster."""
        self.dot.node(hashid, label=label, **attrs)

    def subgraph(self, dot: Digraph) -> None:
        self.dot.subgraph(dot)


class Node:
    """Node represents a node for a specific backend service."""

    _provider = None
    _type = None

    _icon_dir = None
    _icon = None

    def __init__(self, label: str = ""):
        """Node represents a system component.

        :param label: Node label.
        """
        # Generates a hash for identifying a node.
        self._hash = self._rand_hash()
        self.label = label

        # fmt: off
        # If a node has an icon, increase the height slightly to avoid
        # that label being spanned between icon image and white space.
        self.attrs = {
            "shape": "none",
            "height": "1.9",
            "image": self._load_icon(),
        } if self._icon else {}
        # fmt: on

        # Node must be belong to a diagrams.
        self._diagram = getdiagram()
        if self._diagram is None:
            raise EnvironmentError("Global diagrams context not set up")
        self._cluster = getcluster()

        # If a node is in the cluster context, add it to cluster.
        if self._cluster:
            self._cluster.node(self._hash, self.label, **self.attrs)
        else:
            self._diagram.node(self._hash, self.label, **self.attrs)

    def __repr__(self):
        _name = self.__class__.__name__
        return f"<{self._provider}.{self._type}.{_name}>"

    def __sub__(self, other: Union["Node", List["Node"]]):
        """Implement Self - Node and Self - [Nodes]"""
        if not isinstance(other, list):
            return self.connect(other, directed=False)
        for node in other:
            self.connect(node, directed=False)
        return other

    def __rsub__(self, other: List["Node"]):
        """
        Called for [Nodes] - Self because list of Nodes don't have
        __sub__ operators.
        """
        self.__sub__(other)
        return self

    def __rshift__(self, other: Union["Node", List["Node"]]):
        """Implements Self >> Node and Self >> [Nodes]."""
        if not isinstance(other, list):
            return self.connect(other)
        for node in other:
            self.connect(node)
        return other

    def __lshift__(self, other: Union["Node", List["Node"]]):
        """Implements Self << Node and Self << [Nodes]."""
        if not isinstance(other, list):
            return self.reverse(other)
        for node in other:
            self.reverse(node)
        return other

    def __rrshift__(self, other: List["Node"]):
        """
        Called for [Nodes] >> Self because list of Nodes don't have
        __rshift__ operators.
        """
        for node in other:
            node.connect(self)
        return self

    def __rlshift__(self, other: List["Node"]):
        """
        Called for [Nodes] << Self because list of Nodes don't have
        __lshift__ operators.
        """
        for node in other:
            node.reverse(self)
        return self

    @property
    def hashid(self):
        return self._hash

    # TODO: option for adding flow description to the connection edge
    def connect(self, node: "Node", directed=True):
        """Connect to other node.

        :param node: Other node instance.
        :param directed: Whether the flow is directed or not.
        :return: Connected node.
        """
        if not isinstance(node, Node):
            ValueError(f"{node} is not a valid Node")
        # An edge must be added on the global diagrams, not a cluster.
        self._diagram.connect(self, node, directed)
        return node

    def reverse(self, node: "Node", directed=True):
        """Connect to other node in reverse direction.

        :param node: Other node instance.
        :param directed: Whether the flow is directed or not.
        :return: Connected node.
        """
        if not isinstance(node, Node):
            ValueError(f"{node} is not a valid Node")
        # An edge must be added on the global diagrams, not a cluster.
        self._diagram.reverse(self, node, directed)
        return node

    @staticmethod
    def _rand_hash():
        return md5(getrandbits(64).to_bytes(64, "big")).hexdigest()

    def _load_icon(self):
        basedir = Path(os.path.abspath(os.path.dirname(__file__)))
        return os.path.join(basedir.parent, self._icon_dir, self._icon)


Group = Cluster
