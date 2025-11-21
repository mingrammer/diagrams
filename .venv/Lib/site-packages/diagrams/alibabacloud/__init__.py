"""
AlibabaCloud provides a set of services for Alibaba Cloud provider.
"""

from diagrams import Node


class _AlibabaCloud(Node):
    _provider = "alibabacloud"
    _icon_dir = "resources/alibabacloud"

    fontcolor = "#ffffff"


class AlibabaCloud(_AlibabaCloud):
    _icon = "alibabacloud.png"
