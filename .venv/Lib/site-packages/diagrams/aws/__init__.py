"""
AWS provides a set of services for Amazon Web Service provider.
"""

from diagrams import Node


class _AWS(Node):
    _provider = "aws"
    _icon_dir = "resources/aws"

    fontcolor = "#ffffff"


class AWS(_AWS):
    _icon = "aws.png"
