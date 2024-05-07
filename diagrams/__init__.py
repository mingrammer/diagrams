import os
import uuid
from contextvars import ContextVar
from pathlib import Path
from typing import Any, AnyStr, cast, Dict, List, Mapping, Optional, Tuple, Type, Union
from types import TracebackType

from graphviz import Digraph  # type: ignore[import]

# Global contexts for a diagrams and a cluster.
#
# These global contexts are for letting the clusters and nodes know
# where context they are belong to. So the all clusters and nodes does
# not need to specify the current diagrams or cluster via parameters.
__diagram: ContextVar[Optional["Diagram"]] = ContextVar("diagrams")
__cluster: ContextVar[Optional["Cluster"]] = ContextVar("cluster")


def getdiagram() -> Optional["Diagram"]:
    return __diagram.get(None)


def setdiagram(diagram: Optional["Diagram"]) -> None:
    __diagram.set(diagram)


def getcluster() -> Optional["Cluster"]:
    return __cluster.get(None)


def setcluster(cluster: Optional["Cluster"]) -> None:
    __cluster.set(cluster)


class Diagram:
    __directions: Tuple[str, ...] = ("TB", "BT", "LR", "RL")
    __curvestyles: Tuple[str, ...] = ("ortho", "curved")
    __outformats: Tuple[str, ...] = ("png", "jpg", "svg", "pdf", "dot")

    # fmt: off
    _default_graph_attrs: Mapping[str, str] = {
        "pad": "2.0",
        "splines": "ortho",
        "nodesep": "0.60",
        "ranksep": "0.75",
        "fontname": "Sans-Serif",
        "fontsize": "15",
        "fontcolor": "#2D3436",
    }
    _default_node_attrs: Mapping[str, str] = {
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
    _default_edge_attrs: Mapping[str, str] = {
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
        outformat: Union[List[str], str] = "png",
        autolabel: bool = False,
        show: bool = True,
        strict: bool = False,
        graph_attr: Optional[Mapping[str, Any]] = None,
        node_attr: Optional[Mapping[str, Any]] = None,
        edge_attr: Optional[Mapping[str, Any]] = None,
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
        :param strict: Rendering should merge multi-edges.
        """
        if graph_attr is None:
            graph_attr = {}
        if node_attr is None:
            node_attr = {}
        if edge_attr is None:
            edge_attr = {}
        self.name = name
        if not name and not filename:
            filename = "diagrams_image"
        elif not filename:
            filename = "_".join(self.name.split()).lower()
        self.filename: str = filename
        self.dot: Digraph = Digraph(self.name, filename=self.filename, strict=strict)

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

        if not self._validate_curvestyle(curvestyle):
            raise ValueError(f'"{curvestyle}" is not a valid curvestyle')
        self.dot.graph_attr["splines"] = curvestyle

        if isinstance(outformat, list):
            for one_format in outformat:
                if not self._validate_outformat(one_format):
                    raise ValueError(f'"{one_format}" is not a valid output format')
        else:
            if not self._validate_outformat(outformat):
                raise ValueError(f'"{outformat}" is not a valid output format')
        self.outformat: Union[List[str], str] = outformat

        # Merge passed in attributes
        self.dot.graph_attr.update(graph_attr)
        self.dot.node_attr.update(node_attr)
        self.dot.edge_attr.update(edge_attr)

        self.show = show
        self.autolabel = autolabel

    def __str__(self) -> str:
        return str(self.dot)

    def __enter__(self) -> "Diagram":
        setdiagram(self)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.render()
        # Remove the graphviz file leaving only the image.
        os.remove(self.filename)
        setdiagram(None)

    def _repr_png(self) -> AnyStr:
        return cast(AnyStr, self.dot.pipe(format="png"))

    def _validate_direction(self, direction: str) -> bool:
        return direction.upper() in self.__directions

    def _validate_curvestyle(self, curvestyle: str) -> bool:
        return curvestyle.lower() in self.__curvestyles

    def _validate_outformat(self, outformat: str) -> bool:
        return outformat.lower() in self.__outformats

    def node(self, nodeid: str, label: str, **attrs: Dict[Any, Any]) -> None:
        """Create a new node."""
        self.dot.node(nodeid, label=label, **attrs)

    def connect(self, node: "Node", node2: "Node", edge: "Edge") -> None:
        """Connect the two Nodes."""
        self.dot.edge(node.nodeid, node2.nodeid, **edge.attrs)

    def subgraph(self, dot: Digraph) -> None:
        """Create a subgraph for clustering"""
        self.dot.subgraph(dot)

    def render(self) -> None:
        if isinstance(self.outformat, list):
            for one_format in self.outformat:
                self.dot.render(format=one_format, view=self.show, quiet=True)
        else:
            self.dot.render(format=self.outformat, view=self.show, quiet=True)


class Cluster:
    __directions: Tuple[str, ...] = ("TB", "BT", "LR", "RL")
    __bgcolors: Tuple[str, ...] = ("#E5F5FD", "#EBF3E7", "#ECE8F6", "#FDF7E3")

    # fmt: off
    _default_graph_attrs: Mapping[str, str] = {
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
    def __init__(
        self,
        label: str = "cluster",
        direction: str = "LR",
        graph_attr: Optional[Mapping[str, Any]] = None,
    ):
        """Cluster represents a cluster context.

        :param label: Cluster label.
        :param direction: Data flow direction. Default is 'left to right'.
        :param graph_attr: Provide graph_attr dot config attributes.
        """
        if graph_attr is None:
            graph_attr = {}
        self.label: str = label
        self.name: str = f"cluster_{self.label}"

        self.dot: Digraph = Digraph(self.name)

        # Set attributes.
        for k, v in self._default_graph_attrs.items():
            self.dot.graph_attr[k] = v
        self.dot.graph_attr["label"] = self.label

        if not self._validate_direction(direction):
            raise ValueError(f'"{direction}" is not a valid direction')
        self.dot.graph_attr["rankdir"] = direction

        # Node must be belong to a diagrams.
        diagram = getdiagram()
        if diagram is None:
            raise EnvironmentError("Global diagrams context not set up")
        self._diagram: Diagram = diagram
        self._parent: Optional["Cluster"] = getcluster()

        # Set cluster depth for distinguishing the background color
        self.depth: int = self._parent.depth + 1 if self._parent else 0
        coloridx = self.depth % len(self.__bgcolors)
        self.dot.graph_attr["bgcolor"] = self.__bgcolors[coloridx]

        # Merge passed in attributes
        self.dot.graph_attr.update(graph_attr)

    def __enter__(self) -> "Cluster":
        setcluster(self)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if self._parent:
            self._parent.subgraph(self.dot)
        else:
            self._diagram.subgraph(self.dot)
        setcluster(self._parent)

    def _validate_direction(self, direction: str) -> bool:
        return direction.upper() in self.__directions

    def node(self, nodeid: str, label: str, **attrs: Dict[Any, Any]) -> None:
        """Create a new node in the cluster."""
        self.dot.node(nodeid, label=label, **attrs)

    def subgraph(self, dot: Digraph) -> None:
        self.dot.subgraph(dot)


class Node:
    """Node represents a node for a specific backend service."""

    _provider: Optional[str] = None
    _type: Optional[str] = None

    _icon_dir: Optional[str] = None
    _icon: Optional[str] = None

    _height: float = 1.9

    def __init__(self, label: str = "", *, nodeid: Optional[str] = None, **attrs: Dict[Any, Any]):
        """Node represents a system component.

        :param label: Node label.
        """
        # Generates an ID for identifying a node, unless specified
        self._id: str = nodeid or self._rand_id()
        self.label: str = label

        # Node must be belong to a diagrams.
        diagram = getdiagram()
        if diagram is None:
            raise EnvironmentError("Global diagrams context not set up")
        self._diagram: Diagram = diagram

        if self._diagram.autolabel:
            prefix = self.__class__.__name__
            if self.label:
                self.label = f"{prefix}\n{self.label}"
            else:
                self.label = prefix

        # fmt: off
        # If a node has an icon, increase the height slightly to avoid
        # that label being spanned between icon image and white space.
        # Increase the height by the number of new lines included in the label.
        padding = 0.4 * (self.label.count('\n'))
        icon = self._load_icon()
        self._attrs: Dict[str, Any] = {
            "shape": "none",
            "height": str(self._height + padding),
            "image": icon,
        } if icon is not None else {}

        # fmt: on
        self._attrs.update(attrs)

        self._cluster: Optional[Cluster] = getcluster()

        # If a node is in the cluster context, add it to cluster.
        if self._cluster:
            self._cluster.node(self._id, self.label, **self._attrs)
        else:
            self._diagram.node(self._id, self.label, **self._attrs)

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return f"<{self._provider}.{self._type}.{name}>"

    def __sub__(self, other: Union["Node", List["Node"], "Edge"]) -> Union["Node", List["Node"], "Edge"]:
        """Implement Self - Node, Self - [Nodes] and Self - Edge."""
        if isinstance(other, list):
            for node in other:
                self.connect(node, Edge(self))
            return other
        if isinstance(other, Node):
            return self.connect(other, Edge(self))
        other.node = self
        return other

    def __rsub__(self, other: Union[List["Node"], List["Edge"]]) -> "Node":
        """Called for [Nodes] and [Edges] - Self because list don't have __sub__ operators."""
        for o in other:
            if isinstance(o, Edge):
                o.connect(self)
            else:
                o.connect(self, Edge(self))
        return self

    def __rshift__(self, other: Union["Node", List["Node"], "Edge"]) -> Union["Node", List["Node"], "Edge"]:
        """Implements Self >> Node, Self >> [Nodes] and Self Edge."""
        if isinstance(other, list):
            for node in other:
                self.connect(node, Edge(self, forward=True))
            return other
        if isinstance(other, Node):
            return self.connect(other, Edge(self, forward=True))
        other.forward = True
        other.node = self
        return other

    def __lshift__(self, other: Union["Node", List["Node"], "Edge"]) -> Union["Node", List["Node"], "Edge"]:
        """Implements Self << Node, Self << [Nodes] and Self << Edge."""
        if isinstance(other, list):
            for node in other:
                self.connect(node, Edge(self, reverse=True))
            return other
        if isinstance(other, Node):
            return self.connect(other, Edge(self, reverse=True))
        other.reverse = True
        return other.connect(self)

    def __rrshift__(self, other: Union[List["Node"], List["Edge"]]) -> "Node":
        """Called for [Nodes] and [Edges] >> Self because list don't have __rshift__ operators."""
        for o in other:
            if isinstance(o, Edge):
                o.forward = True
                o.connect(self)
            else:
                o.connect(self, Edge(self, forward=True))
        return self

    def __rlshift__(self, other: Union[List["Node"], List["Edge"]]) -> "Node":
        """Called for [Nodes] << Self because list of Nodes don't have __lshift__ operators."""
        for o in other:
            if isinstance(o, Edge):
                o.reverse = True
                o.connect(self)
            else:
                o.connect(self, Edge(self, reverse=True))
        return self

    @property
    def nodeid(self) -> str:
        return self._id

    # TODO: option for adding flow description to the connection edge
    def connect(self, node: "Node", edge: "Edge") -> "Node":
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
    def _rand_id() -> str:
        return uuid.uuid4().hex

    def _load_icon(self) -> Optional[str]:
        if self._icon_dir is None or self._icon is None:
            return None
        return str(Path(__file__).parent / self._icon_dir / self._icon)


class Edge:
    """Edge represents an edge between two nodes."""

    _default_edge_attrs: Mapping[str, str] = {
        "fontcolor": "#2D3436",
        "fontname": "Sans-Serif",
        "fontsize": "13",
    }

    def __init__(
        self,
        node: Optional["Node"] = None,
        forward: bool = False,
        reverse: bool = False,
        label: str = "",
        color: str = "",
        style: str = "",
        **attrs: Dict[Any, Any],
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

        self.node: Optional[Node] = node
        self.forward: bool = forward
        self.reverse: bool = reverse

        self._attrs: Dict[str, Any] = {}

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

    def __sub__(self, other: Union["Node", "Edge", List["Node"]]) -> Union["Node", "Edge", List["Node"]]:
        """Implement Self - Node or Edge and Self - [Nodes]"""
        return self.connect(other)

    def __rsub__(self, other: Union[List["Node"], List["Edge"]]) -> List["Edge"]:
        """Called for [Nodes] or [Edges] - Self because list don't have __sub__ operators."""
        return self.append(other)

    def __rshift__(self, other: Union["Node", "Edge", List["Node"]]) -> Union["Node", "Edge", List["Node"]]:
        """Implements Self >> Node or Edge and Self >> [Nodes]."""
        self.forward = True
        return self.connect(other)

    def __lshift__(self, other: Union["Node", "Edge", List["Node"]]) -> Union["Node", "Edge", List["Node"]]:
        """Implements Self << Node or Edge and Self << [Nodes]."""
        self.reverse = True
        return self.connect(other)

    def __rrshift__(self, other: Union[List["Node"], List["Edge"]]) -> List["Edge"]:
        """Called for [Nodes] or [Edges] >> Self because list of Edges don't have __rshift__ operators."""
        return self.append(other, forward=True)

    def __rlshift__(self, other: Union[List["Node"], List["Edge"]]) -> List["Edge"]:
        """Called for [Nodes] or [Edges] << Self because list of Edges don't have __lshift__ operators."""
        return self.append(other, reverse=True)

    def append(
        self, other: Union[List["Node"], List["Edge"]], forward: Optional[bool] = None, reverse: Optional[bool] = None
    ) -> List["Edge"]:
        result = []
        for o in other:
            if isinstance(o, Edge):
                o.forward = forward if forward else o.forward
                o.reverse = reverse if reverse else o.reverse
                self._attrs = o.attrs.copy()
                result.append(o)
            else:
                result.append(Edge(o, forward=bool(forward), reverse=bool(reverse), **self._attrs))
        return result

    def connect(self, other: Union["Node", "Edge", List["Node"]]) -> Union["Node", "Edge", List["Node"]]:
        if isinstance(other, list):
            if self.node is not None:
                for node in other:
                    self.node.connect(node, self)
            return other
        if isinstance(other, Edge):
            self._attrs = other._attrs.copy()
            return self
        if self.node is not None:
            return self.node.connect(other, self)
        self.node = other
        return self

    @property
    def attrs(self) -> Dict[str, Any]:
        if self.forward and self.reverse:
            direction = "both"
        elif self.forward:
            direction = "forward"
        elif self.reverse:
            direction = "back"
        else:
            direction = "none"
        return {**self._attrs, "dir": direction}


Group: Type[Cluster] = Cluster
