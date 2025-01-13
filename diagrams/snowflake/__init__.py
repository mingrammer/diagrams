"""
Saas provides a set of general saas services.
"""

from diagrams import Node


class _Snowflake(Node):
    _provider = "snowflake"
    _icon_dir = "resources/snowflake"

    fontcolor = "#ffffff"
