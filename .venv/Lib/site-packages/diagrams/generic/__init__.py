"""
Generic provides the possibility of load an image to be presented as a node.
"""

from diagrams import Node


class _Generic(Node):
    provider = "generic"
    _icon_dir = "resources/generic"

    fontcolor = "#ffffff"


class Generic(_Generic):
    _icon = "generic.png"
