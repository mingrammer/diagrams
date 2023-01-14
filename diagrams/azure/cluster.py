from diagrams import Cluster
from diagrams.azure.compute import VM, VMWindows, VMLinux #, VMScaleSet # Depends on PR-404
from diagrams.azure.network import VirtualNetworks, Subnets, NetworkSecurityGroupsClassic

class Subscription(Cluster):
    # fmt: off
    _default_graph_attrs = {
        "shape": "box",
        "style": "dotted",
        "labeljust": "l",
        "pencolor": "#AEB6BE",
        "fontname": "Sans-Serif",
        "fontsize": "12",
    }
    # fmt: on

class Region(Cluster):
    # fmt: off
    _default_graph_attrs = {
        "shape": "box",
        "style": "dotted",
        "labeljust": "l",
        "pencolor": "#AEB6BE",
        "fontname": "Sans-Serif",
        "fontsize": "12",
    }
    # fmt: on

class AvailabilityZone(Cluster):
    # fmt: off
    _default_graph_attrs = {
        "shape": "box",
        "style": "dashed",
        "labeljust": "l",
        "pencolor": "#27a0ff",
        "fontname": "sans-serif",
        "fontsize": "12",
    }
    # fmt: on

class VirtualNetwork(Cluster):
    # fmt: off
    _default_graph_attrs = {
        "shape": "box",
        "style": "",
        "labeljust": "l",
        "pencolor": "#00D110",
        "fontname": "sans-serif",
        "fontsize": "12",
    }
    # fmt: on
    _icon = VirtualNetworks

class SubnetWithNSG(Cluster):
    # fmt: off
    _default_graph_attrs = {
        "shape": "box",
        "style": "",
        "labeljust": "l",
        "pencolor": "#329CFF",
        "fontname": "sans-serif",
        "fontsize": "12",
    }
    # fmt: on
    _icon = NetworkSecurityGroupsClassic

class Subnet(Cluster):
    # fmt: off
    _default_graph_attrs = {
        "shape": "box",
        "style": "",
        "labeljust": "l",
        "pencolor": "#00D110",
        "fontname": "sans-serif",
        "fontsize": "12",
    }
    # fmt: on
    _icon = Subnets

class SecurityGroup(Cluster):
    # fmt: off
    _default_graph_attrs = {
        "shape": "box",
        "style": "dashed",
        "labeljust": "l",
        "pencolor": "#FF361E",
        "fontname": "Sans-Serif",
        "fontsize": "12",
    }
    # fmt: on

class VMContents(Cluster):
    # fmt: off
    _default_graph_attrs = {
        "shape": "box",
        "style": "",
        "labeljust": "l",
        "pencolor": "#FFB432",
        "fontname": "Sans-Serif",
        "fontsize": "12",
    }
    # fmt: on
    _icon = VM

class VMLinuxContents(Cluster):
    # fmt: off
    _default_graph_attrs = {
        "shape": "box",
        "style": "",
        "labeljust": "l",
        "pencolor": "#FFB432",
        "fontname": "Sans-Serif",
        "fontsize": "12",
    }
    # fmt: on
    _icon = VMLinux

class VMWindowsContents(Cluster):
    # fmt: off
    _default_graph_attrs = {
        "shape": "box",
        "style": "",
        "labeljust": "l",
        "pencolor": "#FFB432",
        "fontname": "Sans-Serif",
        "fontsize": "12",
    }
    # fmt: on
    _icon = VMWindows

# Depends on PR-404
# class VMSS(Cluster):
#     # fmt: off
#     _default_graph_attrs = {
#         "shape": "box",
#         "style": "dashed",
#         "labeljust": "l",
#         "pencolor": "#FF7D1E",
#         "fontname": "Sans-Serif",
#         "fontsize": "12",
#     }
#     # fmt: on
#     _icon = VMScaleSet
