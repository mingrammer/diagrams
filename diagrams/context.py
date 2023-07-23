from graphviz import Digraph
from abc import ABC, abstractmethod

class Context(ABC):
    __directions = ("TB", "BT", "LR", "RL")

    def __init__(self, name, **kwargs):
        self.name = name
        self.dot = Digraph(self.name, **kwargs)

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def _validate_direction(self, direction: str) -> bool:
        return direction.upper() in self.__directions

    def node(self, nodeid: str, label: str, **attrs) -> None:
        """Create a new node in the cluster."""
        self.dot.node(nodeid, label=label, **attrs)

    def subgraph(self, dot: Digraph) -> None:
        self.dot.subgraph(dot)