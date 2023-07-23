from graphviz import Digraph
from typing import Optional
from .context import Context
from .utils import setcluster, getcluster, getdiagram

class Cluster(Context):
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
    def __init__(
        self,
        label: str = "cluster",
        direction: str = "LR",
        graph_attr: Optional[dict] = None,
    ):
        """Cluster represents a cluster context.

        :param label: Cluster label.
        :param direction: Data flow direction. Default is 'left to right'.
        :param graph_attr: Provide graph_attr dot config attributes.
        """
        if graph_attr is None:
            graph_attr = {}
        self.label = label
        super().__init__("cluster_" + self.label)

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

        # Merge passed in attributes
        self.dot.graph_attr.update(graph_attr)

    def __enter__(self):
        setcluster(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._parent:
            self._parent.subgraph(self.dot)
        else:
            self._diagram.subgraph(self.dot)
        setcluster(self._parent)
        