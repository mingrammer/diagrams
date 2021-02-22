import contextvars
import html
import os
import uuid
from pathlib import Path
from typing import List, Union, Dict, Sequence

from graphviz import Digraph

# Global contexts for a diagrams and a cluster.
#
# These global contexts are for letting the clusters and nodes know
# where context they are belong to. So the all clusters and nodes does
# not need to specify the current diagrams or cluster via parameters.
__diagram = contextvars.ContextVar("diagrams")
__cluster = contextvars.ContextVar("cluster")


def getdiagram():
    return __diagram.get()


def setdiagram(diagram):
    __diagram.set(diagram)


def getcluster():
    try:
        return __cluster.get()
    except LookupError:
        return None


def setcluster(cluster):
    __cluster.set(cluster)

def new_init(cls, init):
    def reset_init(*args, **kwargs):
        cls.__init__ = init
    return reset_init

class _Cluster:
    __directions = ("TB", "BT", "LR", "RL")

    def __init__(self, name=None, **kwargs):
        self.dot = Digraph(name, **kwargs)
        self.depth = 0
        self.nodes = {}
        self.subgraphs = []

        try:
            self._parent = getcluster() or getdiagram()
        except LookupError:
            self._parent = None

    
    def __enter__(self):
        setcluster(self)
        return self

    def __exit__(self, *args):
        setcluster(self._parent)

        if not (self.nodes or self.subgraphs):
            return

        for node in self.nodes.values():
            self.dot.node(node.nodeid, label=node.label, **node._attrs)

        for subgraph in self.subgraphs:
            self.dot.subgraph(subgraph.dot)

        if self._parent:
            self._parent.remove_node(self.nodeid)
            self._parent.subgraph(self)

    def node(self, node: "Node") -> None:
        """Create a new node."""
        self.nodes[node.nodeid] = node
    
    def remove_node(self, nodeid: str) -> None:
        del self.nodes[nodeid]

    def subgraph(self, subgraph: "_Cluster") -> None:
        """Create a subgraph for clustering"""
        self.subgraphs.append(subgraph)
    
    @property
    def nodes_iter(self):
        if self.nodes:
            yield from self.nodes.values()
        if self.subgraphs:
            for subgraph in self.subgraphs:
                yield from subgraph.nodes_iter

    def _validate_direction(self, direction: str):
        direction = direction.upper()
        for v in self.__directions:
            if v == direction:
                return True
        return False

    def __str__(self) -> str:
        return str(self.dot)


class Diagram(_Cluster):
    __curvestyles = ("ortho", "curved")
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
        # TODO: check graphviz version to see if "imagepos" is available >= 2.40
        # https://github.com/xflr6/graphviz/blob/master/graphviz/backend.py#L248
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
    def __init__(
        self,
        name: str = "",
        filename: str = "",
        direction: str = "LR",
        curvestyle: str = "ortho",
        outformat: str = "png",
        show: bool = True,
        graph_attr: dict = {},
        node_attr: dict = {},
        edge_attr: dict = {},
    ):
        """Diagram represents a global diagrams context.

        :param name: Diagram name. It will be used for output filename if the
            filename isn't given.
        :param filename: The output filename, without the extension (.png).
            If not given, it will be generated from the name.
        :param direction: Data flow direction. Default is 'left to right'.
        :param curvestyle: Curve bending style. One of "ortho" or "curved".
        :param outformat: Output file format. Default is 'png'.
        :param show: Open generated image after save if true, just only save otherwise.
        :param graph_attr: Provide graph_attr dot config attributes.
        :param node_attr: Provide node_attr dot config attributes.
        :param edge_attr: Provide edge_attr dot config attributes.
        """

        self.name = name
        if not name and not filename:
          filename = "diagrams_image"
        elif not filename:
            filename = "_".join(self.name.split()).lower()
        self.filename = filename

        super().__init__(self.name, filename=self.filename)
        self.edges = {}

        # Set attributes.
        self.dot.attr(compound="true")
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

        if not self._validate_curvestyle(curvestyle):
            raise ValueError(f'"{curvestyle}" is not a valid curvestyle')
        self.dot.graph_attr["splines"] = curvestyle

        if not self._validate_outformat(outformat):
            raise ValueError(f'"{outformat}" is not a valid output format')
        self.outformat = outformat

        # Merge passed in attributes
        self.dot.graph_attr.update(graph_attr)
        self.dot.node_attr.update(node_attr)
        self.dot.edge_attr.update(edge_attr)

        self.show = show

    def __enter__(self):
        setdiagram(self)
        super().__enter__()
        return self
    
    def __exit__(self, *args):
        super().__exit__(*args)
        setdiagram(None)

        for (node1, node2), edge in self.edges.items():
            cluster_node1 = next(node1.nodes_iter, None)
            if cluster_node1:
                edge._attrs['ltail'] = node1.nodeid
                node1 = cluster_node1
            cluster_node2 = next(node2.nodes_iter, None)
            if cluster_node2:
                edge._attrs['lhead'] = node2.nodeid
                node2 = cluster_node2
            self.dot.edge(node1.nodeid, node2.nodeid, **edge.attrs)

        self.render()
        # Remove the graphviz file leaving only the image.
        os.remove(self.filename)

    def _repr_png_(self):
        return self.dot.pipe(format="png")

    def _validate_curvestyle(self, curvestyle: str) -> bool:
        curvestyle = curvestyle.lower()
        for v in self.__curvestyles:
            if v == curvestyle:
                return True
        return False

    def _validate_outformat(self, outformat: str) -> bool:
        outformat = outformat.lower()
        for v in self.__outformats:
            if v == outformat:
                return True
        return False

    def connect(self, node: "Node", node2: "Node", edge: "Edge") -> None:
        """Connect the two Nodes."""
        self.edges[(node, node2)] = edge

    def render(self) -> None:
        self.dot.render(format=self.outformat, view=self.show, quiet=True)


class Node(_Cluster):
    """Node represents a node for a specific backend service."""
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

    _provider = None
    _type = None

    _icon_dir = None
    _icon = None
    _icon_size = 30
    _direction = "LR"
    _height = 1.9

    # fmt: on

    def __new__(cls, *args, **kwargs):
        instance = object.__new__(cls)
        lazy = kwargs.pop('_no_init', False)
        if not lazy:
            return instance
        cls.__init__ = new_init(cls, cls.__init__)
        return instance

    def __init__(
        self,
        label: str = "",
        direction: str = None,
        icon: object = None,
        icon_size: int = None,
        **attrs: Dict
        ):
        """Node represents a system component.

        :param label: Node label.
        :param direction: Data flow direction. Default is "LR" (left to right).
        :param icon: Custom icon for tihs cluster. Must be a node class or reference.
        :param icon_size: The icon size when used as a Cluster. Default is 30.
        """
        # Generates an ID for identifying a node.
        self._id = self._rand_id()
        if isinstance(label, str):
            self.label = label
        elif isinstance(label, Sequence):
            self.label = "\n".join(label)
        else:
            self.label = str(label)

        super().__init__()

        if direction:
            if not self._validate_direction(direction):
                raise ValueError(f'"{direction}" is not a valid direction')
            self._direction = direction
        if icon:
            _node = icon(_no_init=True)
            self._icon = _node._icon
            self._icon_dir = _node._icon_dir
        if icon_size:
            self._icon_size = icon_size

        # fmt: off
        # If a node has an icon, increase the height slightly to avoid
        # that label being spanned between icon image and white space.
        # Increase the height by the number of new lines included in the label.
        padding = 0.4 * (self.label.count('\n'))
        icon_path = self._load_icon()
        self._attrs = {
            "shape": "none",
            "height": str(self._height + padding),
            "image": icon_path,
        } if icon_path else {}

        self._attrs['tooltip'] = (icon if icon else self).__class__.__name__

        # fmt: on
        self._attrs.update(attrs)

        # If a node is in the cluster context, add it to cluster.
        if not self._parent:
            raise EnvironmentError("Global diagrams context not set up")
        self._parent.node(self)

    def __enter__(self):
        super().__enter__()

        # Set attributes.
        for k, v in self._default_graph_attrs.items():
            self.dot.graph_attr[k] = v
        for k, v in self._attrs.items():
            self.dot.graph_attr[k] = v

        icon = self._load_icon()
        if icon:
            lines = iter(html.escape(self.label).split("\n"))
            self.dot.graph_attr["label"] = '<<TABLE border="0"><TR>' +\
                f'<TD fixedsize="true" width="{self._icon_size}" height="{self._icon_size}"><IMG SRC="{icon}"></IMG></TD>' +\
                f'<TD align="left">{next(lines)}</TD></TR>' +\
                ''.join(f'<TR><TD colspan="2" align="left">{line}</TD></TR>' for line in lines) +\
                '</TABLE>>'
        else:
            self.dot.graph_attr["label"] = self.label

        self.dot.graph_attr["rankdir"] = self._direction

        # Set cluster depth for distinguishing the background color
        self.depth = self._parent.depth + 1
        coloridx = self.depth % len(self.__bgcolors)
        self.dot.graph_attr["bgcolor"] = self.__bgcolors[coloridx]

        return self

    def __exit__(self, *args):
        super().__exit__(*args)
        self._id = "cluster_" + self.nodeid
        self.dot.name = self.nodeid

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
        """ Called for [Nodes] and [Edges] - Self because list don't have __sub__ operators. """
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
        if not isinstance(node, Edge):
            ValueError(f"{node} is not a valid Edge")
        # An edge must be added on the global diagrams, not a cluster.
        getdiagram().connect(self, node, edge)
        return node

    @staticmethod
    def _rand_id():
        return uuid.uuid4().hex

    def _load_icon(self):
        if self._icon and self._icon_dir:
            basedir = Path(os.path.abspath(os.path.dirname(__file__)))
            return os.path.join(basedir.parent, self._icon_dir, self._icon)
        return None


class Edge:
    """Edge represents an edge between two nodes."""

    _default_edge_attrs = {
        "fontcolor": "#2D3436",
        "fontname": "Sans-Serif",
        "fontsize": "13",
    }

    def __init__(
        self,
        node: "Node" = None,
        forward: bool = False,
        reverse: bool = False,
        label: str = "",
        color: str = "",
        style: str = "",
        **attrs: Dict,
    ):
        """Edge represents an edge between two nodes.

        :param node: Parent node.
        :param forward: Points forward.
        :param reverse: Points backward.
        :param label: Edge label.
        :param color: Edge color.
        :param style: Edge style.
        :param attrs: Other edge attributes
        """
        if node is not None:
            assert isinstance(node, Node)

        self.node = node
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
            self._attrs["tooltip"] = label
        if color:
            self._attrs["color"] = color
        if style:
            self._attrs["style"] = style
        self._attrs.update(attrs)

    def __sub__(self, other: Union["Node", "Edge", List["Node"]]):
        """Implement Self - Node or Edge and Self - [Nodes]"""
        return self.connect(other)

    def __rsub__(self, other: Union[List["Node"], List["Edge"]]) -> List["Edge"]:
        """Called for [Nodes] or [Edges] - Self because list don't have __sub__ operators."""
        return self.append(other)

    def __rshift__(self, other: Union["Node", "Edge", List["Node"]]):
        """Implements Self >> Node or Edge and Self >> [Nodes]."""
        self.forward = True
        return self.connect(other)

    def __lshift__(self, other: Union["Node", "Edge", List["Node"]]):
        """Implements Self << Node or Edge and Self << [Nodes]."""
        self.reverse = True
        return self.connect(other)

    def __rrshift__(self, other: Union[List["Node"], List["Edge"]]) -> List["Edge"]:
        """Called for [Nodes] or [Edges] >> Self because list of Edges don't have __rshift__ operators."""
        return self.append(other, forward=True)

    def __rlshift__(self, other: Union[List["Node"], List["Edge"]]) -> List["Edge"]:
        """Called for [Nodes] or [Edges] << Self because list of Edges don't have __lshift__ operators."""
        return self.append(other, reverse=True)

    def append(self, other: Union[List["Node"], List["Edge"]], forward=None, reverse=None) -> List["Edge"]:
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

    def connect(self, other: Union["Node", "Edge", List["Node"]]):
        if isinstance(other, list):
            for node in other:
                self.node.connect(node, self)
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


Group = Cluster = Node
