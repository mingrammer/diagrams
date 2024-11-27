"""
IBM provides a set of services for IBM Cloud provider.
"""

from diagrams import Node


class _IBM(Node):
    _provider = "ibm"
    _icon_dir = "resources/ibm"

    fontcolor = "#ffffff"


class IBM(_IBM):
    _icon = "ibm.png"
