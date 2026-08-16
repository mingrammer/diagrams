"""
Programming provides a set of programming languages and frameworks.
"""

from diagrams import Node


class _Programming(Node):
    _provider = "programming"
    _icon_dir = "resources/programming"

    fontcolor = "#ffffff"


class Programming(_Programming):
    _icon = "programming.png"
