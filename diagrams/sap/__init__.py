"""
SAP provides a set of services for SAP Business Technology Platform provider.
"""

from diagrams import Node


class _SAP(Node):
    _provider = "sap"
    _icon_dir = "resources/sap"

    fontcolor = "#ffffff"


class SAP(_SAP):
    _icon = "sap.png"
