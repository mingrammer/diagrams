from diagrams import Cluster
from diagrams.onprem.compute import Server

class ServerContents(Cluster):
    # fmt: off
    _default_graph_attrs = {
        "shape": "box",
        "style": "rounded,dotted",
        "labeljust": "l",
        "pencolor": "#A0A0A0",
        "fontname": "Sans-Serif",
        "fontsize": "12",
    }
    # fmt: on
    _icon = Server
