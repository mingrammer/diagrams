"""
OnPrem provides a set of general on-premises services.
"""

from diagrams import Node


class _OnPrem(Node):
    _provider = "onprem"
    _icon_dir = "resources/onprem"

    fontcolor = "#ffffff"


class OnPrem(_OnPrem):
    _icon = "onprem.png"
