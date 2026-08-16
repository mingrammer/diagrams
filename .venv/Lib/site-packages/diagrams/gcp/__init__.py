"""
GCP provides a set of services for Google Cloud Platform provider.
"""

from diagrams import Node


class _GCP(Node):
    _provider = "gcp"
    _icon_dir = "resources/gcp"

    fontcolor = "#2d3436"


class GCP(_GCP):
    _icon = "gcp.png"
