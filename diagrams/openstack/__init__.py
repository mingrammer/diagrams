"""
Openstack provides a set of general OpenStack services.
"""

from diagrams import Node


class _OpenStack(Node):
    _provider = "openstack"
    _icon_dir = "resources/openstack"

    fontcolor = "#ffffff"
