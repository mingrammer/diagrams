"""
Volcengine provides a set of services for Volcengine provider.
"""

from diagrams import Node


class _Volcengine(Node):
    _provider = "volcengine"
    _icon_dir = "resources/volcengine"

    fontcolor = "#ffffff"


class Volcengine(_Volcengine):
    _icon = "volcengine.png"
