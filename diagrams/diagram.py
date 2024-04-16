import os
from .node import Node
from .edge import Edge
from typing import Optional
from graphviz import Digraph
from .context import Context
from .utils import setdiagram


class Diagram(Context):
    __curvestyles = ("ortho", "curved")
    __outformats = ("png", "jpg", "svg", "pdf", "dot")

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
        outformats: list = ["png"],
        autolabel: bool = False,
        show: bool = True,
        strict: bool = False,
        graph_attr: Optional[dict] = None,
        node_attr: Optional[dict] = None,
        edge_attr: Optional[dict] = None,
    ):
        """Diagram represents a global diagrams context.

        :param name: Diagram name. It will be used for output filename if the
            filename isn't given.
        :param filename: The output filename, without the extension (.png).
            If not given, it will be generated from the name.
        :param direction: Data flow direction. Default is 'left to right'.
        :param curvestyle: Curve bending style. One of "ortho" or "curved".
        :param outformats: List of output file formats. Default is ['png'].
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
        
        if not name and not filename:
            filename = "diagrams_image"
        elif not filename:
            filename = "_".join(name.split()).lower()
        self.filename = filename
        super().__init__(name, filename=self.filename, strict=strict)

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

        for outformat in outformats:
            if not self._validate_outformat(outformat):
                raise ValueError(f'"{outformat}" is not a valid output format')
        self.outformats = outformats

        # Merge passed in attributes
        self.dot.graph_attr.update(graph_attr)
        self.dot.node_attr.update(node_attr)
        self.dot.edge_attr.update(edge_attr)

        self.show = show
        self.autolabel = autolabel

    def __str__(self) -> str:
        return str(self.dot)

    def __enter__(self):
        setdiagram(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.render()
        # Remove the graphviz file leaving only the image.
        os.remove(self.filename)
        setdiagram(None)

    def _repr_png_(self):
        return self.dot.pipe(format="png")

    def _validate_curvestyle(self, curvestyle: str) -> bool:
        return curvestyle.lower() in self.__curvestyles

    def _validate_outformat(self, outformat: str) -> bool:
        return outformat.lower() in self.__outformats

    def connect(self, node: "Node", node2: "Node", edge: "Edge") -> None:
        """Connect the two Nodes."""
        self.dot.edge(node.nodeid, node2.nodeid, **edge.attrs)

    def render(self) -> None:
        for outformat in self.outformats:
            self.dot.render(format=outformat, view=self.show, quiet=True)
