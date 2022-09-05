"""
HashiCorp provides a set of services for HashiCorp provider.
"""

from diagrams import Node


class _HashiCorp(Node):
    _provider = "hashicorp"
    _icon_dir = "resources/hashicorp"

    fontcolor = "#ffffff"
