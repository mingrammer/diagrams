import os
import uuid
from pathlib import Path
from typing import List, Union, Dict
from .edge import Edge
from .utils import getcluster, getdiagram

class Node:
    """Node represents a node for a specific backend service."""

    _provider = None
    _type = None

    _icon_dir = None
    _icon = None

    _height = 1.9

    def __init__(self, label: str = "", *, nodeid: str = None, **attrs: Dict):
        """Node represents a system component.

        :param label: Node label.
        """
        # Generates an ID for identifying a node, unless specified
        self._id = nodeid or self._rand_id()
        self.label = label

        # Node must be belong to a diagrams.
        self._diagram = getdiagram()
        if self._diagram is None:
            raise EnvironmentError("Global diagrams context not set up")

        if self._diagram.autolabel:
            prefix = self.__class__.__name__
            if self.label:
                self.label = prefix + "\n" + self.label
            else:
                self.label = prefix

        # fmt: off
        # If a node has an icon, increase the height slightly to avoid
        # that label being spanned between icon image and white space.
        # Increase the height by the number of new lines included in the label.
        padding = 0.4 * (self.label.count('\n'))
        self._attrs = {
            "shape": "none",
            "height": str(self._height + padding),
            "image": self._load_icon(),
        } if self._icon else {}

        # fmt: on
        self._attrs.update(attrs)

        self._cluster = getcluster()

        # If a node is in the cluster context, add it to cluster.
        if self._cluster:
            self._cluster.node(self._id, self.label, **self._attrs)
        else:
            self._diagram.node(self._id, self.label, **self._attrs)

    def __repr__(self):
        _name = self.__class__.__name__
        return f"<{self._provider}.{self._type}.{_name}>"

    def __sub__(self, other: Union["Node", List["Node"], "Edge"]):
        """Implement Self - Node, Self - [Nodes] and Self - Edge."""
        if isinstance(other, list):
            for node in other:
                self.connect(node, Edge(self))
            return other
        elif isinstance(other, Node):
            return self.connect(other, Edge(self))
        else:
            other.node = self
            return other

    def __rsub__(self, other: Union[List["Node"], List["Edge"]]):
        """Called for [Nodes] and [Edges] - Self because list don't have __sub__ operators."""
        for o in other:
            if isinstance(o, Edge):
                o.connect(self)
            else:
                o.connect(self, Edge(self))
        return self

    def __rshift__(self, other: Union["Node", List["Node"], "Edge"]):
        """Implements Self >> Node, Self >> [Nodes] and Self Edge."""
        if isinstance(other, list):
            for node in other:
                self.connect(node, Edge(self, forward=True))
            return other
        elif isinstance(other, Node):
            return self.connect(other, Edge(self, forward=True))
        else:
            other.forward = True
            other.node = self
            return other

    def __lshift__(self, other: Union["Node", List["Node"], "Edge"]):
        """Implements Self << Node, Self << [Nodes] and Self << Edge."""
        if isinstance(other, list):
            for node in other:
                self.connect(node, Edge(self, reverse=True))
            return other
        elif isinstance(other, Node):
            return self.connect(other, Edge(self, reverse=True))
        else:
            other.reverse = True
            return other.connect(self)

    def __rrshift__(self, other: Union[List["Node"], List["Edge"]]):
        """Called for [Nodes] and [Edges] >> Self because list don't have __rshift__ operators."""
        for o in other:
            if isinstance(o, Edge):
                o.forward = True
                o.connect(self)
            else:
                o.connect(self, Edge(self, forward=True))
        return self

    def __rlshift__(self, other: Union[List["Node"], List["Edge"]]):
        """Called for [Nodes] << Self because list of Nodes don't have __lshift__ operators."""
        for o in other:
            if isinstance(o, Edge):
                o.reverse = True
                o.connect(self)
            else:
                o.connect(self, Edge(self, reverse=True))
        return self

    @property
    def nodeid(self):
        return self._id

    # TODO: option for adding flow description to the connection edge
    def connect(self, node: "Node", edge: "Edge"):
        """Connect to other node.

        :param node: Other node instance.
        :param edge: Type of the edge.
        :return: Connected node.
        """
        if not isinstance(node, Node):
            ValueError(f"{node} is not a valid Node")
        if not isinstance(edge, Edge):
            ValueError(f"{edge} is not a valid Edge")
        # An edge must be added on the global diagrams, not a cluster.
        self._diagram.connect(self, node, edge)
        return node

    @staticmethod
    def _rand_id():
        return uuid.uuid4().hex

    def _load_icon(self):
        basedir = Path(os.path.abspath(os.path.dirname(__file__)))
        return os.path.join(basedir.parent, self._icon_dir, self._icon)
