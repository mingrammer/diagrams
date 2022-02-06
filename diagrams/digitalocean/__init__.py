"""
DigitalOcean provides a set of services for DigitalOcean provider.
"""

from diagrams import Node


class _DigitalOcean(Node):
    _provider = "digitalocean"
    _icon_dir = "resources/digitalocean"

    fontcolor = "#ffffff"
