"""
OCI provides a set of services for Oracle Cloud Infrastructure provider.
"""

from diagrams import Node


class _OCI(Node):
    _provider = "oci"
    _icon_dir = "resources/oci"

    fontcolor = "#312D2A"


class OCI(_OCI):
    _icon = "oci.png"
